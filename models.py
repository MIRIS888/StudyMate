from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.username}>'

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    duration_minutes = db.Column(db.Integer, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    materials_analyzed = db.Column(db.Text, nullable=True)  # JSON string of analyzed content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def accuracy_percentage(self):
        if self.questions_answered == 0:
            return 0
        return round((self.correct_answers / self.questions_answered) * 100, 1)
    
    def __repr__(self):
        return f'<StudySession {self.topic}>'

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    subject = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def tag_list(self):
        """Return list of tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def __repr__(self):
        return f'<Note {self.title}>'

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    total_study_time = db.Column(db.Integer, default=0)  # in minutes
    sessions_count = db.Column(db.Integer, default=0)
    average_accuracy = db.Column(db.Float, default=0.0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Make sure user can have only one progress record per subject
    __table_args__ = (db.UniqueConstraint('user_id', 'subject', name='user_subject_unique'),)
    
    def update_progress(self, session_duration, accuracy):
        """Update progress based on new study session"""
        self.sessions_count += 1
        self.total_study_time += session_duration
        
        # Calculate new average accuracy
        if self.sessions_count == 1:
            self.average_accuracy = accuracy
        else:
            # Weighted average with previous accuracy
            self.average_accuracy = ((self.average_accuracy * (self.sessions_count - 1)) + accuracy) / self.sessions_count
        
        self.last_activity = datetime.utcnow()
    
    def __repr__(self):
        return f'<UserProgress {self.subject}>'