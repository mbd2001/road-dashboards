import os
import sys

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html

debug = False if os.environ.get("DEBUG") == "false" else True
if not debug:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    [dcc.Location(id="url"), dbc.Container(dash.page_container, fluid=True, className="px-4 vh-100")],
    className="wrapper h-100",
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6009", debug=debug, use_reloader=debug)
