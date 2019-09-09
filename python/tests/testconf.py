import pytest
import redis

# We need to initialize with "root" as it's the only value I can't add through the API calls
@pytest.fixture(scope="session", autouse=True)
def execute_setup():
    r_cli = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    retries = 0
    print("Setting up root")

    while retries < 5:
        try:
            r_cli.ping()
            break
        except:
            retries += 1
            print("Cannot connect to DB.")

    root_node = {
        "id": "root",
        "root": "root",
        "parent": "",
        "height": 0
    }

    try:
        r_cli.hmset("root", root_node)
    except:
        print("Could not setup root")