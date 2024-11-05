from dash import callback, dash
from dash.dependencies import Input, Output

from workflows_dashboard.config import DATE_RANGE_PICKER


@callback(
    Output(DATE_RANGE_PICKER, "start_date"),
    Output(DATE_RANGE_PICKER, "end_date"),
    Input("reset-dates-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dates(n_clicks):
    if n_clicks:
        return None, None
    return dash.no_update, dash.no_update
