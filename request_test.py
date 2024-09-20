import requests
import os
import base64

# API Gateway endpoint (replace with your actual endpoint)
api_url = "https://kd4mqyytdc.execute-api.us-east-1.amazonaws.com/Prod/pdf-function-test"

# API Key (retrieve from environment variable)
api_key = os.getenv("PDF_FUNCTION_API_KEY")

# Check if the API key is found
if not api_key:
    print("API key not found. Please set the environment variable 'PDF_FUNCTION_API_KEY'.")
    exit(1)

# Data to be sent in the POST request (updated to only send one field)
data = {
    "formData": {
        "fname_input": "John Doe"  # Updated to match the only field in the template
    }
}

try:
    # Make the POST request to the API
    response = requests.post(
        api_url,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json"
        },
        json=data
    )

    # Check if the request was successful
    if response.status_code == 200:
        print(f"Response Headers: {response.headers}")
        print(f"Response Content-Type: {response.headers.get('Content-Type')}")

        # Since the response is base64-encoded, we need to decode it
        if response.headers.get('Content-Type') == 'application/pdf':
            pdf_base64 = response.content.decode('utf-8')
            pdf_data = base64.b64decode(pdf_base64)

            # Save the raw PDF content to a file
            output_pdf_path = "output.pdf"
            with open(output_pdf_path, "wb") as f:
                f.write(pdf_data)

            print(f"PDF successfully saved to {output_pdf_path}")
        else:
            print("Error: The response is not a PDF.")
            print(f"Content-Type received: {response.headers.get('Content-Type')}")
    else:
        print(f"Failed to retrieve PDF. Status code: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred during the request: {e}")
