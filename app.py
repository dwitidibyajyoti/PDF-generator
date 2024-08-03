from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import tempfile
import os
from flask_cors import CORS
from PyPDF2 import PdfReader, PdfWriter
import random
import string
import qrcode
import logging
import datetime
import io

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# You can set the level to DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def generate_certificate_number(length=10):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def create_certificate(name, company_name, reg_date, issue_date, expiry_date, category, certificate_type, address):
    try:
        existing_pdf_path = 'CERTIFICATE_LICENSE.pdf'
        existing_pdf = PdfReader(existing_pdf_path)
        page = existing_pdf.pages[0]
        page_width = float(page.mediabox.upper_right[0])/2
        margin = 30
        # print(page_width)
    except Exception as e:
        print(f"Error reading existing PDF: {e}")
        return

    try:
        # Generate a unique certificate number
        certificate_number = generate_certificate_number()

        # Create a PDF with the text overlay
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        name_section = f'This is to certify, {name} of'

        c.setFont("Helvetica-Bold", 14)
        name_width = c.stringWidth(name_section, "Helvetica-Bold", 14)
        certificate_width = c.stringWidth(
            certificate_type.upper(), "Helvetica-Bold", 14)
        # print(certificate_width,'>>>>>>>>>>',(page_width - certificate_width)/2)

        x_position = 200
        # print(f"Page Width: {certificate_width}")
        c.drawString((page_width)-(certificate_width/2) + margin,
                     685, f"({certificate_type.upper()})")
        c.drawString((page_width)-(name_width/2) + margin, 650, name_section)

        # Wrap and center the company name text
        styles = getSampleStyleSheet()
        styleN = styles["BodyText"]
        styleN.alignment = TA_CENTER
        styleN.leading = 20
        styleN.fontSize = 20  # Set font size to 20
        company_name_paragraph = Paragraph(f'<b>{company_name}</b>', styleN)

        additional_text_style = ParagraphStyle(
            'Calibri',
            parent=styles['BodyText'],
            fontSize=12,
            leading=12,
            alignment=TA_CENTER,
            spaceBefore=2,
            spaceAfter=2
        )

        additional_text = f"""{category}"""
        # category

        additional_text_paragraph = Paragraph(
            additional_text, additional_text_style)

        address_paragraph = Paragraph(address, additional_text_style)

        data = [[company_name_paragraph], [
            address_paragraph], [additional_text_paragraph]]

        # Adjust width as necessary
        table = Table(data, colWidths=[250],  rowHeights=[50, 30, 70])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.white),
        ]))

        # Add table to canvas
        table.wrapOn(c, page_width, 0)
        table.drawOn(c, 210, 490)

        # Additional text
        c.setFont("Helvetica", 12)
        c.drawString(332, 446, certificate_number)
        c.drawString(332, 431, reg_date)
        c.drawString(332, 416, issue_date)
        c.drawString(332, 401, expiry_date)

        c.setStrokeColor(colors.green)
        # c.rect(100, 380, 130, 20)  # Adjust coordinates and size as needed

        c.setFont("Helvetica-Bold", 12)
        office_address_width = c.stringWidth(
            f"Office: {'Electrovolta House, Ministries, Accra, Ghana'}", "Helvetica-Bold", 12)

        c.drawString((page_width)-(office_address_width/2) + 60, 129,
                     f"Office: {'Electrovolta House, Ministries, Accra, Ghana'}")

        # Generate the QR code
        qr_data = f"Name: {name}\nCompany: {company_name}\nReg Date: {reg_date}\nIssue Date: {issue_date}\nExpiry Date: {expiry_date}\nCategory: {category}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        img = Image.open(img_buffer)
        c.drawInlineImage(img, 430, 370, width=110, height=110)

        c.save()
        packet.seek(0)
    except Exception as e:
        print(f"Error creating the PDF overlay: {e}")
        return

    try:
        # Merge the overlay with the existing PDF
        new_pdf = PdfReader(packet)
        output = PdfWriter()

        # Add the "watermark" (which is the new pdf) on the existing page
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        pdf_buffer = io.BytesIO()
        output.write(pdf_buffer)
        pdf_buffer.seek(0)

        return pdf_buffer

        # # Finally, write "output" to a real file
        # output_path = "certificate_output.pdf"
        # with open(output_path, "wb") as output_stream:
        #     output.write(output_stream)
        # >>>>>>.. only for colab .............
        # display_first_page_as_image(output_path)
        # >>>>>>><<<<<<<<<<<<
    except Exception as e:
        print(f"Error merging and writing the PDF: {e}")

