from abc import ABC, abstractmethod
from typing import Union

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from road_dashboards.workflows_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


class Chart(ABC):
    def __init__(self, chart_id: str):
        self.chart_id = chart_id
        self.register_callbacks()

    @abstractmethod
    def create_chart(
        self,
        data: pd.DataFrame,
    ) -> go.Figure:
        """
        Create a chart based on the provided data.

        Args:
            data:  data for the chart

        Returns:
            A plotly figure object
        """
        pass

    def create_empty_chart(self) -> go.Figure:
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
            data = self.get_chart_data(
                brain_types=brain_types,
                start_date=start_date,
                end_date=end_date,
                selected_workflow=selected_workflow,
            )

            if data.empty:
                return self.create_empty_chart()

            return self.create_chart(data=data)

    @abstractmethod
    def get_chart_data(
        self,
        brain_types: list[str],
        start_date: str | None,
        end_date: str | None,
        selected_workflow: str,
    ) -> pd.DataFrame:
        """Get the data needed for the chart."""
        pass
