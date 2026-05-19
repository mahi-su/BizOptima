"""
BizOptima - ML Utilities
Risk analysis, health scoring, recommendations, and what-if summaries.
"""


def analyze_risk(revenue, expenses, marketing_spend, operational_cost, predicted_profit):
    """Return Low Risk, Medium Risk, or High Risk based on financial ratios."""
    profit_margin = (predicted_profit / revenue * 100) if revenue > 0 else 0
    total_expenses = expenses + operational_cost
    expense_ratio = (total_expenses / revenue * 100) if revenue > 0 else 100
    marketing_roi = (predicted_profit / marketing_spend) if marketing_spend > 0 else 0

    risk_score = 0
    if profit_margin < 5:
        risk_score += 3
    elif profit_margin < 15:
        risk_score += 2

    if expense_ratio > 85:
        risk_score += 3
    elif expense_ratio > 70:
        risk_score += 2

    if marketing_roi < 1:
        risk_score += 2
    elif marketing_roi < 2:
        risk_score += 1

    if risk_score <= 2:
        return "Low Risk"
    if risk_score <= 4:
        return "Medium Risk"
    return "High Risk"


def calculate_health_score(revenue, expenses, marketing_spend, employee_count,
                           operational_cost, predicted_profit):
    """Generate a 0-100 business health score from weighted financial metrics."""
    score = 0
    total_expenses = expenses + operational_cost

    profit_margin = (predicted_profit / revenue * 100) if revenue > 0 else 0
    if profit_margin >= 25:
        score += 30
    elif profit_margin >= 15:
        score += 22
    elif profit_margin >= 8:
        score += 15
    elif profit_margin >= 0:
        score += 8

    expense_ratio = (total_expenses / revenue * 100) if revenue > 0 else 100
    if expense_ratio <= 50:
        score += 25
    elif expense_ratio <= 65:
        score += 18
    elif expense_ratio <= 75:
        score += 12
    elif expense_ratio <= 85:
        score += 6

    if revenue >= 1_000_000:
        score += 20
    elif revenue >= 500_000:
        score += 16
    elif revenue >= 200_000:
        score += 12
    elif revenue >= 50_000:
        score += 8
    else:
        score += 4

    marketing_ratio = (marketing_spend / revenue * 100) if revenue > 0 else 0
    marketing_roi = predicted_profit / marketing_spend if marketing_spend > 0 else 0
    if marketing_roi >= 3 and marketing_ratio <= 15:
        score += 15
    elif marketing_roi >= 2:
        score += 10
    elif marketing_roi >= 1:
        score += 6
    else:
        score += 2

    revenue_per_employee = revenue / employee_count if employee_count > 0 else 0
    if revenue_per_employee >= 200_000:
        score += 10
    elif revenue_per_employee >= 100_000:
        score += 7
    elif revenue_per_employee >= 50_000:
        score += 4
    else:
        score += 1

    return min(round(score, 1), 100)


def generate_suggestions(revenue, expenses, marketing_spend, employee_count,
                         operational_cost, predicted_profit, health_score, risk_level):
    """Generate business recommendations from prediction results."""
    suggestions = []
    total_expenses = expenses + operational_cost
    expense_ratio = (total_expenses / revenue * 100) if revenue > 0 else 100
    profit_margin = (predicted_profit / revenue * 100) if revenue > 0 else 0
    marketing_roi = predicted_profit / marketing_spend if marketing_spend > 0 else 0
    revenue_per_employee = revenue / employee_count if employee_count > 0 else 0

    if expense_ratio > 75:
        suggestions.append({
            "type": "warning",
            "icon": "bi-exclamation-triangle",
            "title": "High Expense Ratio Detected",
            "message": f"Your total expenses are {expense_ratio:.1f}% of revenue. Target below 70% for sustainable growth by auditing operational and overhead costs.",
        })

    if profit_margin < 10:
        suggestions.append({
            "type": "danger",
            "icon": "bi-graph-down-arrow",
            "title": "Low Profit Margin Alert",
            "message": f"Profit margin of {profit_margin:.1f}% is below the healthy 10-15% range. Review pricing, supplier costs, and variable expenses.",
        })
    elif profit_margin > 20:
        suggestions.append({
            "type": "success",
            "icon": "bi-rocket-takeoff",
            "title": "Excellent Profit Margin",
            "message": f"Your {profit_margin:.1f}% profit margin is strong. Consider reinvesting in growth, marketing, or product development.",
        })

    if marketing_roi < 1.5:
        suggestions.append({
            "type": "warning",
            "icon": "bi-megaphone",
            "title": "Improve Marketing ROI",
            "message": f"Marketing ROI of {marketing_roi:.2f}x is low. Focus budget on channels with clearer conversion data and better retention.",
        })
    elif marketing_roi > 4:
        suggestions.append({
            "type": "success",
            "icon": "bi-bullseye",
            "title": "Great Marketing Performance",
            "message": f"Marketing ROI of {marketing_roi:.2f}x is excellent. Consider scaling the highest-performing campaigns carefully.",
        })

    if revenue_per_employee < 80_000:
        suggestions.append({
            "type": "info",
            "icon": "bi-people",
            "title": "Boost Employee Productivity",
            "message": f"Revenue per employee is ${revenue_per_employee:,.0f}. Training, automation, and process optimization may improve output per person.",
        })

    op_ratio = (operational_cost / revenue * 100) if revenue > 0 else 0
    if op_ratio > 30:
        suggestions.append({
            "type": "warning",
            "icon": "bi-building-gear",
            "title": "Reduce Operational Costs",
            "message": f"Operational costs are {op_ratio:.1f}% of revenue. Review vendors, workflow bottlenecks, and recurring overhead.",
        })

    if health_score < 40:
        suggestions.append({
            "type": "danger",
            "icon": "bi-exclamation-octagon",
            "title": "Business Needs Immediate Attention",
            "message": "A health score below 40 indicates financial stress. Review cost centers, cash reserves, and near-term obligations.",
        })
    elif health_score > 75:
        suggestions.append({
            "type": "success",
            "icon": "bi-award",
            "title": "Business is Performing Well",
            "message": f"Health score of {health_score} shows strong fundamentals. Maintain discipline while exploring new growth opportunities.",
        })

    if risk_level == "High Risk":
        suggestions.append({
            "type": "danger",
            "icon": "bi-shield-exclamation",
            "title": "High Risk: Immediate Action Required",
            "message": "High-risk indicators detected. Build a 3-6 month expense reserve and reduce non-essential spending quickly.",
        })
    elif risk_level == "Low Risk":
        suggestions.append({
            "type": "success",
            "icon": "bi-shield-check",
            "title": "Low Risk: Stable Financial Position",
            "message": "Your business shows low risk. This is a good time to review strategic investments and expansion plans.",
        })

    return suggestions


def what_if_comparison(original_inputs, modified_inputs, original_profit, modified_profit,
                       original_health, modified_health, original_risk, modified_risk):
    """Generate a concise what-if comparison summary."""
    profit_change = modified_profit - original_profit
    profit_change_pct = (profit_change / abs(original_profit) * 100) if original_profit != 0 else 0
    health_change = modified_health - original_health
    direction = "increased" if profit_change > 0 else "decreased" if profit_change < 0 else "stayed flat"

    return {
        "profit_change": round(profit_change, 2),
        "profit_change_pct": round(profit_change_pct, 2),
        "health_change": round(health_change, 1),
        "risk_changed": original_risk != modified_risk,
        "improved": profit_change > 0,
        "summary": f"Profit {direction} by {abs(profit_change_pct):.1f}%",
    }
