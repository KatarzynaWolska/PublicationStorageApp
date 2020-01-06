from flask import Flask, request, Response, jsonify, send_file, make_response
from flask_hal import HAL, document, link, HALResponse
import io
from uuid import uuid4
import redis
import datetime
import json
from os import getenv
from jwt import encode, decode, InvalidTokenError
from dotenv import load_dotenv
load_dotenv(verbose=True)

redis_users = redis.Redis(host='redis_users', port=6379, charset='ISO-8859-1', decode_responses=True)
redis_files = redis.Redis(host='redis_files', port=6380, charset='ISO-8859-1', decode_responses=True)
TOKEN_TIME = int(getenv("TOKEN_TIME"))
JWT_SECRET = getenv("JWT_SECRET")

app = Flask(__name__)
HAL(app)

@app.route('/login_user', methods=['POST'])
def login_user():
  if('username' in request.json and 'password' in request.json):
    return auth(request.json['username'], request.json['password'])
  else:
    return HALResponse(response=document.Document(data={'message': 'Error - please try again'}).to_json(), status=404, mimetype="application/hal+json") 


@app.route('/publications/<pid>/files', methods=['POST', 'GET'])
def post_or_get_publication_files(pid):
  token = request.headers.get('Authorization') or request.args('token')
  if token != None and valid(token):                         
      payload = decode(token, JWT_SECRET)
      status = 200

      if request.method == 'POST':
        f = request.files.get('file')

        if f is None or f.filename == '':
          return HALResponse(response=document.Document(data={'message': 'Error - no file provided'}).to_json(), status=400, mimetype="application/hal+json")

        fid, content_type = str(uuid4()), f.content_type
        redis_files.hset(pid, fid, f.filename)
        redis_files.hset("files", fid, f.read())
        redis_files.hset("content_types", fid, content_type)
        f.close()

        data = {'message': 'File uploaded'}
        status = 201

      elif request.method == 'GET':
        files = redis_files.hgetall(pid)

        if files != None:
          data = {'files': json.dumps(files)}
        else:
          data = {'files': json.dumps([])}
  
      files = redis_files.hgetall(pid)
      
      api_links=link.Collection()

      for pub_file in files:
        l = link.Link(pub_file, 'http://api:5000/publications/' + pid + '/files/' + pub_file)
        l.name = "download_or_delete_file"
        api_links.append(l)

      return HALResponse(response=document.Document(data=data
                                  ,links=api_links).to_json(), status=status, mimetype="application/hal+json")

  else:
      return HALResponse(response=document.Document(data={'message': 'Invalid token - please try again'}).to_json(), status=401, mimetype="application/hal+json")


@app.route('/publications/<pid>/files/<fid>', methods=['GET', 'DELETE'])
def download_or_delete_publication_file(pid, fid):
  token = request.headers.get('Authorization')
  if token != None and valid(token):                         
      payload = decode(token, JWT_SECRET)

      if request.method == 'GET':
        file_name = redis_files.hget(pid, fid)
        file_to_download = redis_files.hget("files", fid)
        file_content_type = redis_files.hget("content_types", fid)

        if file_name is None or file_to_download is None or file_content_type is None:
          return HALResponse(response=document.Document(data={'message': 'File does not exist'}).to_json(), status=404, mimetype="application/hal+json")

        return send_file(io.BytesIO(file_to_download.encode('ISO-8859-1')), mimetype=file_content_type, attachment_filename=file_name, as_attachment=True)
      
      elif request.method == 'DELETE':
        redis_files.hdel("files", fid)
        redis_files.hdel("content_types", fid)
        redis_files.hdel(pid, fid)

        return HALResponse(response=document.Document(data={'message': 'File deleted'}).to_json(), status=200, mimetype="application/hal+json")
  else:
      return HALResponse(response=document.Document(data={'message': 'Invalid token - please try again'}).to_json(), status=401, mimetype="application/hal+json")


