# ⚡ SnapLink — URL Shortener

A full-stack URL shortener built with Python, Flask, and SQLite.

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/url-shortener.git
cd url-shortener

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

## Features (Week 1)
- Shorten any valid URL to a 6-character code
- Redirects instantly to the original URL
- Duplicate detection — same long URL returns same short code
- Input validation with error messages
- One-click copy to clipboard