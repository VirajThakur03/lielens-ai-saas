from pathlib import Path

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from apps.analysis.models import AnalysisResult, TextSubmission


def build_pdf_report(submission: TextSubmission, result: AnalysisResult) -> str:
    reports_dir = Path(settings.MEDIA_ROOT) / "reports" / str(submission.user_id)
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"submission_{submission.id}.pdf"

    page = canvas.Canvas(str(pdf_path), pagesize=A4)
    page.setTitle("LieLens Analysis Report")
    page.setFont("Helvetica-Bold", 20)
    page.drawString(2 * cm, 27 * cm, "LieLens")
    page.setFont("Helvetica", 12)
    page.drawString(2 * cm, 26.2 * cm, "AI Text Risk & Credibility Report")

    page.setFont("Helvetica-Bold", 12)
    page.drawString(2 * cm, 24.8 * cm, "Score Breakdown")
    page.setFont("Helvetica", 11)
    page.drawString(2 * cm, 24.1 * cm, f"Final Risk Score: {result.final_risk_score:.2f}")
    page.drawString(2 * cm, 23.5 * cm, f"Credibility Score: {result.credibility_score:.2f}")
    page.drawString(2 * cm, 22.9 * cm, f"Confidence Score: {result.confidence_score:.2f}")
    page.drawString(2 * cm, 22.3 * cm, f"Emotional Intensity: {result.emotional_intensity:.2f}")

    page.setFont("Helvetica-Bold", 12)
    page.drawString(2 * cm, 21.2 * cm, "AI Summary")
    page.setFont("Helvetica", 11)
    page.drawString(2 * cm, 20.5 * cm, result.ai_summary[:1100])

    page.setFont("Helvetica-Bold", 12)
    page.drawString(2 * cm, 19.0 * cm, "Recommendations")
    page.setFont("Helvetica", 11)
    y_pos = 18.3
    for item in result.recommendations[:6]:
        page.drawString(2 * cm, y_pos * cm, f"- {item[:100]}")
        y_pos -= 0.6

    page.showPage()
    page.save()
    return str(pdf_path.relative_to(settings.MEDIA_ROOT))
