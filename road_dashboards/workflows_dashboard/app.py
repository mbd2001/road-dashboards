import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html

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
    app.run_server(debug=True)
