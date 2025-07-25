from flask import Flask, render_template, request, send_file, after_this_request
import os
import platform
from datetime import datetime
from num2words import num2words
import pdfkit
from pdfkit.configuration import Configuration
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import shutil

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Cross-platform wkhtmltopdf configuration
wkhtmltopdf_path = os.getenv("WKHTMLTOPDF_PATH")
if not wkhtmltopdf_path:
    if platform.system() == "Windows":
        wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    else:
        wkhtmltopdf_path = "/usr/bin/wkhtmltopdf"
config = Configuration(wkhtmltopdf=wkhtmltopdf_path)

# Google Sheets authentication setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

print("🔐 Loading Google credentials...")
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    print("✅ Google Sheets authorized successfully.")
except Exception as e:
    print("❌ Google Sheets authorization failed:", str(e))
    raise

# Load Google Sheet name from .env
sheet_name = os.getenv("GOOGLE_SHEET_NAME")
print("📄 Loaded sheet name from .env:", sheet_name)
if not sheet_name:
    raise Exception("❌ GOOGLE_SHEET_NAME not found in environment variables!")

try:
    sheet = client.open(sheet_name).sheet1
    print("✅ Google Sheet loaded:", sheet.title)
except Exception as e:
    print("❌ Failed to open Google Sheet:", e)
    raise

# Get next bill number
def get_next_bill_number():
    try:
        records = sheet.get_all_records()
        bill_numbers = []
        for row in records:
            for key in row:
                if key.strip().lower() == 'bill no':
                    bill = row[key]
                    if str(bill).isdigit():
                        bill_numbers.append(int(bill))
                    break
        next_no = str(max(bill_numbers) + 1) if bill_numbers else "1"
        print("📄 Next bill number:", next_no)
        return next_no
    except Exception as e:
        print("❌ Failed to get next bill number:", e)
        return "1"

# Home page
@app.route('/')
def form():
    next_bill_no = get_next_bill_number()
    return render_template('form.html', next_bill_no=next_bill_no)

# Handle form submission
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
    data['items'] = item_details_list

    try:
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        formatted_date_display = date_obj.strftime('%d/%m/%Y')
        formatted_date_filename = date_obj.strftime('%d-%m-%Y')
    except Exception:
        formatted_date_display = data['date']
        formatted_date_filename = data['date']

    data['date'] = formatted_date_display

    # Insert into Google Sheet
    print("📤 Inserting new receipt into Google Sheet...")
    try:
        sheet.insert_row([
            data.get('date', ''),
            data.get('bill_no', ''),
            data.get('name', ''),
            data.get('address', ''),
            item_details,
            data['total'],
            data['total_words'],
            data.get('comments', '')
        ], index=2)
        print("✅ Row inserted successfully!")
    except Exception as e:
        print("❌ Failed to insert row:", str(e))

    # Define PDF file paths
    urdu_font_path = os.path.abspath("static/fonts/NotoNastaliqUrdu-Regular.ttf")
    marathi_font_path = os.path.abspath("static/fonts/NotoSansDevanagari-Regular.ttf")

    safe_bill = data['bill_no'].replace(" ", "_")
    safe_name = data['name'].replace(" ", "_")
    file_name = f"{safe_bill}_{safe_name}_{formatted_date_filename}.pdf"

    rendered = render_template(
        'receipt_template.html',
        data=data,
        urdu_font_path=urdu_font_path,
        marathi_font_path=marathi_font_path
    )

    options = {
        'page-size': 'A5',
        'encoding': 'UTF-8',
        'margin-top': '5mm',
        'margin-bottom': '5mm',
        'margin-left': '5mm',
        'margin-right': '5mm',
        'enable-local-file-access': ''
    }

    pdfkit.from_string(rendered, file_name, options=options, configuration=config)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_name)
        except Exception:
            pass
        return response

    return send_file(file_name, as_attachment=True, download_name=file_name)

# Start the Flask app
if __name__ == '__main__':
    print("📍 wkhtmltopdf path:", wkhtmltopdf_path)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)