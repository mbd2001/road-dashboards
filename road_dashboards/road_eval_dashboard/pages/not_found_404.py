from dash import html, register_page

register_page(__name__, name="Not Found 404")

layout = html.Div(
    [
        html.H1("404: Not found", className="text-danger"),
        html.Hr(),
        html.P(f"The url was not recognised"),
    ],
    className="p-3 bg-light rounded-3",
)
