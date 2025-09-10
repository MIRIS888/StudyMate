from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import json
import PyPDF2
from docx import Document
import openai
from werkzeug.utils import secure_filename
from models import db, User, StudySession, Note, UserProgress
from forms import LoginForm, RegisterForm, NoteForm
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///studymate.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Pro přístup k této stránce se musíte přihlásit.'

# Vytvoření upload složky
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/favicon.ico')
def favicon():
    return '', 204

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
    """Hlavní stránka - přesměruje na dashboard nebo login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Přihlášení"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('dashboard'))
        flash('Nesprávné uživatelské jméno nebo heslo', 'error')
    
    return render_template('login_new.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registrace"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registrace proběhla úspěšně!', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Uživatelské jméno nebo email již existuje', 'error')
    
    return render_template('register_new.html', form=form)

@app.route('/logout')
def logout():
    """Odhlášení"""
    logout_user()
    flash('Byli jste odhlášeni', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - hlavní stránka po přihlášení"""
    # Získání statistik uživatele
    total_sessions = StudySession.query.filter_by(user_id=current_user.id).count()
    total_study_time = db.session.query(db.func.sum(StudySession.duration_minutes)).filter_by(user_id=current_user.id).scalar() or 0
    total_notes = Note.query.filter_by(user_id=current_user.id).count()
    
    # Poslední aktivity
    recent_sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.created_at.desc()).limit(5).all()
    recent_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).limit(3).all()
    
    return render_template('dashboard_new.html', 
                         total_sessions=total_sessions,
                         total_study_time=total_study_time,
                         total_notes=total_notes,
                         recent_sessions=recent_sessions,
                         recent_notes=recent_notes)

@app.route('/study')
@login_required
def study():
    """Stránka pro analýzu materiálů"""
    materials = load_study_materials()
    return render_template('study_new.html', materials=materials)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Endpoint pro analýzu souboru nebo vybraného materiálu"""
    start_time = datetime.utcnow()
    
    try:
        subject = None
        topic = None
        
        if 'file' in request.files and request.files['file'].filename != '':
            # Analýza nahraného souboru
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                topic = filename.rsplit('.', 1)[0]  # Use filename as topic
                
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
        
        # Calculate study duration
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() / 60)  # in minutes
        
        # Save study session
        session_data = StudySession(
            user_id=current_user.id,
            topic=topic or 'Nespecifikované téma',
            subject=subject,
            duration_minutes=max(1, duration),  # At least 1 minute
            questions_answered=len(result.get('questions', [])),
            materials_analyzed=json.dumps(result) if not result.get('error') else None
        )
        
        db.session.add(session_data)
        
        # Update user progress
        if subject:
            progress = UserProgress.query.filter_by(
                user_id=current_user.id, 
                subject=subject
            ).first()
            
            if not progress:
                progress = UserProgress(
                    user_id=current_user.id,
                    subject=subject
                )
                db.session.add(progress)
            
            progress.update_progress(duration, 0)  # We don't have accuracy yet
        
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Chyba serveru: {str(e)}"})

# Additional routes for new features
@app.route('/analytics')
@login_required
def analytics():
    """Stránka se statistikami učení"""
    return render_template('analytics_new.html')

@app.route('/notes')
@login_required
def notes():
    """Stránka s poznámkami"""
    search = request.args.get('search', '')
    tag = request.args.get('tag', '')
    
    query = Note.query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.filter(
            Note.title.contains(search) | Note.content.contains(search)
        )
    
    if tag:
        query = query.filter(Note.tags.contains(tag))
    
    notes_list = query.order_by(Note.updated_at.desc()).all()
    
    # Get all tags for filter
    all_tags = set()
    for note in Note.query.filter_by(user_id=current_user.id).all():
        all_tags.update(note.tag_list)
    
    return render_template('notes_new.html', 
                         notes=notes_list, 
                         search=search, 
                         selected_tag=tag,
                         all_tags=sorted(all_tags))

@app.route('/notes/new', methods=['GET', 'POST'])
@login_required
def new_note():
    """Vytvoření nové poznámky"""
    form = NoteForm()
    
    # Populate subject choices from study materials
    materials = load_study_materials()
    form.subject.choices = [('', 'Bez předmětu')] + [(subject, subject) for subject in materials.keys()]
    
    if form.validate_on_submit():
        note = Note(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            subject=form.subject.data if form.subject.data else None,
            tags=form.tags.data
        )
        
        db.session.add(note)
        db.session.commit()
        
        flash('Poznámka byla úspěšně vytvořena!', 'success')
        return redirect(url_for('notes'))
    
    return render_template('note_form.html', form=form, title='Nová poznámka')

@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    """Editace poznámky"""
    note = Note.query.get_or_404(note_id)
    
    # Check if user owns this note
    if note.user_id != current_user.id:
        flash('Nemáte oprávnění k editaci této poznámky', 'error')
        return redirect(url_for('notes'))
    
    form = NoteForm(obj=note)
    
    # Populate subject choices
    materials = load_study_materials()
    form.subject.choices = [('', 'Bez předmětu')] + [(subject, subject) for subject in materials.keys()]
    
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        note.subject = form.subject.data if form.subject.data else None
        note.tags = form.tags.data
        note.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Poznámka byla úspěšně aktualizována!', 'success')
        return redirect(url_for('notes'))
    
    return render_template('note_form.html', form=form, title='Editovat poznámku', note=note)

@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    """Smazání poznámky"""
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('Nemáte oprávnění ke smazání této poznámky', 'error')
        return redirect(url_for('notes'))
    
    db.session.delete(note)
    db.session.commit()
    
    flash('Poznámka byla smazána', 'info')
    return redirect(url_for('notes'))

@app.route('/settings')
@login_required
def settings():
    """Stránka s nastaveními"""
    return render_template('settings_new.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create demo user if no users exist
        if User.query.count() == 0:
            demo_user = User(username='demo', email='demo@studymate.cz')
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            print('Demo uživatel byl vytvořen: demo / demo123')
    
    app.run(debug=True)