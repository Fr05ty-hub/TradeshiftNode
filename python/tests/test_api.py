import pytest
import redis
import requests
import json
import time

url_base = "http://localhost:5000/app/api/v1.0/nodes"
http_url = "localhost"
http_port = 5000
auth = ('test', 'test')


# THIS TEST IS JUST TO RESET THE BASIC DB I'M USING. SHOULD NOT BE USED
def test_deletion():
    r_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    results = False

    try:
        results = r_cli.delete("root", "root:children", "a", "a:children", 'O G', 'O G:children', 'Liquid', 'Liquid:children')
    except:
        print("Could not delete old")

    return 0


def add_node(data):
    url = url_base+'/add'
    data = json.dumps(data)
    session = requests.Session()
    session.trust_env = False
    request = session.put(url=url, json=data, auth=auth, verify=False)
    result = request.status_code

    return result


def get_children(node):
    session = requests.Session()
    session.trust_env = False
    url = url_base+'/children/'+node

    request = session.get(url=url, verify=False)

    return request


def get_offspring(node, levels=False):
    session = requests.Session()
    session.trust_env = False
    url = url_base+'/offspring/'+node+'/'
    if levels:
        url = url+levels

    request = session.get(url=url, verify=False)

    return request


def change_parent_no_auth(data):
    session = requests.Session()
    session.trust_env = False
    url = url_base+'/parent_change'
    data = json.dumps(data)

    request = session.post(url=url, json=data, verify=False)

    return request


def change_parent(data):
    session = requests.Session()
    session.trust_env = False
    url = url_base+'/parent_change'
    data = json.dumps(data)

    request = session.post(url=url, json=data, verify=False, auth=auth)

    return request


def check_node(data):
    result = {}
    try:
        r_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
        result['node'] = r_cli.hgetall(data['id'])
        result['children'] = r_cli.lrange(data['parent']+":children", 0, -1)
    except:
        print("Couldn't connect to DB")

    return result


# INIT TEST: Check connection to ensure Redis db is up
def test_connection():
    r_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    success = False
    retries = 0

    while retries < 5:
        try:
            success = r_cli.ping()
            break
        except:
            retries += 1
            print("Cannot connect to DB.")
            time.sleep(1)

    assert success == True


# TEST SETUP: Load up root as it's the only value not addable later
def test_setup():
    r_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
    root_node = {
        "id": "root",
        "root": "root",
        "parent": "",
        "height": 0
    }

    results = False

    try:
        results = r_cli.hmset("root", root_node)
    except:
        print("Could not setup root")

    assert results == True


### API ADD FUNCTION TESTING ###
# Test add a node
def test_simple_add():
    node_data = {
        "id": "a",
        "root": "root",
        "parent": "root"
    }

    results = add_node(node_data)

    assert results == 200


# Test add a node with missing values
def test_neg_add():
    node_data = {
        "id": "b",
        "parent": "root"
    }

    results = add_node(node_data)

    assert results == 400


# Test add a node with missing parent
def test_mis_par_add():
    node_data = {
        "id": "b",
        "parent": "zai",
        "root": "root"
    }

    results = add_node(node_data)

    assert results == 400


# Test add a node with name Nil (REDIS DOESN'T LIKE IT)
def test_nil_add():
    node_data = {
        "id": "Nil",
        "parent": "root"
    }

    results = add_node(node_data)

    assert results == 400


# Test add a node id with spaces
def test_spac_add():
    node_data = {
        "id": "O G",
        "parent": "a",
        "root": "root"
    }

    results = add_node(node_data)

    assert results == 200


# Test add a node with parent id with spaces
def test_spac_par_add():
    node_data = {
        "id": "Liquid",
        "parent": "O G",
        "root": "root"
    }

    results = add_node(node_data)

    assert results == 200


# Test add an existing node again
def test_mult_add():
    node_data = {
        "id": "O G",
        "parent": "a",
        "root": "root"
    }

    results = add_node(node_data)

    assert results == 400


# Test add a node with non-existing parent
def test_neg_root_add():
    node_data = {
        "id": "O G",
        "parent": "a",
        "root": "EG"
    }

    results = add_node(node_data)

    assert results == 400


# Test simple check get children
def test_simple_get():
    results = get_children('root')
    got_results = json.loads(results.content)
    exp_results = {"1": ["a"]}

    assert got_results == exp_results


# Test check if get children works with spaces
def test_spac_get():
    results = get_children('O G')
    got_results = json.loads(results.content)
    exp_results = {"1": ["Liquid"]}

    assert got_results == exp_results


# Test check invalid name
def test_null_get():
    results = get_children('Nil')

    assert results.status_code == 440


# Test to check empty get commands
def test_empty_get():
    results = get_children('')

    assert results.status_code == 404


# Test to check nodes with no children
def test_no_child_get():
    results = get_children('Liquid')
    got_results = json.loads(results.content)
    exp_results = {"1": []}

    assert got_results == exp_results


# Test that data is getting added
def test_simple_check_data():
    node_data = {
        "id": "a",
        "root": "root",
        "parent": "root"
    }

    db_data = {'node': {
        "id": "a",
        "root": "root",
        "parent": "root",
        "height": '1'
    }, 'children': ['a']}

    data = check_node(node_data)

    assert data == db_data

#Test to check if offspring is limited to levels
def test_offspring_levels():
    results = get_offspring('root', '2')
    got_results = json.loads(results.content)
    exp_results = {"1": ['a'],
                   "2": ['O G']}

    assert got_results == exp_results

# Test to check if unlimited offspring gets brought back
def test_offspring_unlimited():
    results = get_offspring('root', '0')
    got_results = json.loads(results.content)
    exp_results = {"1": ['a'],
                   "2": ['O G'],
                   "3": ['Liquid']}

    assert got_results == exp_results

# Test to check what happens if no level argument is passed
def test_offspring_no_level():
    results = get_offspring('root')

    assert results.status_code == 404


# Test to check if offspring don't exist
def test_no_offspring():
    results = get_offspring('Liquid', '0')
    got_results = json.loads(results.content)
    exp_results = {"1": []}

    assert got_results == exp_results


#Test to check no authorization
def test_change_parent_no_auth():
    change_data = {
        "node": "Liquid",
        "new_parent": "root"
    }
    results = change_parent_no_auth(change_data)

    assert results.status_code == 401


# Basic parents change
def test_change_parent():
    change_data = {
        "node": "Liquid",
        "new_parent": "root"
    }
    results = change_parent(change_data)

    assert results.status_code == 200


# Test to prevent circlejerk changing of parents
def test_circlejerk_parent():
    change_data = {
        "node": "a",
        "new_parent": "O G"
    }
    results = change_parent(change_data)

    assert results.status_code == 400


if __name__ == '__main__':
    test_connection()
    test_deletion()
    test_setup()
    test_simple_add()
    test_simple_check_data()
    test_neg_add()
    test_mis_par_add()
    test_nil_add()
    test_spac_add()
    test_spac_par_add()
    test_mult_add()
    test_neg_root_add()
    test_simple_get()
    test_spac_get()
    test_null_get()
    test_empty_get()
    test_no_child_get()
    test_offspring_levels()
    test_offspring_unlimited()
    test_offspring_no_level()
    test_no_offspring()
    test_change_parent_no_auth()
    test_change_parent()
    test_circlejerk_parent()
    #test_check_data()
    #test_offspring_change()
