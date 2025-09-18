import os
from flask import render_template
from xhtml2pdf import pisa

# Make PDF_DIR absolute based on this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, '../static/pdfs')
os.makedirs(PDF_DIR, exist_ok=True)


def generate_weekly_summary_pdf(technician, week_start, week_end,
                                shifts, jobs):
    filename = f"weekly_summary_{technician.id}_{week_start}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    html = render_template(
        "weekly_summary_template.html",
        technician=technician,
        start_of_week=week_start,
        end_of_week=week_end,
        shift_logs=shifts,
        jobs=jobs
    )

    with open(filepath, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html, dest=pdf_file)
        if pisa_status.err:
            return None

    return filename


def get_pdfs_for_tech(tech_id):
    all_files = os.listdir(PDF_DIR)
    tech_files = [f for f in all_files if
                  f.startswith(f"weekly_summary_{tech_id}_")]
    return sorted(tech_files, reverse=True)