# Example usage
# logger.debug(f"Error: {'testtt'}")


@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided")

        reg_date = data.get('reg_date')
        issue_date = data.get('issue_date')
        expiryDate = data.get('expiry_date')
        name = data.get('name')
        address = data.get('address')
        certificate_type = data.get('type')
        category = data.get('category')
        company_name = data.get('company_name')

        if certificate_type == 'external installation':
            category = 'As a licensed Electrical Contractor to carry out external installation under the provision of Electricity Supply and Distribution (Technical and Operational) Rules, 2005 LI 1816)'
        else:
            category = f'{category}, Category 4- Construction of 33kV and 111kV Overhead Line on Wood/Tubular Steel Poles (pole height not exceeding 14m) Underground Cable, Installation of Distribution Transformers and LV Network'

        # logger.debug(f"Error: {category}")
        try:
            pdf_buffer = create_certificate(name, company_name, reg_date,
                                            issue_date, expiryDate, category, certificate_type, address)
        except Exception as e:
            app.logger.debug(f"Error generating certificate: {e}")
        # # Create a PDF buffer
        # # Replace with the path to your existing PDF
        # existing_pdf_path = 'Sample_certificate2.pdf'
        # existing_pdf = PdfReader(existing_pdf_path)
        # page = existing_pdf.pages[0]
        # page_width = float(page.mediabox.upper_right[0])
        # # Generate a unique certificate number
        # certificate_number = generate_certificate_number()

        # # Create a PDF with the text overlay
        # packet = io.BytesIO()
        # c = canvas.Canvas(packet, pagesize=letter)
        # text = f'This is to certify, {name} of'

        # c.setFont("Helvetica-Bold", 14)
        # text_width = c.stringWidth(text, "Helvetica-Bold", 12)
        # text_company = c.stringWidth(company_name, "Helvetica-Bold", 20)

        # x_position = (page_width - text_width) / 2
        # x_position_company_name = (page_width - text_company) / 2

        # c.drawString(x_position, 650, text)

        # c.setFont("Helvetica-Bold", 20)
        # c.drawString(x_position_company_name, 600, company_name)

        # # Adjust the position as needed
        # c.setFont("Helvetica", 12)
        # c.drawString(332, 446, certificate_number)
        # c.drawString(332, 431, reg_date)  # Adjust the position as needed
        # c.drawString(332, 416, issue_date)  # Adjust the position as needed
        # c.drawString(332, 401, expiryDate)  # Adjust the position as needed

        # c.line(332, 360, 500, 400)

        # c.save()

        # # Move to the beginning of the StringIO buffer
        # packet.seek(0)
        # overlay_pdf = PdfReader(packet)
        # overlay_page = overlay_pdf.pages[0]

        # # Merge the overlay with the existing page
        # page.merge_page(overlay_page)

        # # Save the result
        # output = PdfWriter()
        # output.add_page(page)

        # pdf_buffer = io.BytesIO()
        # output.write(pdf_buffer)
        # pdf_buffer.seek(0)
        current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        download_name = f"{'license_certificate'}_{current_datetime}.pdf"
        logger.debug(f"Error: {download_name}")

        return send_file(pdf_buffer, as_attachment=True, download_name=download_name, mimetype='application/pdf')
    except Exception as e:
        logger.debug(f"Error: {e}")
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
