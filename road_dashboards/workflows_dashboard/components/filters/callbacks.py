from dash import Input, Output, callback

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


@callback(
    Output(ComponentIds.DATE_RANGE_PICKER, "start_date"),
    Output(ComponentIds.DATE_RANGE_PICKER, "end_date"),
    Input("reset-dates-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_date_range(_):
    return None, None
