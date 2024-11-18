from abc import ABC, abstractmethod
from typing import Union

import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from road_dashboards.workflows_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


class BaseChart(ABC):
    def __init__(self, chart_id: str):
        self.chart_id = chart_id
        self.store_id = f"{self.chart_id}-store"
        self.chart_cache = {}
        self.register_callbacks()

    @abstractmethod
    def create_chart(self, filters: dict) -> Union[go.Figure, px.pie]:
        """
        Create a chart based on the provided filters.

        Args:
            filters (dict): Dictionary containing filter parameters:
                - brain_types (list[str]): List of brain types to filter by
                - start_date (str): Start date for filtering in ISO format
                - end_date (str): End date for filtering in ISO format
                - selected_workflow (str): Currently selected workflow

        Returns:
            Union[go.Figure, px.pie]: A plotly figure object
        """
        pass

    def create_empty_chart(self) -> px.pie:
        fig = px.pie(values=[], names=[], title="No data to display")
        return fig

    def render(self) -> dbc.Col:
        return dbc.Col(
            [
                card_wrapper(
                    [
                        html.Div(id=f"{self.chart_id}-loading-wrapper"),
                        dcc.Graph(id=self.chart_id),
                    ]
                ),
            ],
            md=12,
        )

    def register_callbacks(self):
        """Register callbacks for the chart."""

        @callback(
            Output(self.chart_id, "figure"),
            [
                Input(ComponentIds.BRAIN_SELECTOR, "value"),
                Input(ComponentIds.DATE_RANGE_PICKER, "start_date"),
                Input(ComponentIds.DATE_RANGE_PICKER, "end_date"),
                Input(ComponentIds.WORKFLOW_SELECTOR, "value"),
            ],
        )
        def update_chart(brain_types, start_date, end_date, selected_workflow):
            if hasattr(self, "workflow_name") and selected_workflow != self.workflow_name:
                return self.create_empty_chart()

            filters = {
                "brain_types": brain_types,
                "start_date": start_date,
                "end_date": end_date,
                "selected_workflow": selected_workflow,
            }

            return self.create_chart(filters)
