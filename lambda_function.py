import json
import base64
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
import boto3

s3 = boto3.client('s3')


def lambda_handler(event, context):
    try:
        form_data = json.loads(event['body']).get('formData', {})

        # Define S3 bucket and template path
        bucket_name = 'aws-sam-cli-managed-default-samclisourcebucket-kdvjqzoec6pg'
        pdf_template_s3_key = 'pdf-function-test/template.pdf'

        # Paths in Lambda's tmp directory
        pdf_template_path = '/tmp/template.pdf'
        output_pdf_path = '/tmp/output.pdf'

        # Download the template PDF from S3
        s3.download_file(bucket_name, pdf_template_s3_key, pdf_template_path)

        # Open and modify the PDF
        pdf_reader = PdfReader(pdf_template_path)
        pdf_writer = PdfWriter()

        for page in pdf_reader.pages:
            if '/Annots' in page:
                for annotation in page['/Annots']:
                    field = annotation.get_object()
                    field_name = field.get('/T')
                    if field_name:
                        field_name = field_name.strip('()')
                        if field_name in form_data:
                            field.update({
                                NameObject("/V"): TextStringObject(form_data[field_name])
                            })
            pdf_writer.add_page(page)

        # Write modified PDF to output file
        with open(output_pdf_path, 'wb') as f:
            pdf_writer.write(f)

        # Encode PDF in base64 for the API response
        with open(output_pdf_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        # Return the encoded PDF
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/pdf',
                'Content-Disposition': 'inline; filename="output.pdf"'
            },
            'body': encoded_pdf,
            'isBase64Encoded': True
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
