import os
import requests
from flask import Flask, request, url_for, flash, redirect, render_template
from dotenv import load_dotenv
from requests import ConnectionError, HTTPError
from urllib.parse import urlparse
from page_analyzer.utils import validate_url
from page_analyzer.page_checker import get_content_of_page
from page_analyzer import db

app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

print("HOST:", os.getenv("HOST"))
print("PORT:", os.getenv("PORT"))
print("USER:", os.getenv("USER"))
print("PASSWORD:", os.getenv("PASSWORD"))
print("DATABASE:", os.getenv("DATABASE"))


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def post_url():
    url = request.form.get('url')
    errors = validate_url(url)
    if errors:
        for error in errors:
            flash(error, "alert alert-danger")
        return render_template(
            'index.html',
            url_input=url,
        ), 422
    parsed_url = urlparse(url)
    valid_url = parsed_url.scheme + '://' + parsed_url.netloc
    result = db.get_url_id_by_name(valid_url)
    if result:
        flash("Страница уже существует", "alert alert-info")
        return redirect(url_for('url_added', id=result.id))

    url_id = db.add_url(valid_url)
    flash("Страница успешно добавлена", "alert alert-success")
    return redirect(url_for('url_added', id=url_id))


@app.route('/urls/<id>')
def url_added(id):
    url_data = db.get_url_by_id(id)
    url_name, url_created_at = url_data
    checks = db.get_url_checks_by_id(id)
    return render_template(
        'page.html',
        url_name=url_name,
        url_id=id,
        url_created_at=url_created_at.date(),
        checks=checks
    )


@app.get('/urls')
def urls_get():
    checks = db.get_all_urls()
    return render_template(
        'pages.html',
        checks=checks
    )


@app.route('/urls/<id>/checks', methods=['POST'])
def id_check(id):
    url_data = db.get_url_by_id(id)
    url_name = url_data.name
    try:
        response = requests.get(url_name)
        response.raise_for_status()
    except (ConnectionError, HTTPError):
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('url_added', id=id))

    status_code = response.status_code
    h1, title, meta = get_content_of_page(response.text)
    db.add_url_check(id, status_code, h1, title, meta)
    flash("Страница успешно проверена", "alert alert-success")
    return redirect(url_for('url_added', id=id))
