from datetime import datetime
from functools import reduce

import pandas as pd
from dash import Input, Output, State, callback, dcc

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds, WorkflowFields


@callback(
    Output(ComponentIds.DOWNLOAD_DATAFRAME, "data"),
    Input(ComponentIds.EXPORT_BUTTON, "n_clicks"),
    State(ComponentIds.WORKFLOW_DATA_STORE, "data"),
    State(ComponentIds.EXPORT_WORKFLOW_SELECTOR, "value"),
    prevent_initial_call=True,
)
def export_data(n_clicks, store_data, selected_workflows):
    if not n_clicks or not store_data or not selected_workflows:
        return None

    common_fields = [WorkflowFields.clip_name, WorkflowFields.brain_type]
    current_date = datetime.now().strftime("%d-%m-%Y")

    if len(selected_workflows) > 1:
        dfs = []
        for workflow in selected_workflows:
            if workflow not in store_data or not store_data[workflow]:
                continue
            df = pd.DataFrame(store_data[workflow])
            rename_cols = {col: f"{workflow}_{col}" for col in df.columns if col not in common_fields}
            dfs.append(df.rename(columns=rename_cols))

        if not dfs:
            return None
        df = reduce(lambda left, right: pd.merge(left, right, on=common_fields, how="outer"), dfs)

        df = df[common_fields + [col for col in df.columns if col not in common_fields]]
        workflow_names = "_".join(selected_workflows)
        filename = f"{workflow_names}_data_{current_date}.csv"
    else:
        workflow = selected_workflows[0]
        if workflow not in store_data or not store_data[workflow]:
            return None

        df = pd.DataFrame(store_data[workflow])
        cols_ordered = [WorkflowFields.clip_name, WorkflowFields.brain_type] + [
            col for col in df.columns if col not in common_fields
        ]
        df = df[cols_ordered]
        filename = f"{workflow}_data_{current_date}.csv"

    return dcc.send_data_frame(df.to_csv, filename, index=False)
