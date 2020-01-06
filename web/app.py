from flask import Flask
from flask import request
from flask import make_response, send_file
from flask import render_template
from flask import jsonify, session
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

redis_auth = redis.Redis(host='redis_auth', port=6381, charset='ISO-8859-1', decode_responses=True)
SESSION_TIME = int(getenv("SESSION_TIME"))

app = Flask(__name__)


@app.route('/')
def index():
    session_id = request.cookies.get('session_id')
    response = redirect('/login')
    
    if session_id:
        username = redis_auth.hget("session_id-login", session_id)
        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                response = redirect("/welcome")
            else:
                response = redirect('/login')
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                clear_redis(username)
                return response

    return redirect('/login')


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
        redis_auth.hset("session_id-login", session_id, username)
        redis_auth.set("session_id_" + username, session_id, ex=SESSION_TIME)
        redis_auth.hset('links_' + username, 'create_or_get_publications', res.json()['_links']['publications']['href'])
        response.set_cookie("session_id", session_id, max_age=SESSION_TIME)
        response.headers["Location"] = "/welcome"
        redis_auth.set('token_' + username, res.json()['token'])
        print(res.json()['token'])
        return response
    else:
        response = redirect('/login')
        response.set_cookie("session_id", "INVALIDATE", max_age=1)
        return response

    return redirect('/login')


@app.route('/add_publication_form')
def add_publication_form():
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)
        
        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                return render_template('add_publication.html')
            else:
                response = redirect('/login')
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                clear_redis(username)
                return response

    return redirect('/login')


@app.route('/update_publication_form/<pid>')
def update_publication_form(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):

                pub_url_json = redis_auth.hget('links_' + username, 'get_update_or_delete_pubs')

                pub_url_json = json.loads(pub_url_json)

                if not pub_url_json.get(pid):
                    return redirect("/error?error=Publication+does+not+exist&status=404")

                res_publication = requests.get(pub_url_json[pid], headers={'Authorization': redis_auth.get('token_' + username)})

                if res_publication.status_code == 200:
                    pub = json.loads(res_publication.json()['publication'])

                    return render_template('update_publication.html', PID=pid, title_value=pub['title'], authors_value=pub['authors'], year_value=pub['year'], publisher_value=pub['publisher'])
                else:
                    error = res_publication.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_publication.status_code}')

            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/add_user_publication', methods=['POST'])
def add_user_publication():
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                title = request.form.get('title')
                authors = request.form.get('authors')
                year = request.form.get('year')
                publisher = request.form.get('publisher')

                url = redis_auth.hget('links_' + username, 'create_or_get_publications')

                res_create_pub = requests.post(url, json={'title' : title, 'authors' : authors, 'year': year, 'publisher': publisher}, headers={'Authorization': redis_auth.get('token_' + username)})

                if res_create_pub.status_code == 201:
                    publications = res_create_pub.json()

                    get_update_or_delete_pub_dict = {}
                    upload_or_get_pub_files = {}
                    
                    for pub in publications['_links']:
                        if pub != 'self':
                            for data in publications['_links'][pub]:
                                if data.get('name'):
                                    if data['name'] == 'get_update_or_delete_pub':
                                        get_update_or_delete_pub_dict[pub] = data['href']
                                    elif data['name'] == 'upload_or_get_files':
                                        upload_or_get_pub_files[pub] = data['href']

                    redis_auth.hset('links_' + username, 'get_update_or_delete_pubs', json.dumps(get_update_or_delete_pub_dict))
                    redis_auth.hset('links_' + username, 'upload_or_get_pub_files', json.dumps(upload_or_get_pub_files))

                    return redirect('/user_publications')
                
                else:
                    error = res_create_pub.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_create_pub.status_code}')

            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/welcome')
