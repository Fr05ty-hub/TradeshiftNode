from flask import Flask, jsonify, make_response, request, abort
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash,check_password_hash
import redis

app = Flask(__name__)
auth = HTTPBasicAuth()

# This user dictionary is just a placeholder to enable demos. In a practical application, it would actually query a
# database to validate security credentials
users = {
    "test": generate_password_hash("test"),
    "root": generate_password_hash("admin")
}


@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False


@auth.errorhandler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.errorhandler
def not_found():
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler
def redis_error(error):
    return make_response(jsonify({'error': error}), 442)


@app.errorhandler
def conn_error(error):
    return make_response(jsonify({'error': error}), 441)


@app.errorhandler
def data_error(error):
    return make_response(jsonify({'error': error}), 440)


@app.route('/app/api/v1.0/nodes/children/<node_id>', methods=['GET'])
def get_node_children(node_id):
    r = redis.StrictRedis()
    children = node_offspring(r, node_id, 1)
    return jsonify(children[1])


@app.route('/app/api/v1.0/nodes/offspring/<node_id>/<levels>', methods=['GET'])
def get_node_offspring(node_id, levels):
    r = redis.StrictRedis()
    if r.exists(node_id+":children") == 0:
        raise not_found
    children = node_offspring(r, node_id, levels)
    return jsonify(children)


@app.route('/app/api/v1.0/nodes/parent_change', methods=['PUT'])
@auth.login_required
def change_node_parent():
    if not request.json or 'node' not in request.json or 'new_parent' not in request.json:
        abort(400)
    r = redis.StrictRedis(host='redis', port=6379)
    node_id = request.json['node']
    new_parent = request.json['new_parent']
    val = redis_change_parent(r, node_id, new_parent)

    return jsonify(val)


def node_offspring(redis, node, levels=-1):
    node_dict = {}
    node_dict['0'] = [node]
    child_string = ":children"
    children = redis.lrange(node + child_string, 0, -1)
    node_dict['1'] = children
    level = 2
    while level <= levels or levels == -1:
        if len(node_dict[level-1]):
            break
        node_dict[level] = []
        for x in node_dict[level-1]:
            children = redis.lrange(x+child_string, 0, -1)
            node_dict[level] = node_dict[level] + children
        level = level +1

    return node_dict


def redis_change_parent(redis, node, new_parent):
    old_parent = redis.hget(node, 'parent')
    node_parent = redis.hexists(new_parent, 'parent')
    if old_parent is None or node_parent is None:
        raise data_error("FAIL: Some of the nodes don't exist or aren't properly set up")
    new_par_height = redis.hget(new_parent, 'height')
    old_par_height = redis.hget(old_parent, 'height')
    if new_par_height is None or old_par_height is None:
        raise data_error("FAIL: Some of the nodes are missing internal values")
    height_diff = new_par_height - old_par_height
    offspring = node_offspring(redis, node)
    child_string = ":children"

    pipe = redis.pipeline()
    pipe.hset(node, 'parent', new_parent)
    pipe.lrem(old_parent+child_string, 50, node)
    pipe.lpush(new_parent+child_string, node)

    for level in offspring:
        for nd in offspring[level]:
            pipe.hincrby(nd, 'height', height_diff)

    try:
        response = pipe.execute()
    except pipe.DataError:
        raise data_error("INNER FAILURE WHILE EXECUTING PIPELINE. DATA MIGHT BE COMPROMISED.")
    except pipe.ConnectionError or pipe.ResponseError:
        raise conn_error("CONNECTION ERROR WHEN SENDING COMMANDS")
    except pipe.RedisError:
        raise redis_error("REDIS ERROR")

    return response


if __name__ == '__main__':
    app.run(debug=True)
