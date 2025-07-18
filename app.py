# === app.py ===
from flask import Flask, render_template, request, send_file
import pdfkit
import uuid
import os
from num2words import num2words
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.to_dict()
    total = 0
    i = 1
    descriptions = []

    while f'desc{i}' in data or f'charge{i}' in data:
        try:
            charge = float(data.get(f'charge{i}', 0))
            total += charge
        except ValueError:
            charge = 0
        descriptions.append(f"{data.get(f'desc{i}', '')} - {charge}")
        i += 1

    data['item_count'] = i - 1
    data['total'] = "{:.2f}".format(total)
    data['total_words'] = num2words(total, to='cardinal', lang='en').title() + " Rupees Only"

    try:
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        formatted_date_display = date_obj.strftime('%d/%m/%Y')
        formatted_date_filename = date_obj.strftime('%d-%m-%Y')
    except Exception:
        formatted_date_display = data['date']
        formatted_date_filename = data['date']

    data['date'] = formatted_date_display

    # Save to Google Sheet
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
    client = gspread.authorize(creds)

    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "Patti_Form_Data")
    sheet = client.open(sheet_name).sheet1

    desc_combined = "\n".join(descriptions)
    sheet.append_row([
        formatted_date_display,
        data.get('bill_no', ''),
        data.get('name', ''),
        data.get('address', ''),
        desc_combined,
        data.get('total', ''),
        data.get('total_words', ''),
        data.get('comments', '')
    ])

    urdu_font_path = os.path.abspath("static/fonts/NotoNastaliqUrdu-Regular.ttf")
    marathi_font_path = os.path.abspath("static/fonts/NotoSansDevanagari-Regular.ttf")

    rendered = render_template('receipt_template.html', data=data,
                               urdu_font_path=urdu_font_path, marathi_font_path=marathi_font_path)

    safe_bill = data['bill_no'].replace(" ", "_")
    safe_name = data['name'].replace(" ", "_")
    file_name = f"{safe_bill}_{safe_name}_{formatted_date_filename}.pdf"

    # Use default wkhtmltopdf
    config = pdfkit.configuration()
    options = {
        'page-size': 'A5',
        'encoding': 'UTF-8',
        'margin-top': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'margin-right': '10mm'
    }

    pdfkit.from_string(rendered, file_name, configuration=config, options=options)
    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
