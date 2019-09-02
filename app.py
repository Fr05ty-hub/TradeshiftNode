import time
import json
from flask import Flask, jsonify, make_response, request, abort
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
import redis

app = Flask(__name__)

auth = HTTPBasicAuth()
r_cli = redis.StrictRedis(host='redis', port=6379, decode_responses=True)
# This user dictionary is just a placeholder to enable demos. In a practical application, it would actually query a
# database to validate security credentials
users = {
    "test": generate_password_hash("test"),
    "root": generate_password_hash("admin")
}

# Password verification
@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False


class BadRequest(Exception):
    def __init__(self, message, status=400, payload=None):
        self.message = message
        self.status = status
        self.payload = payload

# Error handler instance
@app.errorhandler(BadRequest)
def handle_bad_request(error):
    payload = dict(error.payload or ())
    payload['status'] = error.status
    payload['message'] = error.message
    return jsonify(payload), error.status

# Function to get children of a given node
@app.route('/app/api/v1.0/nodes/children/<node_id>', methods=['GET'])
def get_node_children(node_id):
    children = node_offspring(node_id, 1)
    if children == -1:
        raise BadRequest("FAIL: Node " + node_id + " not found", 440, {'ext': 1})
    return json.dumps(children)

# Function to get offspring of a given node to X levels of depth
@app.route('/app/api/v1.0/nodes/offspring/<node_id>/<levels>', methods=['GET'])
def get_node_offspring(node_id, levels):
    children = node_offspring(node_id, levels)
    if children == -1:
        raise BadRequest("FAIL: Node " + node_id + " not found", 440, {'ext': 1})
    return json.dumps(children)

# Function to add a new node to the database
@app.route('/app/api/v1.0/nodes/add', methods=['POST'])
@auth.login_required
def add_node():
    if not request.json or 'id' not in request.json or 'parent' not in request.json or 'root' not in request.json:
        raise BadRequest("Missing node parameters to add for db", 400, {'ext': 1})
    parent_data = r_cli.hgetall(request.json['parent'])
    if not parent_data:
        raise BadRequest("Parent node does not exist", 400, {'ext': 1})
    param_str = ''
    request.json['height'] = str(int(parent_data['height'])+1)
    for item in request.json:
        param_str = param_str + request.json[item]
    pipe = r_cli.pipeline()
    pipe.hmset(request.json['id'], request.json)
    pipe.lpush(request.json['parent']+":children", request.json['id'])
    val = pipe.execute()

    return json.dumps(val)

# Function to change the parent of a node
@app.route('/app/api/v1.0/nodes/parent_change', methods=['PUT'])
@auth.login_required
def change_node_parent():
    if not request.json or 'node' not in request.json or 'new_parent' not in request.json:
        raise BadRequest("Missing node parameters or nodes not present in db", 400, {'ext': 1})
    node_id = request.json['node']
    new_parent = request.json['new_parent']
    val = redis_change_parent(node_id, new_parent)

    return json.dumps(val)


# Checks if node exists
def node_check(node):
    exists = r_cli.exists(node)
    if exists != 0:
        return True
    return False


# Function finds offspring of a node to X degrees of depth
def node_offspring(node, levels=0):
    node_dict = {}
    if not node_check(node):
        return -1
    child_string = ":children"
    level = 1
    children = r_cli.lrange(node+child_string, 0, -1)
    node_dict[level] = children

    while int(level) < int(levels) or int(levels) == 0:
        if level not in node_dict.keys():
            break
        level = level + 1
        new_spawn = []
        for x in node_dict[level-1]:
            children = r_cli.lrange(x+child_string, 0, -1)
            new_spawn = new_spawn + children
        if len(new_spawn) != 0:
            node_dict[level] = new_spawn

    return node_dict


# Queues all the commands for Redis to execute atomically in a queue
def redis_change_parent(node, new_parent):
    old_parent = r_cli.hget(node, 'parent')
    node_parent = r_cli.hexists(new_parent, 'parent')
    if old_parent is None or node_parent is None:
        raise BadRequest("FAIL: Some of the nodes don't exist or aren't properly set up", 440, {'ext': 1})
    new_par_height = r_cli.hget(new_parent, 'height')
    old_par_height = r_cli.hget(old_parent, 'height')
    if new_par_height is None or old_par_height is None:
        raise BadRequest("FAIL: Some of the nodes are missing internal values", 440, {'ext': 1})
    height_diff = int(new_par_height) - int(old_par_height)
    offspring = node_offspring(node)
    child_string = ":children"

    pipe = r_cli.pipeline()
    pipe.hset(node, 'parent', new_parent)
    pipe.lrem(old_parent+child_string, 50, node)
    pipe.lpush(new_parent+child_string, node)

    pipe.hincrby(node, 'height', height_diff)
    for level in offspring:
        for nd in offspring[level]:
            pipe.hincrby(nd, 'height', height_diff)

    try:
        response = pipe.execute()
    except pipe.DataError:
        raise BadRequest("INNER FAILURE WHILE EXECUTING PIPELINE. DATA MIGHT BE COMPROMISED.", 440, {'ext': 1})
    except pipe.ConnectionError or pipe.ResponseError:
        raise BadRequest("CONNECTION ERROR WHEN SENDING COMMANDS", 441, {'ext': 1})
    except pipe.RedisError:
        raise BadRequest("REDIS ERROR", 4050, {'ext': 1})

    return response


if __name__ == '__main__':
    app.run(debug=True)
