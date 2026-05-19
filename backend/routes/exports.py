"""
BizOptima - Export Routes
PDF and CSV exports for prediction reports.
"""

import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import db, Prediction, User

exports_bp = Blueprint("exports", __name__)


@exports_bp.route("/csv", methods=["GET"])
@jwt_required()
def export_csv():
    """Export all predictions for the current user as CSV."""
    try:
        user_id = int(get_jwt_identity())
        predictions = Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.desc()).all()

        if not predictions:
            return jsonify({"error": "No predictions to export"}), 404

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID",
            "Date",
            "Revenue",
            "Expenses",
            "Marketing Spend",
            "Employee Count",
            "Operational Cost",
            "Predicted Profit",
            "Risk Level",
            "Health Score",
        ])

        for prediction in predictions:
            writer.writerow([
                prediction.id,
                prediction.created_at.strftime("%Y-%m-%d %H:%M"),
                prediction.revenue,
                prediction.expenses,
                prediction.marketing_spend,
                prediction.employee_count,
                prediction.operational_cost,
                round(prediction.predicted_profit, 2),
                prediction.risk_level,
                prediction.health_score,
            ])

        output.seek(0)
        csv_bytes = BytesIO(output.getvalue().encode("utf-8"))
        csv_bytes.seek(0)
        filename = f"bizoptima_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )

    except Exception:
        return jsonify({"error": "CSV export failed"}), 500


@exports_bp.route("/pdf/<int:prediction_id>", methods=["GET"])
@jwt_required()
def export_pdf(prediction_id):
    """Export a single prediction for the current user as a PDF report."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER

        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        prediction = Prediction.query.filter_by(id=prediction_id, user_id=user_id).first()

        if not prediction:
            return jsonify({"error": "Prediction not found"}), 404

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        elements = []
        navy = colors.HexColor("#102033")
        blue = colors.HexColor("#2563eb")
        teal = colors.HexColor("#0f766e")
        border = colors.HexColor("#d8e0ea")
        soft = colors.HexColor("#f5f7fb")

        title_style = ParagraphStyle(
            "BizTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=navy,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        sub_style = ParagraphStyle(
            "BizSub",
            parent=styles["BodyText"],
            fontSize=10,
            textColor=colors.HexColor("#667085"),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        section_style = ParagraphStyle(
            "BizSection",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=navy,
            spaceBefore=14,
            spaceAfter=7,
            fontName="Helvetica-Bold",
        )
        body_style = ParagraphStyle(
            "BizBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475467"),
        )

        elements.append(Paragraph("BizOptima", title_style))
        elements.append(Paragraph("AI Business Profit Prediction Report", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=teal))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Report Details", section_style))
        report_data = [
            ["Business Name", (user.business_name or user.username) if user else "BizOptima User"],
            ["Generated On", datetime.now().strftime("%d %B %Y, %I:%M %p")],
            ["Prediction ID", f"#{prediction.id}"],
            ["Report", prediction.report_name or "Business Analysis"],
        ]
        elements.append(build_table(report_data, [2.4 * inch, 4.6 * inch], border, soft, navy, colors.white, Table, TableStyle))

        elements.append(Paragraph("Business Input Parameters", section_style))
        input_data = [
            ["Parameter", "Value"],
            ["Revenue", f"${prediction.revenue:,.2f}"],
            ["Expenses", f"${prediction.expenses:,.2f}"],
            ["Marketing Spend", f"${prediction.marketing_spend:,.2f}"],
            ["Employee Count", str(prediction.employee_count)],
            ["Operational Cost", f"${prediction.operational_cost:,.2f}"],
        ]
        input_table = Table(input_data, colWidths=[3.5 * inch, 3.5 * inch])
        input_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, soft]),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ]))
        elements.append(input_table)

        elements.append(Paragraph("Prediction Results", section_style))
        result_data = [
            ["Metric", "Value", "Status"],
            [
                "Predicted Profit",
                f"${prediction.predicted_profit:,.2f}",
                "Positive" if prediction.predicted_profit > 0 else "Negative",
            ],
            [
                "Business Health Score",
                f"{prediction.health_score:.1f} / 100",
                "Good" if prediction.health_score >= 60 else "Fair" if prediction.health_score >= 40 else "Poor",
            ],
            [
                "Risk Level",
                prediction.risk_level,
                "Safe" if prediction.risk_level == "Low Risk" else "Caution" if prediction.risk_level == "Medium Risk" else "Alert",
            ],
        ]
        result_table = Table(result_data, colWidths=[2.4 * inch, 2.3 * inch, 2.3 * inch])
        result_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), teal),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, soft]),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(result_table)

        suggestions = json.loads(prediction.suggestions) if prediction.suggestions else []
        if suggestions:
            elements.append(Paragraph("Recommendations", section_style))
            for index, suggestion in enumerate(suggestions[:5], 1):
                title = escape(suggestion.get("title", "Recommendation"))
                message = escape(suggestion.get("message", ""))
                elements.append(Paragraph(f"{index}. <b>{title}</b>", body_style))
                elements.append(Paragraph(message, body_style))
                elements.append(Spacer(1, 5))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=border))
        elements.append(Paragraph(
            "Generated by BizOptima | Confidential Business Report",
            ParagraphStyle(
                "Footer",
                parent=styles["BodyText"],
                fontSize=8,
                textColor=colors.HexColor("#667085"),
                alignment=TA_CENTER,
                spaceBefore=7,
            ),
        ))

        doc.build(elements)
        buffer.seek(0)
        filename = f"bizoptima_report_{prediction_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except ImportError:
        return jsonify({"error": "ReportLab is not installed. Run pip install reportlab."}), 500
    except Exception:
        return jsonify({"error": "PDF export failed"}), 500


def build_table(data, col_widths, border, soft, navy, white, table_cls, style_cls):
    table = table_cls(data, colWidths=col_widths)
    table.setStyle(style_cls([
        ("BACKGROUND", (0, 0), (0, -1), soft),
        ("TEXTCOLOR", (0, 0), (0, -1), navy),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, border),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, soft]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    return table
