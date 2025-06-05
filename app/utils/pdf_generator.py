from xhtml2pdf import pisa
from flask import render_template
import os

def generate_job_pdf(job, technician):
    from app import create_app
    app = create_app()
    with app.app_context():
        html = render_template("job_pdf_template.html", job=job, technician=technician)

        output_path = os.path.join("app", "static", "pdfs", f"job_{job.id}_summary.pdf")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w+b") as result_file:
            pisa.CreatePDF(src=html, dest=result_file)
