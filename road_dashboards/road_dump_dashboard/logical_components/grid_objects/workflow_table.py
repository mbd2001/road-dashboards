import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html, no_update

from road_dashboards.road_dump_dashboard.graphical_components.pie_chart import basic_pie_chart
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import dump_db_manager
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject


class WorkflowTable(GridObject):
    def __init__(
        self,
        datasets_dropdown_id: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.datasets_dropdown_id = datasets_dropdown_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.status_table_id = self._generate_id("status_table")
        self.state_pie_id = self._generate_id("state_pie")

    def layout(self):
        shown_columns = ["exit_code", "count", "example_clip_name", "error_msg"]
        workflow_details_table = dash_table.DataTable(
            id=self.status_table_id,
            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in shown_columns],
            data=[],
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            sort_by=[{"column_id": "count", "direction": "desc"}],
            page_action="native",
            page_current=0,
            page_size=20,
            css=[{"selector": ".show-hide", "rule": "display: none"}],
            style_cell={
                "textAlign": "left",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "paddingLeft": "10px",
                "maxWidth": 0,
            },
            style_header={
                "background-color": "#4e4e50",
                "fontWeight": "bold",
                "color": "white",
            },
            style_data={
                "backgroundColor": "white",
                "color": "rgb(102, 102, 102)",
            },
            style_data_conditional=[
                {"if": {"column_id": "exit_code"}, "width": "7%"},
                {"if": {"column_id": "count"}, "width": "7%"},
                {"if": {"column_id": "example_clip_name"}, "width": "32%"},
            ],
            style_table={
                "border": "1px solid rgb(230, 230, 230)",
            },
        )
        pie_graph = dcc.Graph(
            id=self.state_pie_id,
            config={"displayModeBar": False},
        )
        final_layout = html.Div(
            [
                card_wrapper([html.H2("Exit Codes"), loading_wrapper(workflow_details_table)]),
                card_wrapper(loading_wrapper(pie_graph)),
            ]
        )
        return final_layout

    def _callbacks(self):
        @callback(
            Output(self.status_table_id, "data"),
            Output(self.status_table_id, "tooltip_data"),
            Input(self.datasets_dropdown_id, "value"),
        )
        def update_workflow_table(chosen_dataset):
            if not chosen_dataset:
                return no_update, no_update

            workflow_dict = self.get_workflow_dict(chosen_dataset)

            tooltip_columns = ["example_clip_name", "error_msg"]
            tooltip_data = [{col: exit_code[col] for col in tooltip_columns} for exit_code in workflow_dict.values()]
            return list(workflow_dict.values()), tooltip_data

        @callback(Output(self.state_pie_id, "figure"), Input(self.datasets_dropdown_id, "value"))
        def update_workflow_pie_chart(chosen_dataset):
            if not chosen_dataset:
                return no_update

            workflow_dict = self.get_workflow_dict(chosen_dataset)
            if not workflow_dict:
                return {}

            workflow_df = pd.DataFrame(list(workflow_dict.values()))
            fig = basic_pie_chart(workflow_df, "exit_code", "count", title="Exit Codes Distribution", hover="error_msg")
            return fig

    @staticmethod
    def get_workflow_dict(chosen_dataset: str) -> dict[str, any]:
        workflow_dict = dump_db_manager.get_item(chosen_dataset).get("common_exit_codes", {})
        workflow_dict.pop("0", None)
        return workflow_dict
