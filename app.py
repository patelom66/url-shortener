import secrets
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ─── Models ───────────────────────────────────────────────────────
class URL(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    original   = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicks     = db.relationship('Click', backref='url', lazy=True)

    @property
    def click_count(self):
        return len(self.clicks)


class Click(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    url_id     = db.Column(db.Integer, db.ForeignKey('url.id'), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    browser    = db.Column(db.String(100))
    platform   = db.Column(db.String(100))


# ─── Helper ───────────────────────────────────────────────────────
def generate_short_code():
    while True:
        code = secrets.token_urlsafe(4)[:6]
        if not URL.query.filter_by(short_code=code).first():
            return code


def parse_user_agent(ua_string):
    """Extract basic browser and platform info from user agent."""
    ua = ua_string.lower()

    if 'chrome' in ua and 'edg' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'edg' in ua:
        browser = 'Edge'
    else:
        browser = 'Other'

    if 'windows' in ua:
        platform = 'Windows'
    elif 'mac' in ua:
        platform = 'Mac'
    elif 'android' in ua:
        platform = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        platform = 'iOS'
    elif 'linux' in ua:
        platform = 'Linux'
    else:
        platform = 'Other'

    return browser, platform


# ─── Routes ───────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    error     = None

    if request.method == 'POST':
        original = request.form.get('original_url', '').strip()

        if not original:
            error = "Please enter a URL."
        elif not (original.startswith('http://') or original.startswith('https://')):
            error = "URL must start with http:// or https://"
        else:
            existing = URL.query.filter_by(original=original).first()
            if existing:
                short_url = request.host_url + existing.short_code
            else:
                code    = generate_short_code()
                new_url = URL(original=original, short_code=code)
                db.session.add(new_url)
                db.session.commit()
                short_url = request.host_url + code

    return render_template('index.html', short_url=short_url, error=error)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first()
    if url is None:
        abort(404)

    # Log the click
    ua_string        = request.headers.get('User-Agent', '')
    browser, platform = parse_user_agent(ua_string)
    click = Click(url_id=url.id, browser=browser, platform=platform)
    db.session.add(click)
    db.session.commit()

    return redirect(url.original)


@app.route('/dashboard')
def dashboard():
    urls = URL.query.order_by(URL.created_at.desc()).all()

    # Total stats
    total_urls   = len(urls)
    total_clicks = sum(u.click_count for u in urls)

    # Clicks per day for the last 7 days (for line chart)
    from collections import defaultdict
    from datetime import timedelta
    today     = datetime.utcnow().date()
    day_range = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    clicks_by_day = defaultdict(int)

    all_clicks = Click.query.all()
    for click in all_clicks:
        day = click.clicked_at.date()
        if day in day_range:
            clicks_by_day[day] += 1

    chart_labels = [d.strftime('%b %d') for d in day_range]
    chart_data   = [clicks_by_day[d] for d in day_range]

    # Top 5 URLs by clicks (for bar chart)
    top_urls = sorted(urls, key=lambda u: u.click_count, reverse=True)[:5]
    top_labels = [u.short_code for u in top_urls]
    top_data   = [u.click_count for u in top_urls]

    return render_template('dashboard.html',
        urls=urls,
        total_urls=total_urls,
        total_clicks=total_clicks,
        chart_labels=chart_labels,
        chart_data=chart_data,
        top_labels=top_labels,
        top_data=top_data
    )


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)