from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors  # Import the colors module
from pdfrw import PdfWriter

# Path to the output PDF
template_path = 'data/editable_template.pdf'

def create_editable_pdf(template_path):
    # Create a blank PDF with a form field
    c = canvas.Canvas(template_path, pagesize=letter)

    # Add a form field (text field)
    form = c.acroForm

    # Create text fields with different properties
    form.textfield(name='Field1', tooltip='Fill in Field 1',
                   x=100, y=750, width=300, height=20,
                   borderStyle='underlined', textColor=colors.black,  # Using colors.black instead of 'black'
                   forceBorder=True)

    form.textfield(name='Field2', tooltip='Fill in Field 2',
                   x=100, y=700, width=300, height=20,
                   borderStyle='underlined', textColor=colors.black,  # Corrected
                   forceBorder=True)

    form.textfield(name='Field3', tooltip='Fill in Field 3',
                   x=100, y=650, width=300, height=20,
                   borderStyle='underlined', textColor=colors.black,  # Corrected
                   forceBorder=True)

    # Save the PDF
    c.save()

# Generate the editable PDF template
create_editable_pdf(template_path)
