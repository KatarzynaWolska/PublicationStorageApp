from flask import Flask
from flask import request
from flask import make_response, send_file
from flask import render_template
from flask import jsonify
from os import getenv
from uuid import uuid4
from jwt import encode
from dotenv import load_dotenv
import datetime
import redis
import json
import requests
import os
import base64
import io
import cgi
load_dotenv(verbose=True)


PDF = getenv("PDF_HOST")
API = getenv("API_HOST")
SESSION_TIME = int(getenv("SESSION_TIME"))

redis_auth = redis.Redis(host='redis_auth', port=6381)

app = Flask(__name__)

@app.route('/') # MUSZE CHYBA PODODAWAC DO TRASY ID UZYTKOWNIKA !!!!!!!!!!!!!!!!
def index():
    session_id = request.cookies.get('session_id') # zmienić tą nazwę
    response = redirect('/login')
    
    if session_id != None and redis_auth.get("session_id") != None and session_id == redis_auth.get("session_id").decode('utf-8'):
        response = redirect("/welcome")

    return response


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    res = requests.post('http://api:5000/login_user', json={'username' : username, 'password' : password})
    response = make_response('', 303)

    if res.status_code == 200:
        session_id = str(uuid4())
        redis_auth.set("session_id", session_id, ex=SESSION_TIME)
        response.set_cookie("session_id", session_id, max_age=SESSION_TIME)
        response.headers["Location"] = "/welcome"     # ogarnąc czy nie da sie lepiej
        redis_auth.set('token', res.text)
        return response
    else:
        response.set_cookie("session_id", "INVALIDATE", max_age=-1)
        return redirect("/login")


@app.route('/add_publication_form')
def add_publication_form():
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            return render_template('add_publication.html')

    return redirect('/login')