def welcome():
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                return render_template('welcome.html', username=username)
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications/<pid>')
def get_user_publication(pid):    
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                
                pub_url_json = redis_auth.hget('links_' + username, 'get_update_or_delete_pubs')
                pub_url_json = json.loads(pub_url_json)

                files_pub_url_json = redis_auth.hget('links_' + username, 'upload_or_get_pub_files')
                files_pub_url_json = json.loads(files_pub_url_json)

                if not pub_url_json.get(pid):
                    return redirect("/error?error=Publication+does+not+exist&status=404")

                res_publication = requests.get(pub_url_json[pid], headers={'Authorization': redis_auth.get('token_' + username)})
                res_pub_files = requests.get(files_pub_url_json[pid], headers={'Authorization': redis_auth.get('token_' + username)})
                
                if res_publication.status_code == 200 and res_pub_files.status_code == 200:
                    publication = json.loads(res_publication.json()['publication'])
                    files = json.loads(res_pub_files.json()['files'])
                    file_links = res_pub_files.json()['_links']

                    download_or_delete_file_dict = {}

                    for link in file_links:
                        if link != 'self':
                            if file_links[link].get('name'):
                                if file_links[link]['name'] == 'download_or_delete_file':
                                    download_or_delete_file_dict[link] = file_links[link]['href']

                    redis_auth.hset('links_' + username, 'download_or_delete_pub_file', json.dumps(download_or_delete_file_dict))

                    return render_template('publication.html', PID=pid, publication=json.dumps(publication), files_list=json.dumps(files))
                
                elif res_publication.status_code != 200:
                    error = res_publication.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_publication.status_code}')

                elif res_pub_files.status_code != 200:
                    error = res_pub_files.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_pub_files.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications/<pid>/update', methods=['POST'])
