import dash_bootstrap_components as dbc
from dash import html

from road_dashboards.workflows_dashboard.components.charts.error_pie import ErrorPieChart
from road_dashboards.workflows_dashboard.components.charts.status_pie import StatusPieChart
from road_dashboards.workflows_dashboard.components.charts.weekly_success import WeeklySuccessChart
from road_dashboards.workflows_dashboard.components.charts.workflow_success_count import WorkflowSuccessCountChart
from road_dashboards.workflows_dashboard.components.selectors.workflow_selector import create_workflow_selector
from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS


def create_charts_container():
    return html.Div(
        [
            dbc.Row([WeeklySuccessChart().render()], className="g-4 mb-4"),
            dbc.Row([WorkflowSuccessCountChart().render()], className="g-4 mb-4"),
            create_workflow_selector(),
            *[create_workflow_charts(workflow) for workflow in WORKFLOWS],
        ]
    )


def create_workflow_charts(workflow):
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col([StatusPieChart(workflow).render()], lg=6, xs=12, className="d-flex align-items-stretch"),
                    dbc.Col([ErrorPieChart(workflow).render()], lg=6, xs=12, className="d-flex align-items-stretch"),
                ],
                className="g-4",
            )
        ],
        id=f"content-{workflow}",
    )
