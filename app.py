# === app.py ===
from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
from num2words import num2words
import pdfkit
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive.file", 
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(os.getenv("GOOGLE_SHEET_NAME")).sheet1

@app.route('/')
def form():
    # Fetch last Bill No from top row (row 2)
    try:
        records = sheet.get_all_records()
        if records:
            latest_bill_no = int(records[0]['Bill No']) + 1
        else:
            latest_bill_no = 1
    except:
        latest_bill_no = 1

    return render_template('form.html', bill_no=latest_bill_no)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.to_dict()
    total = 0
    i = 1
    item_details_list = []

    while f'desc{i}' in data or f'charge{i}' in data:
        desc = data.get(f'desc{i}', '').strip()
        charge = data.get(f'charge{i}', '').strip()
        item_details_list.append(f"{desc} - ₹{charge}")
        try:
            total += float(charge)
        except ValueError:
            pass
        i += 1

    item_details = "\n".join(item_details_list)
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

    # Insert at top of Google Sheet (after headers)
    sheet.insert_row([
        data['date'],
        data['bill_no'],
        data['name'],
        data['address'],
        item_details,
        data['total'],
        data['total_words'],
        data.get('comments', '')
    ], 2)

    # PDF Generation
    rendered = render_template('receipt_template.html', data=data)
    safe_bill = data['bill_no'].replace(" ", "_")
    safe_name = data['name'].replace(" ", "_")
    file_name = f"{safe_bill}_{safe_name}_{formatted_date_filename}.pdf"

    options = {
        'page-size': 'A5',
        'encoding': 'UTF-8',
        'margin-top': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'margin-right': '10mm'
    }

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    pdfkit.from_string(rendered, file_name, options=options, configuration=config)

    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
