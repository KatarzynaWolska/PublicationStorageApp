from flask import Flask, request, Response, jsonify, send_file, make_response
import io
from uuid import uuid4
import redis
import datetime
import json
from os import getenv
from jwt import encode, decode, InvalidTokenError
from dotenv import load_dotenv
load_dotenv(verbose=True)


redis_users = redis.Redis(host='redis_users', port=6379)
redis_files = redis.Redis(host='redis_files', port=6380, charset='ISO-8859-1', decode_responses=True)
TOKEN_TIME = int(getenv("TOKEN_TIME"))
JWT_SECRET = getenv("JWT_SECRET")

app = Flask(__name__)

@app.route('/login_user', methods=['POST'])
def login_user():
  return auth(request.json['username'], request.json['password'])


@app.route('/publications/<pid>/files', methods=['POST', 'GET'])
def post_publication_file(pid):
  token = request.headers.get('Authorization') or request.args('token')
  if valid(token):                         
      payload = decode(token, JWT_SECRET)

      if request.method == 'POST':
        f = request.files.get('file')

        if f.filename == '':
          return Response("Error - no file provided", status=400) #poprawić to na jsony

        fid, content_type = str(uuid4()), f.content_type
        redis_files.hset(pid, fid, f.filename)
        #redis_files.hset("files_names", fid, f.filename)
        redis_files.hset("files", fid, f.read())
        redis_files.hset("content_types", fid, content_type)
        f.close()
        return Response("File uploaded", status=200)

      elif request.method == 'GET':
        files = redis_files.hgetall(pid)

        if files != None:
          return json.dumps(files)
        else:
          return json.dumps([])
  
  else:
      return Response("Invalid token - please try again", status=400)


@app.route('/publications/<pid>/files/<fid>', methods=['GET', 'DELETE'])
def download_or_delete_publication_file(pid, fid):
  token = request.headers.get('Authorization')
  if valid(token):                         
      payload = decode(token, JWT_SECRET)

      if request.method == 'GET':
        file_name = redis_files.hget(pid, fid)        # może sprawdzać czy istnieje
        file_to_download = redis_files.hget("files", fid)
        file_content_type = redis_files.hget("content_types", fid)

        return send_file(io.BytesIO(file_to_download.encode('ISO-8859-1')), mimetype=file_content_type, attachment_filename=file_name, as_attachment=True)
      
      elif request.method == 'DELETE':
        redis_files.hdel("files", fid)
        redis_files.hdel("content_types", fid)
        redis_files.hdel(pid, fid)

        return Response("File deleted", status=200)
  else:
      return Response("Invalid token - please try again", status=400)


@app.route('/publications/<pid>', methods=['GET', 'DELETE', 'PUT'])
def get_update_or_delete_publication(pid):
  token = request.headers.get('Authorization')
  if valid(token):                         
      payload = decode(token, JWT_SECRET)
      
      pubs = redis_files.hget('publications', payload['id'])

      if pubs != None:
        pubs_json_array = json.loads(pubs)

        user_pub = None
        for pub_json in pubs_json_array:
          if pub_json['pub_id'] == pid:
            user_pub = pub_json
            break

      if pubs == None or user_pub == None:
        return Response("Error - please try again", status=400)

      if request.method == 'GET':
        return json.dumps(user_pub)

      elif request.method == 'DELETE':
        pubs_json_array.remove(user_pub)
        redis_files.hset('publications', payload['id'], json.dumps(pubs_json_array))

        fids = redis_files.hgetall(pid)
        print(fids)

        for fid in fids:
          print(fid)
          redis_files.hdel("files", fid)
          redis_files.hdel("content_types", fid)
        
        redis_files.hdel(pid)

        return Response("Publication deleted", status=200)

      elif request.method == 'PUT':
        pubs_json_array.remove(user_pub)
        pub_id = user_pub['pub_id']
        name = request.json['name']
        authors = request.json['authors']
        year = request.json['year']
        publisher = request.json['publisher']

        new_pub_json = json.dumps({"pub_id" : pub_id, "name": name, "authors": authors, "year": year, "publisher": publisher})
        pubs_json_array = []

        if pubs != None:
          pubs_json_array = json.loads(pubs)
          pubs_json_array.append(json.loads(new_pub_json)) # tu tez było bez loads
        else:
          #pubs_json_array.append(new_pub_json)
          pubs_json_array.append(json.loads(new_pub_json))

      redis_files.hset('publications', payload['id'], json.dumps(pubs_json_array))
      return Response("Publication updated", status=200)

  else:
    return Response("Invalid token - please try again", status=400)


@app.route('/publications', methods=['GET', 'POST'])
def publications():
  token = request.headers.get('Authorization')  # czy token w nagłówku czy w argumentach
  if valid(token):                              # sprawdzac token tak jak w P2
    payload = decode(token, JWT_SECRET)
    pubs = redis_files.hget('publications', payload['id'])

    if request.method == 'GET':
      if(pubs != None):
        return json.dumps(json.loads(pubs))
      else:
        return json.dumps([])

    elif request.method == 'POST':
      pub_id = str(uuid4())
      name = request.json['name']
      authors = request.json['authors']
      year = request.json['year']
      publisher = request.json['publisher']

      new_pub_json = json.dumps({"pub_id" : pub_id, "name": name, "authors": authors, "year": year, "publisher": publisher})
      pubs_json_array = []

      if pubs != None:
        pubs_json_array = json.loads(pubs)
        pubs_json_array.append(json.loads(new_pub_json)) # tu tez było bez loads
      else:
        #pubs_json_array.append(new_pub_json)
        pubs_json_array.append(json.loads(new_pub_json))

    redis_files.hset('publications', payload['id'], json.dumps(pubs_json_array))
    return Response("Publication added", status=200)

  else:
      return Response("Wrong authorization token - please try again", status=400)  # posprawdzać statusy, mimetype application/json usuniete


def auth(username, password):
  if(redis_users.hget(username, 'password') != None and redis_users.hget(username, 'password').decode('utf-8') == password): # zastanowic sie nad metoda laczenia z redisem
    return Response(create_token(username, password, redis_users.hget(username, 'id').decode('utf-8')), status=200, mimetype='application/json') # zmienic na make_response ? usunac message 
  else:
    return Response("Login failed - wrong credentials.", status=400)


def create_token(username, password, id):
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_TIME)
    return encode({"username":username, "password":password, "id": id, "exp":exp}, JWT_SECRET, "HS256")


def valid(token):
  try:
    decoded = decode(token, JWT_SECRET)
    user_pass = redis_users.hget(decoded['username'], 'password')
    if user_pass != None and user_pass.decode('utf-8') == decoded['password']:
      return True
    else:
      return False
  except InvalidTokenError as e:
    app.logger.error(str(e))
    return False
  return True