@app.route('/publications/<pid>', methods=['GET', 'DELETE', 'PUT'])
def get_update_or_delete_publication(pid):
  token = request.headers.get('Authorization')
  if token != None and valid(token):                         
      payload = decode(token, JWT_SECRET)
      
      pubs = redis_files.hget('publications', payload['username'])

      if pubs != None:
        pubs_json_array = json.loads(pubs)

        user_pub = None
        for pub_json in pubs_json_array:
          if pub_json['pub_id'] == pid:
            user_pub = pub_json
            break

      if pubs == None or user_pub == None:
        return HALResponse(response=document.Document(data={'message': 'Error - please try again'}).to_json(), status=404, mimetype="application/hal+json")

      if request.method == 'GET':
        return HALResponse(response=document.Document(data={'publication': json.dumps(user_pub)}).to_json(), status=200, mimetype="application/hal+json")

      elif request.method == 'DELETE':
        pubs_json_array.remove(user_pub)
        redis_files.hset('publications', payload['username'], json.dumps(pubs_json_array))

        fids = redis_files.hgetall(pid)

        for fid in fids:
          redis_files.hdel("files", fid)
          redis_files.hdel("content_types", fid)
        
        redis_files.delete(pid)

        return HALResponse(response=document.Document(data={'message': 'Publication deleted'}).to_json(), status=200, mimetype="application/hal+json")

      elif request.method == 'PUT':
        if not ("title" in request.json and "authors" in request.json and "year" in request.json and "publisher" in request.json):
            return HALResponse(response=document.Document(data={'message': 'Error - not all information provided'}).to_json(), status=400, mimetype="application/hal+json")

        pubs_json_array.remove(user_pub)

        pub_id = user_pub['pub_id']
        title = request.json['title']
        authors = request.json['authors']
        year = request.json['year']
        publisher = request.json['publisher']

        new_pub_json = json.dumps({"pub_id" : pub_id, "title": title, "authors": authors, "year": year, "publisher": publisher})
        pubs_json_array.append(json.loads(new_pub_json))

        redis_files.hset('publications', payload['username'], json.dumps(pubs_json_array))
        return HALResponse(response=document.Document(data={'message': 'Publication updated'}).to_json(), status=200, mimetype="application/hal+json")

  else:
    return HALResponse(response=document.Document(data={'message': 'Invalid token - please try again'}).to_json(), status=401, mimetype="application/hal+json")


@app.route('/publications', methods=['GET', 'POST'])
def publications():
  token = request.headers.get('Authorization')
  if token != None and valid(token):
    payload = decode(token, JWT_SECRET)
    pubs = redis_files.hget('publications', payload['username'])

    data = {}
    status = 200

    if request.method == 'GET':
      if(pubs != None):
        data = {'pubs': json.dumps(json.loads(pubs))}
      else:
        data = {'pubs': json.dumps([])}

    elif request.method == 'POST':
      if not ("title" in request.json and "authors" in request.json and "year" in request.json and "publisher" in request.json):
            return HALResponse(response=document.Document(data={'message': 'Error - not all information provided'}).to_json(), status=400, mimetype="application/hal+json")

      pub_id = str(uuid4())
      title = request.json['title']
      authors = request.json['authors']
      year = request.json['year']
      publisher = request.json['publisher']

      new_pub_json = json.dumps({"pub_id" : pub_id, "title": title, "authors": authors, "year": year, "publisher": publisher})
      pubs_json_array = []

      if pubs != None:
        pubs_json_array = json.loads(pubs)
        pubs_json_array.append(json.loads(new_pub_json))
      else:
        pubs_json_array.append(json.loads(new_pub_json))

      redis_files.hset('publications', payload['username'], json.dumps(pubs_json_array))

      pubs = redis_files.hget('publications', payload['username'])
            
      data = {'message': 'Publication added'}
      status = 201

    api_links=link.Collection()

    if pubs:
      for pub in json.loads(pubs):
          l = link.Link(pub['pub_id'], 'http://api:5000/publications/' + pub['pub_id'])
          l.name = "get_update_or_delete_pub"
          api_links.append(l)
          l = link.Link(pub['pub_id'], 'http://api:5000/publications/' + pub['pub_id'] + '/files')
          l.name = "upload_or_get_files"
          api_links.append(l)

    return HALResponse(response=document.Document(data=data
                                ,links=api_links).to_json(), status=status, mimetype="application/hal+json")

  else:
      return HALResponse(response=document.Document(data={'message': 'Invalid token - please try again'}).to_json(), status=401, mimetype="application/hal+json")


def auth(username, password):
  if(redis_users.get(username) != None and redis_users.get(username) == password):
    return HALResponse(response=document.Document(data={'message': 'OK', 'token': create_token(username, password).decode('utf-8')}
                            ,links=link.Collection(link.Link('publications', 'http://api:5000/publications'))).to_json(), status=200, mimetype="application/hal+json")
  
  else:
    return HALResponse(response=document.Document(data={'message': 'Login failed - wrong credentials'}).to_json(), status=401, mimetype="application/hal+json")

def create_token(username, password):
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TIME)
    return encode({"username":username, "password":password, "exp":exp}, JWT_SECRET, "HS256")


def valid(token):
  try:
    decoded = decode(token.encode('utf-8'), JWT_SECRET)
    user_pass = redis_users.get(decoded['username'])
    if user_pass != None and user_pass == decoded['password']:
      return True
    else:
      return False
  except InvalidTokenError as e:
    print(e)
    return False
  return True
