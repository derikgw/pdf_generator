# pdf_generator_service.py
import boto3
import logging
import base64
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
import sys

# Set up logging to go to stdout, which Lambda captures
logging.basicConfig(
    level=logging.INFO,  # Capture INFO-level logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Ensure logs are written to stdout
)
logger = logging.getLogger()

# Initialize the S3 client
s3 = boto3.client('s3')


def download_pdf(bucket_or_path, s3_key=None, local_path=None):
    """
    Download a PDF template from S3 or use the local path if provided.

    If running in Lambda (USE_S3=true), download the file from S3. Otherwise, use the local file path.
    """
    use_s3 = os.getenv('USE_S3', 'false').lower() == 'true'

    if use_s3:
        # S3 download logic
        bucket_name = bucket_or_path if not bucket_or_path.startswith("s3://") else bucket_or_path.split('/')[2]
        s3_key = '/'.join(bucket_or_path.split('/')[3:]) if bucket_or_path.startswith("s3://") else s3_key

        if not local_path:
            local_path = f'/tmp/{os.path.basename(s3_key)}'

        try:
            logger.info(f"Downloading PDF from S3 bucket: {bucket_name}, key: {s3_key}, to {local_path}")
            s3.download_file(bucket_name, s3_key, local_path)
            logger.info(f"Downloaded PDF to local path: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading PDF from S3: {str(e)}", exc_info=True)
            raise e
    else:
        # Use local file system path
        logger.info(f"Using local PDF path: {bucket_or_path}")
        return bucket_or_path


def fill_pdf_fields(pdf_template_path, form_data, output_pdf_path):
    """
    Fill in the form fields of the PDF based on the provided form data.

    :param pdf_template_path: The local file path of the template PDF
    :param form_data: The data to populate the form fields with
    :param output_pdf_path: The local file path where the filled-in PDF will be saved
    :return: Base64-encoded string of the modified PDF
    """
    logger.info(f"Opening PDF template: {pdf_template_path}")

    pdf_reader = PdfReader(pdf_template_path)
    pdf_writer = PdfWriter()

    # Iterate over each page and its annotations
    for page in pdf_reader.pages:
        if '/Annots' in page:
            for annotation in page['/Annots']:
                field = annotation.get_object()
                field_name = field.get('/T')
                field_type = field.get('/FT')
                field_value = form_data.get(field_name, None)

                logger.info(f"Field Name: {field_name}, Type: {field_type}, Current Value: {field.get('/V')}")

                if field_name and field_name.strip('()') in form_data:
                    field_name = field_name.strip('()')  # Clean field name
                    field_value = form_data[field_name]

                    if field_type == NameObject("/Btn"):
                        # Handle checkbox fields
                        logger.info(f"Setting checkbox {field_name} to: {field_value}")
                        checked_value = "/Yes"  # Try /Yes first; adjust if necessary

                        if isinstance(field_value, str) and field_value.lower() in ['yes', 'true', 'on']:
                            # Check the box
                            field.update({
                                NameObject("/V"): NameObject(checked_value),
                                NameObject("/AS"): NameObject(checked_value)
                            })
                            logger.info(f"Checkbox {field_name} set to {checked_value} (checked).")
                        else:
                            # Uncheck the box
                            field.update({
                                NameObject("/V"): NameObject("/Off"),
                                NameObject("/AS"): NameObject("/Off")
                            })
                            logger.info(f"Checkbox {field_name} set to Off (unchecked).")

                        if "/AP" in field:
                            logger.info(f"Resetting appearance stream for {field_name}")
                            del field[NameObject("/AP")]
                    else:
                        # For text fields, set the value
                        logger.info(f"Setting text field {field_name} to: {field_value}")
                        field.update({
                            NameObject("/V"): TextStringObject(field_value)
                        })
                        if "/AP" in field:
                            del field[NameObject("/AP")]

        pdf_writer.add_page(page)

    # Write the modified PDF to output file
    with open(output_pdf_path, 'wb') as f:
        pdf_writer.write(f)

    logger.info(f"PDF modified and written to: {output_pdf_path}")

    # Encode the modified PDF in base64 for the API response
    with open(output_pdf_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

    return encoded_pdf
