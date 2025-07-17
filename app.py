# app.py

from flask import Flask, render_template, request, send_file
from weasyprint import HTML, CSS
import uuid
import os
from num2words import num2words
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.to_dict()
    total = 0
    i = 1
    while f'desc{i}' in data or f'charge{i}' in data:
        try:
            total += float(data.get(f'charge{i}', 0))
        except ValueError:
            pass
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

    # Font paths
    urdu_font_path = os.path.abspath("static/fonts/NotoNastaliqUrdu-Regular.ttf")
    marathi_font_path = os.path.abspath("static/fonts/NotoSansDevanagari-Regular.ttf")

    rendered_html = render_template('receipt_template.html', data=data,
                                    urdu_font_path=urdu_font_path, marathi_font_path=marathi_font_path)

    file_name = f"{data['bill_no'].replace(' ', '_')}_{data['name'].replace(' ', '_')}_{formatted_date_filename}.pdf"

    html = HTML(string=rendered_html)
    css = CSS(string='''
        @page { size: A5; margin: 10mm; }
        body { font-family: 'DejaVu Sans'; }
    ''')
    html.write_pdf(file_name, stylesheets=[css])

    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
