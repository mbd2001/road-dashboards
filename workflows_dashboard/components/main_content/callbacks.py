from datetime import datetime

import pandas as pd
from dash import Input, Output, State, callback, dcc

from workflows_dashboard.config import DOWNLOAD_DATAFRAME, EXPORT_BUTTON, WORKFLOW_DATA_STORE, WORKFLOW_SELECTOR


@callback(
    Output(DOWNLOAD_DATAFRAME, "data"),
    Input(EXPORT_BUTTON, "n_clicks"),
    State(WORKFLOW_DATA_STORE, "data"),
    State(WORKFLOW_SELECTOR, "value"),
    prevent_initial_call=True,
)
def export_data(n_clicks, store_data, selected_workflow):
    if not n_clicks or not store_data or selected_workflow not in store_data:
        return None

    df = pd.DataFrame(store_data[selected_workflow])

    if df.empty:
        return None

    timestamp = datetime.now().strftime("%d-%m-%Y")
    filename = f"{selected_workflow}_data_{timestamp}.csv"

    return dcc.send_data_frame(df.to_csv, filename, index=False)