def update_publication(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                title = request.form.get('title')
                authors = request.form.get('authors')
                year = request.form.get('year')
                publisher = request.form.get('publisher')

                pub_url_json = redis_auth.hget('links_' + username, 'get_update_or_delete_pubs')

                pub_url_json = json.loads(pub_url_json)

                if not pub_url_json.get(pid):
                    return redirect("/error?error=Publication+does+not+exist&status=404")

                res = requests.put(pub_url_json[pid], json={'title' : title, 'authors' : authors, 'year': year, 'publisher': publisher}, headers={'Authorization': redis_auth.get('token_' + username)})
                
                if res.status_code == 200:
                    return redirect('/user_publications')
                else:
                    error = res.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications/<pid>/upload_file', methods=['POST'])
def upload_file(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                f = request.files.get('file')
                file_to_send = {'file': (f.filename, f.read(), f.content_type)}
                if f.filename == '':
                    return redirect(f'/user_publications/{pid}')
        
                pub_url_json = redis_auth.hget('links_' + username, 'upload_or_get_pub_files')
                pub_url_json = json.loads(pub_url_json)

                if not pub_url_json.get(pid):
                    return redirect("/error?error=Publication+does+not+exist&status=404")

                res_upload_file = requests.post(pub_url_json[pid], files=file_to_send, headers={'Authorization': redis_auth.get('token_' + username)})

                if res_upload_file.status_code == 201:
                    file_links = res_upload_file.json()['_links']
            
                    download_or_delete_file_dict = {}

                    for link in file_links:
                        if link != 'self':
                            if file_links[link].get('name'):
                                if file_links[link]['name'] == 'download_or_delete_file':
                                    download_or_delete_file_dict[link] = file_links[link]['href']

                    redis_auth.hset('links_' + username, 'download_or_delete_pub_file', json.dumps(download_or_delete_file_dict))
                
                    return redirect(f'/user_publications/{pid}')
                else:
                    error = res_upload_file.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_upload_file.status_code}')

            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications/<pid>/files/<fid>')
def download_file(pid, fid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):

                file_url_json = redis_auth.hget('links_' + username, 'download_or_delete_pub_file')
                file_url_json = json.loads(file_url_json)

                
                if not file_url_json.get(fid):
                    return redirect("/error?error=File+does+not+exist&status=404")

                res = requests.get(file_url_json[fid], headers={'Authorization': redis_auth.get('token_' + username)})
                
                if res.status_code == 200:
                    value, params = cgi.parse_header(res.headers['Content-Disposition'])
                    return send_file(io.BytesIO(res.content), mimetype=res.headers['Content-Type'], attachment_filename=params['filename'], as_attachment=True)
                else:
                    error = res.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')

    
@app.route('/user_publications/<pid>/delete')
def delete_publication(pid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
                
                pub_url_json = redis_auth.hget('links_' + username, 'get_update_or_delete_pubs')

                pub_url_json = json.loads(pub_url_json)

                if not pub_url_json.get(pid):
                    return redirect("/error?error=Publication+does+not+exist&status=404")

                res_delete_publication = requests.delete(pub_url_json[pid], headers={'Authorization': redis_auth.get('token_' + username)})

                if res_delete_publication.status_code == 200:
                    return redirect('/user_publications')
                else:
                    error = res_delete_publication.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res_delete_publication.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications/<pid>/files/<fid>/delete')
def delete_file(pid, fid):
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):

                file_url_json = redis_auth.hget('links_' + username, 'download_or_delete_pub_file')
                file_url_json = json.loads(file_url_json)

                if not file_url_json.get(fid):
                    return redirect("/error?error=File+does+not+exist&status=404")

                res = requests.delete(file_url_json[fid], headers={'Authorization': redis_auth.get('token_' + username)})
                
                if res.status_code == 200:
                    return redirect(f'/user_publications/{pid}')
                else:
                    error = res.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/user_publications')
def user_publications():
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)

        if username:
            if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):

                url = redis_auth.hget('links_' + username, 'create_or_get_publications')
                res = requests.get(url, headers={'Authorization': redis_auth.get('token_' + username)})
                
                if res.status_code == 200:
                    publications = res.json()

                    get_update_or_delete_pub_dict = {}
                    upload_or_get_pub_files = {}
                    
                    for pub in publications['_links']:
                        if pub != 'self':
                            for data in publications['_links'][pub]:
                                if data.get('name'):
                                    if data['name'] == 'get_update_or_delete_pub':
                                        get_update_or_delete_pub_dict[pub] = data['href']
                                    elif data['name'] == 'upload_or_get_files':
                                        upload_or_get_pub_files[pub] = data['href']

                    redis_auth.hset('links_' + username, 'get_update_or_delete_pubs', json.dumps(get_update_or_delete_pub_dict))
                    redis_auth.hset('links_' + username, 'upload_or_get_pub_files', json.dumps(upload_or_get_pub_files))
                                
                    return render_template('publications.html', publications=publications['pubs'])

                else:
                    error = res.json()['message'].replace(" ", "+")
                    return redirect(f'/error?error={error}&status={res.status_code}')
            else:
                response = redirect('/login')
                clear_redis(username)
                response.set_cookie("session_id", "INVALIDATE", max_age=1)
                return response

    return redirect('/login')


@app.route('/error')
def error():
    session_id = request.cookies.get('session_id')

    if not session_id:
        return redirect("/login")

    username = redis_auth.hget("session_id-login", session_id)

    if username:
        err = request.args.get('error')
        status = request.args.get('status')

        if(redis_auth.get("session_id_" + username) != None and redis_auth.get("session_id_" + username) == session_id):
            if err:
                return f"{err}", status
            return f"<h1>WEB</h1> Something went wrong", status

        else:
            response = redirect('/login')
            redis_auth.hdel("session_id-login", username)
            redis_auth.delete("links_" + username)
            response.set_cookie("session_id", "INVALIDATE", max_age=1)
            return response
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')

    if session_id:
        username = redis_auth.hget("session_id-login", session_id)
        if username:
            redis_auth.hdel("session_id-login", username)
            redis_auth.delete("links_" + username)
            redis_auth.delete("token_" + username)

        response = redirect("/login")
        response.set_cookie("session_id", "LOGGED_OUT", max_age=1)
        return response
    return redirect("/login")


def clear_redis(username):
    redis_auth.hdel("session_id-login", username)
    redis_auth.delete("token_" + username)
    redis_auth.delete("links_" + username)


def redirect(location):
    response = make_response('', 303)
    response.headers["Location"] = location
    return response