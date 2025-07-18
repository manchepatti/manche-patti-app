# === app.py ===
from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
from num2words import num2words
import pdfkit
from pdfkit.configuration import Configuration  # 👈 Add this
config = Configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")  # 👈 Set path
pdfkit.from_string(rendered, file_name, options=options, configuration=config)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv  # ✅ Step 1: Load .env

load_dotenv()  # ✅ Step 2: Make sure environment variables are available

app = Flask(__name__)

# --- Google Sheet Setup ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ✅ Step 3: Make sure the sheet name is properly loaded from .env
sheet_name = os.getenv("GOOGLE_SHEET_NAME")
if not sheet_name:
    raise Exception("❌ GOOGLE_SHEET_NAME not found in .env file!")

sheet = client.open(sheet_name).sheet1

# --- Get Next Bill Number ---
def get_next_bill_number():
    records = sheet.get_all_records()
    bill_numbers = []

    for row in records:
        for key in row:
            if key.strip().lower() == 'bill no':
                bill = row[key]
                if str(bill).isdigit():
                    bill_numbers.append(int(bill))
                break

    return str(max(bill_numbers) + 1) if bill_numbers else "1"

# --- Routes ---
@app.route('/')
def form():
    next_bill_no = get_next_bill_number()
    return render_template('form.html', next_bill_no=next_bill_no)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.to_dict()
    total = 0
    i = 1
    item_details_list = []

    while f'desc{i}' in data or f'charge{i}' in data:
        desc = data.get(f'desc{i}', '').strip()
        charge = data.get(f'charge{i}', '').strip()
        if desc or charge:
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

    # Insert to Google Sheet (at top, after headers)
    sheet.insert_row([
        data['date'],
        data['bill_no'],
        data['name'],
        data['address'],
        item_details,
        data['total'],
        data['total_words'],
        data.get('comments', '')
    ], index=2)

    # PDF generation
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

    pdfkit.from_string(rendered, file_name, options=options, configuration=config)
    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
