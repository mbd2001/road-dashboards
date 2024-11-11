from dash import callback, dash
from dash.dependencies import Input, Output

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


@callback(
    Output(ComponentIds.DATE_RANGE_PICKER, "start_date"),
    Output(ComponentIds.DATE_RANGE_PICKER, "end_date"),
    Input("reset-dates-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dates(n_clicks):
    if n_clicks:
        return None, None
    return dash.no_update, dash.no_update
