import json
import base64
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
import boto3

s3 = boto3.client('s3')

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

        # Download the template PDF from S3
        s3.download_file(bucket_name, pdf_template_s3_key, pdf_template_path)

        # Open and modify the PDF
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

                    # Log field information
                    print(f"Field Name: {field_name}, Type: {field_type}, Current Value: {field.get('/V')}")

                    if field_name and field_name.strip('()') in form_data:
                        field_name = field_name.strip('()')  # Clean field name
                        field_value = form_data[field_name]

                        if field_type == NameObject("/Btn"):
                            # Handle checkbox fields
                            print(f"Setting checkbox {field_name} to: {field_value}")

                            # Try setting the value to `/Yes`, `/On`, or `/1`
                            checked_value = "/Yes"  # Try /Yes first; adjust if necessary

                            if isinstance(field_value, str) and field_value.lower() in ['yes', 'true', 'on']:
                                # Check the box
                                field.update({
                                    NameObject("/V"): NameObject(checked_value),  # Set the value
                                    NameObject("/AS"): NameObject(checked_value)  # Set the appearance state
                                })
                                print(f"Checkbox {field_name} set to {checked_value} (checked).")
                            else:
                                # Uncheck the box
                                field.update({
                                    NameObject("/V"): NameObject("/Off"),
                                    NameObject("/AS"): NameObject("/Off")
                                })
                                print(f"Checkbox {field_name} set to Off (unchecked).")

                            # Reset appearance to force the visual update
                            if "/AP" in field:
                                print(f"Resetting appearance stream for {field_name}")
                                del field[NameObject("/AP")]
                        else:
                            # For text fields, set the value
                            print(f"Setting text field {field_name} to: {field_value}")
                            field.update({
                                NameObject("/V"): TextStringObject(field_value)
                            })
                            if "/AP" in field:
                                del field[NameObject("/AP")]  # Force appearance stream regeneration

            pdf_writer.add_page(page)

        # Write the modified PDF to output file
        with open(output_pdf_path, 'wb') as f:
            pdf_writer.write(f)

        # Encode the modified PDF in base64 for the API response
        with open(output_pdf_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

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
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
