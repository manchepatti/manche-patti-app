# === app.py ===
from flask import Flask, render_template, request, send_file
import pdfkit
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

    # Calculate total charges
    total = 0
    i = 1
    item_details = []
    while f'desc{i}' in data or f'charge{i}' in data:
        desc = data.get(f'desc{i}', '').strip()
        charge = data.get(f'charge{i}', '0').strip()
        try:
            amount = float(charge)
            total += amount
            if desc:
                item_details.append(f"{i}. {desc} - ₹{amount:.2f}")
        except ValueError:
            pass
        i += 1

    data['item_count'] = i - 1
    data['total'] = "{:.2f}".format(total)
    data['total_words'] = num2words(total, to='cardinal', lang='en').title() + " Rupees Only"

    # Format the date for display and filename
    try:
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        formatted_date_display = date_obj.strftime('%d/%m/%Y')
        formatted_date_filename = date_obj.strftime('%d-%m-%Y')
    except Exception:
        formatted_date_display = data['date']
        formatted_date_filename = data['date']

    data['date'] = formatted_date_display

    # === Save to Google Sheets ===
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("Patti Receipts").sheet1
        row_data = [
            data['date'],
            data['bill_no'],
            data['name'],
            data['address'],
            ", ".join(item_details),
            data['total'],
            data['total_words'],
            data.get('comments', '')
        ]
        sheet.append_row(row_data)
    except Exception as e:
        print("[Google Sheet Error]", str(e))

    # Font paths
    urdu_font_path = os.path.abspath("static/fonts/NotoNastaliqUrdu-Regular.ttf")
    marathi_font_path = os.path.abspath("static/fonts/NotoSansDevanagari-Regular.ttf")

    # Render the HTML template
    rendered = render_template(
        'receipt_template.html',
        data=data,
        urdu_font_path=urdu_font_path,
        marathi_font_path=marathi_font_path
    )

    # Create the file name for the PDF
    safe_bill = data['bill_no'].replace(" ", "_")
    safe_name = data['name'].replace(" ", "_")
    file_name = f"{safe_bill}_{safe_name}_{formatted_date_filename}.pdf"

    # PDF options
    config = pdfkit.configuration(wkhtmltopdf=r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    options = {
        'page-size': 'A5',
        'encoding': 'UTF-8',
        'margin-top': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'margin-right': '10mm'
    }

    # Generate the PDF
    pdfkit.from_string(rendered, file_name, configuration=config, options=options)
    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
