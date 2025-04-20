from dash import Input, Output, State, callback, html

from road_dashboards.workflows_dashboard.common.analytics import analytics_manager
from road_dashboards.workflows_dashboard.common.consts import ComponentIds


@callback(
    Output(ComponentIds.DATE_RANGE_PICKER, "start_date"),
    Output(ComponentIds.DATE_RANGE_PICKER, "end_date"),
    Input("reset-dates-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_date_range(_):
    return None, None


@callback(
    Output(ComponentIds.REFRESH_DB_BUTTON, "children"),
    Output(ComponentIds.REFRESH_DB_BUTTON, "disabled"),
    Output("refresh-trigger-store", "data"),
    Input(ComponentIds.REFRESH_DB_BUTTON, "n_clicks"),
    State("refresh-trigger-store", "data"),
    prevent_initial_call=True,
)
def refresh_database(_, current_trigger_value):
    analytics_manager.refresh_data()
    new_trigger_value = current_trigger_value + 1
    return [html.I(className="fas fa-sync-alt me-2"), "Refresh Data"], False, new_trigger_value
