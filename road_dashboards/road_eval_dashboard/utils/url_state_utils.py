import base64
import json

import dash_bootstrap_components as dbc
from dash import html

NETS_STATE_KEY = "nets"
META_DATA_STATE_KEY = "meta_data"


def dict_to_hash(d):
    return "#" + base64.b64encode(json.dumps(d).encode("utf-8")).decode("utf-8")


def hash_to_dict(h):
    return json.loads(base64.b64decode(h)) if h else {}


def add_state(key, state: dict, state_hash=None):
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


def create_dropdown_options_list(labels, values=None, do_hover=False):
    if not values:
        values = labels

    assert len(labels) == len(values), "values are different from labels, both should be of the same size"
    return [
        {"label": label, "value": value, **({"title": str(value)} if do_hover else {})}
        for label, value in zip(labels, values)
    ]


def create_alert_message(msg, color, style=None):
    if style is None:
        style = {"margin-top": 10}

    message_lines = msg.split("\n")

    # Create a list of Dash HTML components, interspersing html.Br() elements for line breaks
    formatted_message = [html.Span(line) for line in message_lines]

    # Insert html.Br() after each line except the last one
    components = []
    for component in formatted_message[:-1]:
        components.extend([component, html.Br()])
    components.append(formatted_message[-1])

    return dbc.Alert(components, color=color, style=style)
