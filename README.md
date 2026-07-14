# Notes App

A personal notes application built with Flask, SQLite, SQLAlchemy, Bootstrap, and Flask-Login.

## Included features

- Secure registration, login, logout, password hashing, and sessions
- Create, view, edit, delete, and search personal notes
- Owner-only access to notes
- Dashboard total, recently created notes, and recently updated notes

## Run locally

1. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install packages: `pip install -r requirements.txt`
3. Start the app: `python app.py`
4. Open `http://127.0.0.1:5000`

Before deploying, set a strong `SECRET_KEY` environment variable. The SQLite database is created automatically in the Flask `instance` folder.
