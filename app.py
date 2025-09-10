from flask import Flask, request, render_template, jsonify
import os
import json
import PyPDF2
from docx import Document
import openai
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Vytvoření upload složky
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# OpenAI API klíč - nastavte svůj klíč zde nebo jako environment proměnnou
openai.api_key = os.getenv('OPENAI_API_KEY')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_txt_file(filepath):
    """Čte obsah TXT souboru"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='cp1250') as file:
            return file.read()

def read_pdf_file(filepath):
    """Čte obsah PDF souboru"""
    text = ""
    with open(filepath, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx_file(filepath):
    """Čte obsah DOCX souboru"""
    doc = Document(filepath)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def load_study_materials():
    """Načte studijní materiály z databáze (JSON soubor)"""
    try:
        with open('study_materials.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def analyze_with_openai(text):
    """Pošle text na OpenAI API a vrátí analýzu"""
    try:
        client = openai.OpenAI()
        
        prompt = f"""
        Analyzuj následující studijní text a vytvoř:
        
        1. SHRNUTÍ - hlavní body a klíčové informace (3-5 bodů)
        2. TESTOVÉ OTÁZKY - 5 otázek s multiple choice možnostmi (A, B, C, D) včetně správných odpovědí
        3. KARTIČKY - 5 dvojic otázka-odpověď pro procvičování
        
        Odpovídej ve formátu JSON:
        {{
            "summary": ["bod1", "bod2", "bod3"],
            "questions": [
                {{
                    "question": "text otázky",
                    "options": ["A) možnost1", "B) možnost2", "C) možnost3", "D) možnost4"],
                    "correct": "A"
                }}
            ],
            "flashcards": [
                {{
                    "question": "otázka",
                    "answer": "odpověď"
                }}
            ]
        }}
        
        Text k analýze:
        {text}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # Parsování JSON odpovědi
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "error": f"Chyba při analýze: {str(e)}",
            "summary": ["Nepodařilo se analyzovat text"],
            "questions": [],
            "flashcards": []
        }

@app.route('/')
def index():
    """Hlavní stránka"""
    materials = load_study_materials()
    return render_template('index.html', materials=materials)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Endpoint pro analýzu souboru nebo vybraného materiálu"""
    try:
        if 'file' in request.files and request.files['file'].filename != '':
            # Analýza nahraného souboru
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Čtení obsahu podle typu souboru
                if filename.lower().endswith('.pdf'):
                    text = read_pdf_file(filepath)
                elif filename.lower().endswith('.docx'):
                    text = read_docx_file(filepath)
                else:  # txt
                    text = read_txt_file(filepath)
                
                # Smazání dočasného souboru
                os.remove(filepath)
                
            else:
                return jsonify({"error": "Nepodporovaný typ souboru"})
                
        elif 'subject' in request.form and 'topic' in request.form:
            # Analýza vybraného materiálu z databáze
            subject = request.form['subject']
            topic = request.form['topic']
            materials = load_study_materials()
            
            if subject in materials and topic in materials[subject]:
                text = materials[subject][topic]
            else:
                return jsonify({"error": "Materiál nebyl nalezen"})
        else:
            return jsonify({"error": "Není vybrán soubor ani materiál"})
        
        # Analýza textu pomocí OpenAI
        result = analyze_with_openai(text)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Chyba serveru: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)