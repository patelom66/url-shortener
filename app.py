import secrets
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Database Model ───────────────────────────────────────────────
class URL(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    original    = db.Column(db.String(2048), nullable=False)
    short_code  = db.Column(db.String(6), unique=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<URL {self.short_code} → {self.original[:40]}>'


# ─── Helper ───────────────────────────────────────────────────────
def generate_short_code():
    """Generate a unique 6-character code."""
    while True:
        code = secrets.token_urlsafe(4)[:6]   # URL-safe, 6 chars
        if not URL.query.filter_by(short_code=code).first():
            return code


# ─── Routes ───────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    error     = None

    if request.method == 'POST':
        original = request.form.get('original_url', '').strip()

        # Basic validation
        if not original:
            error = "Please enter a URL."
        elif not (original.startswith('http://') or original.startswith('https://')):
            error = "URL must start with http:// or https://"
        else:
            # Check if this long URL was already shortened
            existing = URL.query.filter_by(original=original).first()
            if existing:
                short_url = request.host_url + existing.short_code
            else:
                code      = generate_short_code()
                new_url   = URL(original=original, short_code=code)
                db.session.add(new_url)
                db.session.commit()
                short_url = request.host_url + code

    return render_template('index.html', short_url=short_url, error=error)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first()
    if url is None:
        abort(404)
    return redirect(url.original)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ─── Entry Point ──────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()          # Creates urls.db automatically on first run
    app.run(debug=True)