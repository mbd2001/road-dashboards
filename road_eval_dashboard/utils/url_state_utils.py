import base64
import json

NETS_STATE_KEY = "nets"
META_DATA_STATE_KEY = "meta_data"

def dict_to_hash(d):
    return "#" + base64.b64encode(
        json.dumps(d)
        .encode("utf-8")
    ).decode("utf-8")


def hash_to_dict(h):
    return json.loads(base64.b64decode(h)) if h else {}

def add_state(key, state : dict, state_hash=None):
    url_state = hash_to_dict(state_hash) if state_hash else {}
    url_state[key] = state
    return dict_to_hash(url_state)

def get_state(state_hash, key=None):
    if not state_hash:
        return
    state = hash_to_dict(state_hash)
    if key:
        return state.get(key)
    return state
