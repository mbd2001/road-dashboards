import pandas as pd
from dash import Input, Output, callback, dash_table

from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import card_wrapper
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
        pass

    def layout(self):
        shown_columns = ["exit_code", "count", "example_clip_name"]
        workflow_details_table = dash_table.DataTable(
            id=self.component_id,
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
            style_cell={"textAlign": "left"},
            style_header={
                "background-color": "#4e4e50",
                "fontWeight": "bold",
                "color": "white",
            },
            style_data={
                "backgroundColor": "white",
                "color": "rgb(102, 102, 102)",
            },
            style_table={
                "border": "1px solid rgb(230, 230, 230)",
            },
        )
        return card_wrapper(workflow_details_table)

    def _callbacks(self):
        @callback(Output(self.component_id, "data"), Input(self.datasets_dropdown_id, "value"))
        def update_workflow_data(chosen_dump):
            workflow_dict = dump_db_manager.get_item(chosen_dump).get("common_exit_codes", None)
            workflow_dict.pop("0", None)
            if not workflow_dict:
                return pd.DataFrame()

            return list(workflow_dict.values())