@app.route('/update_publication_form/<pid>')
def update_publication_form(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            res_publication = requests.get(f'http://api:5000/publications/{pid}', headers={'Authorization': redis_auth.get('token').decode('utf-8')})

            if res_publication.status_code == 200:
                pub = res_publication.json()

                return render_template('update_publication.html', PID=pid, name_value=pub['name'], authors_value=pub['authors'], year_value=pub['year'], publisher_value=pub['publisher'])
            else:
                return redirect('/user_publications')

    return redirect('/login')


@app.route('/add_user_publication', methods=['POST'])
def add_user_publication():
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            name = request.form.get('name')
            authors = request.form.get('authors')
            year = request.form.get('year')
            publisher = request.form.get('publisher')

            res = requests.post('http://api:5000/publications', json={'name' : name, 'authors' : authors, 'year': year, 'publisher': publisher}, headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            print(res.text)
            print(res.status_code)
            return redirect('/user_publications')
    
    return redirect('/login')


@app.route('/welcome', methods=['GET'])
def welcome():
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            return render_template('welcome.html')

    return render_template('login.html')


@app.route('/user_publications/<pid>')
def get_user_publication(pid):    
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            
            res_publication = requests.get(f'http://api:5000/publications/{pid}', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            res_pub_files = requests.get(f'http://api:5000/publications/{pid}/files', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            
            if res_publication.status_code == 200 and res_pub_files.status_code == 200:
                publication = res_publication.json()

                if bool(res_pub_files.json()):
                    files = res_pub_files.json()
                else:
                    files = None

                return render_template('publication.html', PID=pid, publication=json.dumps(publication), files_list=json.dumps(files))
            else:
                print(res_publication.text)
                print(res_pub_files.text)
    return redirect('/login')


@app.route('/user_publications/<pid>/update', methods=['POST'])
def update_publication(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            name = request.form.get('name')
            authors = request.form.get('authors')
            year = request.form.get('year')
            publisher = request.form.get('publisher')

            res = requests.put(f'http://api:5000/publications/{pid}', json={'name' : name, 'authors' : authors, 'year': year, 'publisher': publisher}, headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            print(res.text)
            print(res.status_code)
            return redirect('/user_publications')

    return redirect('/login')


@app.route('/user_publications/<pid>/upload_file', methods=['POST'])
def upload_file(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            f = request.files.get('file')
            file_to_send = {'file': (f.filename, f.read(), f.content_type)}
            if f.filename == '':
                return redirect(f'/user_publications/{pid}')

            res = requests.post(f'http://api:5000/publications/{pid}/files', files=file_to_send, headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            if res.status_code == 200:
                print(res.text)
                return redirect(f'/user_publications/{pid}')
            else:
                print(res.text)
    return redirect('/login')


@app.route('/user_publications/<pid>/files/<fid>', methods=['GET'])
def download_file(pid, fid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            
            res = requests.get(f'http://api:5000/publications/{pid}/files/{fid}', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            
            value, params = cgi.parse_header(res.headers['Content-Disposition'])
            return send_file(io.BytesIO(res.content), mimetype=res.headers['Content-Type'], attachment_filename=params['filename'], as_attachment=True)
            #return send_file(res.content, mimetype=request.headers['Content-Type'],  as_attachment=True)
            #return send_file(io.BytesIO(file_to_download.encode('ISO-8859-1')), mimetype=file_content_type, attachment_filename=file_name, as_attachment=True)


    return redirect('/login')

    
@app.route('/user_publications/<pid>/delete')
def delete_publication(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            res = requests.delete(f'http://api:5000/publications/{pid}', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            print(res.text)
            return redirect('/user_publications')

    return redirect('/login')


@app.route('/user_publications/<pid>/files/<fid>/delete')
def delete_file(pid, fid):
    session_id = request.cookies.get('session_id')

    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):
            res = requests.delete(f'http://api:5000/publications/{pid}/files/{fid}', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            print(res.text)
            return redirect(f'/user_publications/{pid}')

    return redirect('/login')


@app.route('/user_publications')
def user_publications():
    session_id = request.cookies.get('session_id')
    
    if session_id:
        if(redis_auth.get("session_id") != None and redis_auth.get("session_id").decode('utf-8') == session_id):

            res = requests.get('http://api:5000/publications', headers={'Authorization': redis_auth.get('token').decode('utf-8')})
            
            if res.status_code == 200:
                publications = res.json()

                """
                if bool(publications):
                    pubs = json.dumps(publications)
                else:
                    pubs = None
                """
                return render_template('publications.html', publications=json.dumps(publications))

            else:
                return redirect('/login')

    return redirect('/login')


def redirect(location):
    response = make_response('', 303)
    response.headers["Location"] = location
    return response

"""
@app.route('/callback_error')
def callback_error():
    session_id = request.cookies.get('session_id')
    err = request.args.get('error')

    if not session_id:
        return redirect("/login")

    if(r.get("session_id") != None and r.get("session_id").decode('utf-8') == session_id):
        if err:
            return f"<h1>WEB</h1> {err}", 400
        return f"<h1>WEB</h1> Something went wrong", 400

    return redirect("/login")


@app.route('/callback')
def uploaded():
    session_id = request.cookies.get('session_id')
    fid = request.args.get('fid')
    content_type = request.args.get('content_type','text/plain')

    if not session_id:
        return redirect("/login")
    
    if(r.get("session_id") != None and r.get("session_id").decode('utf-8') == session_id):
        if not fid:
            return f"<h1>WEB</h1> Upload successfull, but no fid returned", 500
    
        return f"<h1>WEB</h1> User {session_id} uploaded {fid} ({content_type})", 200
    
    return redirect("/login")


@app.route('/logout')
def logout():
    response = redirect("/login")
    session_id = request.cookies.get('session_id')
    response.set_cookie("session_id", "INVALIDATE", max_age=-1)
    r.delete("session_id")
    return response


def redirect(location):
    response = make_response('', 303)
    response.headers["Location"] = location
    return response


def create_download_token():
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TIME)
    return encode({"iss":"web.company.com", "exp":exp, "action":"download"}, JWT_SECRET, "HS256")


def create_upload_token():
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TIME)
    return encode({"iss":"web.company.com", "exp":exp, "action":"upload"}, JWT_SECRET, "HS256")


def create_get_files_token():
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TIME)
    return encode({"iss":"web.company.com", "exp":exp, "action":"get_files"}, JWT_SECRET, "HS256")
"""