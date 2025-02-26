from dash import Input, Output, callback, html

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds
from road_dashboards.workflows_dashboard.database.workflow_manager import db_manager


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
    Input(ComponentIds.REFRESH_DB_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def refresh_database(_):
    db_manager.refresh_data()
    return [html.I(className="fas fa-sync-alt me-2"), "Refresh Data"], False
