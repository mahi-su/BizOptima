"""
BizOptima - Prediction Routes
Handles profit prediction, history, what-if analysis, and dashboard data
"""

import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import db, Prediction
from ml.model_training import predict_profit, get_model_metrics
from utils.ml_utils import analyze_risk, calculate_health_score, generate_suggestions, what_if_comparison

predictions_bp = Blueprint('predictions', __name__)


def validate_inputs(data):
    """Validate prediction input fields"""
    if not isinstance(data, dict):
        return "Request body must be valid JSON"
    required_fields = ['revenue', 'expenses', 'marketing_spend', 'employee_count', 'operational_cost']
    for field in required_fields:
        if field not in data or data[field] is None:
            return f"Missing field: {field}"
        try:
            val = float(data[field])
            if val < 0:
                return f"{field} cannot be negative"
            if field == 'employee_count' and val < 1:
                return "employee_count must be at least 1"
        except (ValueError, TypeError):
            return f"{field} must be a number"
    return None


@predictions_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Main prediction endpoint.
    Runs ML model + risk analysis + health score + smart suggestions.
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}

        # Validate inputs
        error = validate_inputs(data)
        if error:
            return jsonify({'error': error}), 400

        # Extract inputs
        revenue = float(data['revenue'])
        expenses = float(data['expenses'])
        marketing_spend = float(data['marketing_spend'])
        employee_count = int(float(data['employee_count']))
        operational_cost = float(data['operational_cost'])

        # --- ML Prediction ---
        predicted_profit = predict_profit(
            revenue, expenses, marketing_spend,
            employee_count, operational_cost
        )

        # --- Risk Analysis ---
        risk_level = analyze_risk(revenue, expenses, marketing_spend, operational_cost, predicted_profit)

        # --- Health Score ---
        health_score = calculate_health_score(
            revenue, expenses, marketing_spend,
            employee_count, operational_cost, predicted_profit
        )

        # --- Smart Suggestions ---
        suggestions = generate_suggestions(
            revenue, expenses, marketing_spend,
            employee_count, operational_cost,
            predicted_profit, health_score, risk_level
        )

        # --- Save to Database ---
        prediction = Prediction(
            user_id=user_id,
            revenue=revenue,
            expenses=expenses,
            marketing_spend=marketing_spend,
            employee_count=employee_count,
            operational_cost=operational_cost,
            predicted_profit=predicted_profit,
            risk_level=risk_level,
            health_score=health_score,
            suggestions=json.dumps(suggestions),
            report_name=(data.get('report_name') or f'Report #{user_id}')[:200]
        )
        db.session.add(prediction)
        db.session.commit()

        # --- Response ---
        return jsonify({
            'success': True,
            'prediction_id': prediction.id,
            'predicted_profit': round(predicted_profit, 2),
            'risk_level': risk_level,
            'health_score': round(health_score, 1),
            'suggestions': suggestions,
            'inputs': {
                'revenue': revenue,
                'expenses': expenses,
                'marketing_spend': marketing_spend,
                'employee_count': employee_count,
                'operational_cost': operational_cost
            },
            'metrics': {
                'profit_margin': round((predicted_profit / revenue * 100), 2) if revenue > 0 else 0,
                'expense_ratio': round(((expenses + operational_cost) / revenue * 100), 2) if revenue > 0 else 0,
                'marketing_roi': round((predicted_profit / marketing_spend), 2) if marketing_spend > 0 else 0
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/what-if', methods=['POST'])
@jwt_required()
def what_if():
    """
    What-If Analysis: Compare original vs modified business inputs
    """
    try:
        data = request.get_json(silent=True) or {}

        original = data.get('original')
        modified = data.get('modified')

        if not original or not modified:
            return jsonify({'error': 'Both original and modified inputs required'}), 400

        # Validate both
        for label, inputs in [('original', original), ('modified', modified)]:
            err = validate_inputs(inputs)
            if err:
                return jsonify({'error': f'{label}: {err}'}), 400

        # Original predictions
        o_profit = predict_profit(
            float(original['revenue']), float(original['expenses']),
            float(original['marketing_spend']), int(float(original['employee_count'])),
            float(original['operational_cost'])
        )
        o_risk = analyze_risk(float(original['revenue']), float(original['expenses']),
                               float(original['marketing_spend']), float(original['operational_cost']), o_profit)
        o_health = calculate_health_score(
            float(original['revenue']), float(original['expenses']),
            float(original['marketing_spend']), int(float(original['employee_count'])),
            float(original['operational_cost']), o_profit
        )

        # Modified predictions
        m_profit = predict_profit(
            float(modified['revenue']), float(modified['expenses']),
            float(modified['marketing_spend']), int(float(modified['employee_count'])),
            float(modified['operational_cost'])
        )
        m_risk = analyze_risk(float(modified['revenue']), float(modified['expenses']),
                               float(modified['marketing_spend']), float(modified['operational_cost']), m_profit)
        m_health = calculate_health_score(
            float(modified['revenue']), float(modified['expenses']),
            float(modified['marketing_spend']), int(float(modified['employee_count'])),
            float(modified['operational_cost']), m_profit
        )

        # Comparison
        comparison = what_if_comparison(
            original, modified, o_profit, m_profit, o_health, m_health, o_risk, m_risk
        )

        return jsonify({
            'original': {
                'predicted_profit': round(o_profit, 2),
                'risk_level': o_risk,
                'health_score': round(o_health, 1)
            },
            'modified': {
                'predicted_profit': round(m_profit, 2),
                'risk_level': m_risk,
                'health_score': round(m_health, 1)
            },
            'comparison': comparison
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """Get prediction history for current user"""
    try:
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        predictions = Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'predictions': [p.to_dict() for p in predictions.items],
            'total': predictions.total,
            'pages': predictions.pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_data():
    """Get dashboard analytics data for charts"""
    try:
        user_id = int(get_jwt_identity())
        predictions = Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.asc()).all()

        if not predictions:
            return jsonify({
                'message': 'No predictions yet',
                'has_data': False
            }), 200

        # Prepare chart data
        labels = [p.created_at.strftime('%b %d') for p in predictions]
        profits = [round(p.predicted_profit, 2) for p in predictions]
        revenues = [p.revenue for p in predictions]
        expenses = [p.expenses for p in predictions]
        health_scores = [p.health_score for p in predictions]

        # Risk distribution
        risk_counts = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
        for p in predictions:
            risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + 1

        # Summary stats
        avg_profit = sum(profits) / len(profits)
        avg_health = sum(health_scores) / len(health_scores)
        best_profit = max(profits)
        total_revenue = sum(revenues)

        # Feature importances from model
        metrics = get_model_metrics()
        feature_importances = metrics.get('feature_importances', {})

        return jsonify({
            'has_data': True,
            'labels': labels,
            'profits': profits,
            'revenues': revenues,
            'expenses': expenses,
            'health_scores': health_scores,
            'risk_distribution': risk_counts,
            'feature_importances': feature_importances,
            'summary': {
                'total_predictions': len(predictions),
                'avg_profit': round(avg_profit, 2),
                'avg_health_score': round(avg_health, 1),
                'best_profit': round(best_profit, 2),
                'total_revenue': round(total_revenue, 2),
                'model_accuracy': metrics.get('r2_score', 0)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/model-info', methods=['GET'])
@jwt_required()
def model_info():
    """Get ML model performance metrics"""
    try:
        metrics = get_model_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/<int:prediction_id>', methods=['GET'])
@jwt_required()
def get_prediction(prediction_id):
    """Get single prediction by ID"""
    try:
        user_id = int(get_jwt_identity())
        prediction = Prediction.query.filter_by(id=prediction_id, user_id=user_id).first()
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        return jsonify(prediction.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/<int:prediction_id>', methods=['DELETE'])
@jwt_required()
def delete_prediction(prediction_id):
    """Delete a prediction"""
    try:
        user_id = int(get_jwt_identity())
        prediction = Prediction.query.filter_by(id=prediction_id, user_id=user_id).first()
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        db.session.delete(prediction)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
