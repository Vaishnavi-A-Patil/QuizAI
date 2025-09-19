import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import docx
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
EXTRACT_FOLDER = os.path.join(os.getcwd(), 'extracted')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'png', 'jpg', 'jpeg'}

# Ensure folders exist
for folder in [UPLOAD_FOLDER, EXTRACT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(filepath, ext):
    text = ""
    if ext == "pdf":
        reader = PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif ext == "docx":
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
    return text.strip()

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        ext = filename.rsplit('.', 1)[1].lower()
        extracted_text = extract_text(filepath, ext)

        # Save extracted text into a .txt file
        text_filename = filename.rsplit('.', 1)[0] + "_extracted.txt"
        text_filepath = os.path.join(EXTRACT_FOLDER, text_filename)
        with open(text_filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return render_template("result.html", filename=filename, text=extracted_text, download_file=text_filename)

    else:
        flash("File type not allowed!")
        return redirect(url_for('index'))

@app.route('/download/<download_file>')
def download_file(download_file):
    file_path = os.path.join(EXTRACT_FOLDER, download_file)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
