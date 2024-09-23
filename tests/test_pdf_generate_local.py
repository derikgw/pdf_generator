# test_pdf_generator.py
import os
from pdf_generator_service import download_pdf, fill_pdf_fields

def test_pdf_generator():
    # Test data
    #template_path = "s3://your-bucket-name/pdf_templates/sample_template.pdf"  # Use local path or S3 path
    template_dir = os.path.expanduser("~")
    template_path = f"{template_dir}/pdf_templates/template_form1.pdf"
    form_data = {
        "fname_input": "John",
        "lname_input": "Doe",
        "accept_terms": "Yes"
    }
    output_path = "/tmp/generated_output.pdf"

    # Download PDF (either from S3 or local)
    pdf_template_path = download_pdf(template_path)

    # Generate filled PDF
    encoded_pdf = fill_pdf_fields(pdf_template_path, form_data, output_path)

    # Save the output PDF for review
    with open("output_encoded.pdf", "wb") as f:
        f.write(encoded_pdf.encode('utf-8'))

    print("PDF generation test completed. Output saved.")

if __name__ == "__main__":
    test_pdf_generator()
