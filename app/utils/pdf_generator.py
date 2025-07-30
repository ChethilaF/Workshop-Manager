import os
from flask import render_template
from xhtml2pdf import pisa

PDF_DIR = "app/static/pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

def generate_job_pdf(job, technician):
    filename = f"job_{job.id}_summary.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    
    html = render_template("job_summary_template.html", job=job, technician=technician)
    with open(filepath, "wb") as pdf_file:
        pisa.CreatePDF(html, dest=pdf_file)

def generate_weekly_summary_pdf(technician, week_start, week_end, shifts, jobs):
    filename = f"weekly_summary_{technician.id}_{week_start}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    html = render_template(
        "weekly_summary_template.html",
        technician=technician,
        week_start=week_start,
        week_end=week_end,
        shifts=shifts,
        jobs=jobs
    )

    with open(filepath, "wb") as pdf_file:
        pisa.CreatePDF(html, dest=pdf_file)

    return filename
