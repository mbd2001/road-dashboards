import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, Input, Output, State, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components import page_content, sidebar
from road_dashboards.road_eval_dashboard.components.catalog_table import (
    init_nets,
    run_eval_db_manager,
    update_nets_md_according_to_population,
    update_state_by_nets,
)
from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    GRAPH_TO_COPY,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_TO_TYPE,
    NET_ID_TO_FB_BEST_THRESH,
    NETS,
    STATE_NOTIFICATION,
    URL,
)
from road_dashboards.road_eval_dashboard.components.dcc_stores import init_dcc_stores
from road_dashboards.road_eval_dashboard.utils.url_state_utils import META_DATA_STATE_KEY, NETS_STATE_KEY, get_state

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    routing_callback_inputs={
        # The app state is serialised in the URL hash without refreshing the page
        # This URL can be copied and then parsed on page load
        "state": State(URL, "hash"),
    },
)

app.layout = html.Div(
    [
        init_dcc_stores(),
        dcc.Location(id=URL),
        sidebar.sidebar(),
        page_content.layout,
    ],
    className="wrapper",
)

app.clientside_callback(
    """function(stored_image_data) {
    if (stored_image_data) {
        const img = new Image();
        img.src = 'data:image/png;base64,' + stored_image_data;

        img.onload = function() {
            const canvas = document.createElement('canvas');
            canvas.width = this.naturalWidth;
            canvas.height = this.naturalHeight;
            canvas.getContext('2d').drawImage(this, 0, 0);

            canvas.toBlob(function(blob) {
                const item = new ClipboardItem({'image/png': blob});
                navigator.clipboard.write([item]);
            });
        };
    }
    return window.dash_clientside.no_update, false
}
""",
    Output("saved_alert", "is_open"),
    Input(GRAPH_TO_COPY, "data"),
)


@app.callback(Output(URL, "pathname"), Input(URL, "pathname"))
def redirect_to_home(pathname):
    if pathname == "/":
        return "/home"

    return no_update


@app.callback(
    Output(NETS, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_TYPE, "data", allow_duplicate=True),
    Output(MD_COLUMNS_OPTION, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data", allow_duplicate=True),
    Output(EFFECTIVE_SAMPLES_PER_BATCH, "data", allow_duplicate=True),
    Output(NET_ID_TO_FB_BEST_THRESH, "data", allow_duplicate=True),
    Output(STATE_NOTIFICATION, "children"),
    Input(URL, "hash"),
    State(NETS, "data"),
    prevent_initial_call=True,
)
def init_run(state, nets):
    nets_ids = get_state(state, NETS_STATE_KEY)
    if not nets_ids or (nets and compare_existing_nets_to_hashed_nets(nets, nets_ids)):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    rows = [run_eval_db_manager.get_item(net_id) for net_id in nets_ids]
    nets = init_nets(pd.DataFrame(rows))
    (
        md_columns_options,
        md_columns_to_distinguish_values,
        md_columns_to_type,
        effective_samples_per_batch,
        net_id_to_best_thresh,
    ) = update_state_by_nets(nets)
    nets = update_nets_md_according_to_population(
        nets, md_columns_to_distinguish_values
    )  # TODO: backward compatibility, will be removed later

    notification = dbc.Alert("State loaded successfully!", color="success", dismissable=True, duration=2500, fade=True)
    return (
        nets,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        effective_samples_per_batch,
        net_id_to_best_thresh,
        notification,
    )


def compare_existing_nets_to_hashed_nets(nets: dict, run_ids: list):
    return nets["run_names"] == run_ids


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6018", debug=True)
