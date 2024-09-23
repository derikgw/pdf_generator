# pdf_generator.py
import json
import logging
from pdf_generator_service import download_pdf, fill_pdf_fields  # Import the service functions
import sys

# Set up logging to go to stdout, which Lambda captures
logging.basicConfig(
    level=logging.INFO,  # Capture INFO-level logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Ensure logs are written to stdout
)
logger = logging.getLogger()

def lambda_handler(event, context):
    try:
        # Get template name from query parameters
        template_name = event.get('queryStringParameters', {}).get('templateName')
        if not template_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'templateName parameter is required'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Parse the form data from the request body
        form_data = json.loads(event['body']).get('formData', {})
        if not form_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'formData is required'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Define S3 bucket and dynamic template path
        bucket_name = 'aws-sam-cli-managed-default-samclisourcebucket-kdvjqzoec6pg'
        pdf_template_s3_key = f'pdf_templates/{template_name}'

        # Paths in Lambda's tmp directory
        pdf_template_path = f'/tmp/{template_name}'
        output_pdf_name = template_name.replace('.pdf', '_output.pdf')
        output_pdf_path = f'/tmp/{output_pdf_name}'

        logger.info(
            f"About to download template from S3 bucket: {bucket_name}, key: {pdf_template_s3_key}, to {pdf_template_path}")

        # Download the template PDF from S3 using the service function
        download_pdf(f"s3://{bucket_name}", pdf_template_s3_key, pdf_template_path)

        logger.info(f"Download completed, file should be available at {pdf_template_path}")

        # Generate the filled-in PDF using the service function
        encoded_pdf = fill_pdf_fields(pdf_template_path, form_data, output_pdf_path)

        # Return the encoded PDF as part of the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'inline; filename="{output_pdf_name}"'
            },
            'body': encoded_pdf,
            'isBase64Encoded': True
        }

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
