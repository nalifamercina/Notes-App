import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-production")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access your notes."


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    notes = db.relationship("Note", backref="author", lazy=True, cascade="all, delete-orphan")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not username or not email or not password:
            flash("All fields are required.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif User.query.filter(or_(User.username == username, User.email == email)).first():
            flash("That username or email is already registered.", "danger")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    recent_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).limit(5).all()
    updated_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).limit(5).all()
    total_notes = Note.query.filter_by(user_id=current_user.id).count()
    return render_template("dashboard.html", total_notes=total_notes, recent_notes=recent_notes, updated_notes=updated_notes)


@app.route("/notes")
@login_required
def notes():
    query = request.args.get("q", "").strip()
    note_query = Note.query.filter_by(user_id=current_user.id)
    if query:
        pattern = f"%{query}%"
        note_query = note_query.filter(or_(Note.title.ilike(pattern), Note.content.ilike(pattern)))
    user_notes = note_query.order_by(Note.updated_at.desc()).all()
    return render_template("notes.html", notes=user_notes, query=query)


@app.route("/notes/new", methods=["GET", "POST"])
@login_required
def create_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("A note needs both a title and content.", "danger")
        else:
            db.session.add(Note(title=title, content=content, author=current_user))
            db.session.commit()
            flash("Note created.", "success")
            return redirect(url_for("notes"))
    return render_template("note_form.html", note=None)


def get_owned_note(note_id):
    return Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    note = get_owned_note(note_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("A note needs both a title and content.", "danger")
        else:
            note.title, note.content = title, content
            db.session.commit()
            flash("Note updated.", "success")
            return redirect(url_for("notes"))
    return render_template("note_form.html", note=note)


@app.post("/notes/<int:note_id>/delete")
@login_required
def delete_note(note_id):
    note = get_owned_note(note_id)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for("notes"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
