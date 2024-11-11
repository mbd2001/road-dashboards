from abc import ABC, abstractmethod

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

from road_dashboards.workflows_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


class BaseChart(ABC):
    def __init__(self, chart_id: str):
        self.chart_id = chart_id
        self.store_id = f"{self.chart_id}-store"
        self.chart_cache = {}
        self.register_callbacks()

    @abstractmethod
    def create_chart(self, data):
        pass

    def create_empty_chart(self) -> px.pie:
        fig = px.pie(values=[], names=[], title="No data to display")
        return fig

    def render(self) -> dbc.Col:
        return dbc.Col(
            [
                dcc.Store(id=self.store_id),
                card_wrapper(
                    [
                        # Only show loading on initial load
                        html.Div(id=f"{self.chart_id}-loading-wrapper"),
                        dcc.Graph(id=self.chart_id),
                    ]
                ),
            ],
            md=12,
        )

    def register_callbacks(self):
        """Register callbacks for the chart."""
        if self.chart_id == ComponentIds.WEEKLY_SUCCESS_RATE_CHART:

            @callback(Output(self.chart_id, "figure"), Input(ComponentIds.WORKFLOW_DATA_STORE, "data"))
            def update_chart(store_data):
                if not store_data:
                    return self.create_empty_chart()
                return self.create_chart(store_data)

        else:

            @callback(
                [Output(self.chart_id, "figure"), Output(f"{self.chart_id}-loading-wrapper", "children")],
                [Input(ComponentIds.WORKFLOW_DATA_STORE, "data"), Input(ComponentIds.WORKFLOW_SELECTOR, "value")],
                [State(self.store_id, "data")],
            )
            def update_chart(store_data, selected_workflow, cached_figure):
                if not store_data or selected_workflow not in store_data:
                    return self.create_empty_chart(), None

                # Check if we have a valid cached figure for this data
                cache_key = (selected_workflow, str(store_data[selected_workflow]))
                if cached_figure and cached_figure.get("cache_key") == str(cache_key):
                    return cached_figure["figure"], None

                # Create new figure if cache miss
                df = pd.DataFrame.from_dict(store_data[selected_workflow])
                figure = self.create_chart(df)

                # Update cache
                return figure, None
