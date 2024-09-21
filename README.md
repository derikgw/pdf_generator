# PDF Generator with AWS Lambda and PyPDF

This project is an AWS Lambda function that dynamically populates a PDF form using form data provided via an API request. The PDF template is stored in an S3 bucket, and the filled PDF is returned as a base64-encoded string in the response.

## Features

- **Dynamic PDF Form Filling**: Populate PDF text fields and checkboxes with data provided in the API request.
- **S3 Integration**: Retrieve PDF templates from an S3 bucket.
- **Base64-encoded PDF Response**: Return the generated PDF in a base64-encoded format, making it easy to download or display in web applications.
- **Checkbox Handling**: Properly check/uncheck checkboxes in the PDF.
- **Text Field Population**: Fill out text fields using form data.
- **Customizable Output**: The modified PDF is returned with the original filename, appended with `_output.pdf`.

## How it Works

1. The API receives a POST request with the PDF template name and form data.
2. The Lambda function retrieves the specified PDF template from the S3 bucket.
3. The function modifies the form fields (text fields and checkboxes) in the PDF based on the provided data.
4. The updated PDF is returned as a base64-encoded string in the response.

## Technologies Used

- **AWS Lambda**: Serverless function to process the PDF generation.
- **AWS S3**: Stores the PDF templates.
- **PyPDF**: Python library used to read and modify PDF forms.
- **Boto3**: AWS SDK for Python, used to interact with S3.
- **Python 3.12**: The runtime environment for the Lambda function.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Overview](#api-overview)
3. [S3 Bucket Structure](#s3-bucket-structure)
4. [Lambda Code](#lambda-code)
5. [Deploying the Lambda Function](#deploying-the-lambda-function)
6. [Testing the API](#testing-the-api)
7. [Error Handling](#error-handling)
8. [Future Improvements](#future-improvements)

---

## Prerequisites

Before you begin, ensure you have the following:

- **AWS Account**: You need an AWS account to create the Lambda function and S3 bucket.
- **AWS CLI**: Installed and configured on your machine. [AWS CLI Installation](https://aws.amazon.com/cli/)
- **SAM CLI (Serverless Application Model)**: For deploying the Lambda function. [Install SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- **Python 3.12 or higher**: The Lambda function uses Python 3.12.

## API Overview

### Request Format

The API expects a POST request with the following structure:

- **Query Parameters**:
  - `templateName`: The name of the PDF template stored in the S3 bucket.
  
- **Body**:
  - `formData`: A JSON object containing the form fields and their corresponding values.

#### Example Request

```http
POST /pdf-generator?templateName=sample_template.pdf HTTP/1.1
Host: your-api-gateway-url
Content-Type: application/json

{
    "formData": {
        "fname_input": "John",
        "middle_init_input": "A",
        "lname_input": "Doe",
        "q_human_boolean_input": "Yes"
    }
}
```

### Response

- **Status Code**: `200 OK`
- **Response Body**: Base64-encoded string of the generated PDF file.
- **Headers**:
  - `Content-Type`: `application/pdf`
  - `Content-Disposition`: Inline filename with the original template name appended with `_output.pdf`.

#### Example Response

```json
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/pdf",
        "Content-Disposition": "inline; filename=\"sample_template_output.pdf\""
    },
    "body": "<base64-encoded-pdf>",
    "isBase64Encoded": true
}
```

## S3 Bucket Structure

Your S3 bucket should contain the PDF templates that are used to populate data. The Lambda function fetches these templates using the template name provided in the query parameter.

### Example Structure:

```plaintext
S3 Bucket: aws-sam-cli-managed-default-samclisourcebucket-kdvjqzoec6pg
└── pdf_templates/
    ├── sample_template.pdf
    └── another_template.pdf
```

## Lambda Code

Here’s the core code of the Lambda function:

```python
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
                    if field_name and field_name.strip('()') in form_data:
                        field_name = field_name.strip('()')  # Clean field name
                        field_value = form_data[field_name]

                        if field_type == NameObject("/Btn"):
                            # Handle checkbox fields
                            checked_value = "/Yes"
                            if isinstance(field_value, str) and field_value.lower() in ['yes', 'true', 'on']:
                                field.update({NameObject("/V"): NameObject(checked_value), NameObject("/AS"): NameObject(checked_value)})
                            else:
                                field.update({NameObject("/V"): NameObject("/Off"), NameObject("/AS"): NameObject("/Off")})
                            if "/AP" in field:
                                del field[NameObject("/AP")]
                        else:
                            field.update({NameObject("/V"): TextStringObject(field_value)})
                            if "/AP" in field:
                                del field[NameObject("/AP")]

            pdf_writer.add_page(page)

        # Write the modified PDF to output file
        with open(output_pdf_path, 'wb') as f:
            pdf_writer.write(f)

        # Encode the modified PDF in base64 for the API response
        with open(output_pdf_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/pdf', 'Content-Disposition': f'inline; filename="{output_pdf_name}"'},
            'body': encoded_pdf,
            'isBase64Encoded': True
        }

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'message': 'Internal server error', 'error': str(e)})}
```

## Deploying the Lambda Function

You can deploy this Lambda function using AWS SAM. Here's a general overview of the deployment process:

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Build the Lambda Function**:
   ```bash
   sam build
   ```

3. **Deploy the Lambda Function**:
   ```bash
   sam deploy --guided
   ```

   During deployment, SAM will ask you to provide various parameters, including the stack name and the S3 bucket name.

4. **Test the API** using the API Gateway URL provided after deployment.

## Testing the API

You can test the API using tools like **Postman** or **cURL**. Example:

```bash
curl -X POST https://your-api-url/pdf-generator?templateName=sample_template.pdf \
    -H "Content-Type: application/json" \
    -d '{"formData": {"fname_input": "John", "middle_init_input": "A

", "lname_input": "Doe", "q_human_boolean_input": "Yes"}}'
```

## Error Handling

The function returns the following error codes:

- **400 Bad Request**: When the `templateName` query parameter or `formData` body is missing.
- **500 Internal Server Error**: When something goes wrong during PDF processing.

## Future Improvements

- **Add Support for Dropdowns**: The current implementation only supports checkboxes and text fields. Dropdown fields can be added in future iterations.
- **Advanced PDF Layouts**: Handling multi-page PDFs or dynamic field positioning can enhance the functionality.
- **Error Logging**: Integrate detailed logging using AWS CloudWatch for easier debugging.
