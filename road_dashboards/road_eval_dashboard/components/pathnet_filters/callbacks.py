from dash import Input, Output, State, callback, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    BIN_POPULATION_DROPDOWN,
    MD_FILTERS,
    NETS,
    PATHNET_FILTERS,
    PATHNET_FILTERS_IN_DROPDOWN,
    PATHNET_FILTERS_OUT_DROPDOWN,
    PATHNET_MD_FILTERS_SUBMIT_BUTTON,
    PATHNET_PRED,
    ROLE_POPULATION_VALUE,
    SPLIT_ROLE_POPULATION_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_avail_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list


@callback(
    Output(PATHNET_FILTERS, "data"),
    State(BIN_POPULATION_DROPDOWN, "value"),
    State(SPLIT_ROLE_POPULATION_DROPDOWN, "value"),
    State(ROLE_POPULATION_VALUE, "value"),
    State("roles_operation", "value"),
    Input("pathnet_update_filters_btn", "n_clicks"),
)
def update_pathnet_filters(bin_population, column, value, roles_operation, n_clicks):
    if (not bin_population and not column and not value) or not n_clicks:
        return ""
    filters = []
    if bin_population:
        filters.append(f"bin_population = '{bin_population}'")
    if column and roles_operation and value is not None:
        filters.append(f"{column} {roles_operation} {value}")

    return " AND ".join(filters)


@callback(
    Output(BIN_POPULATION_DROPDOWN, "options"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
)
def create_population_dropdown(meta_data_filters, nets):
    if not nets:
        return no_update
    query = generate_avail_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters,
        column_name="bin_population",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return create_dropdown_options_list(labels=df["bin_population"])


@callback(
    Output(SPLIT_ROLE_POPULATION_DROPDOWN, "options"),
    Input(NETS, "data"),
)
def create_dp_split_role_dropdown(nets):
    if not nets:
        return no_update
    return create_dropdown_options_list(labels=["split_role", "matched_split_role", "ignore_role"])


@callback(
    Output(ROLE_POPULATION_VALUE, "options"),
    Input(SPLIT_ROLE_POPULATION_DROPDOWN, "value"),
    State(MD_FILTERS, "data"),
    State(NETS, "data"),
)
def create_dp_split_role_dropdown(split_role_population_values, meta_data_filters, nets):
    if not split_role_population_values or not nets:
        return no_update
    query = generate_avail_query(
        nets[PATHNET_PRED],
        nets["meta_data"],
        meta_data_filters,
        column_name=split_role_population_values,
        extra_columns=[split_role_population_values],
    )
    df, _ = run_query_with_nets_names_processing(query)
    values = set(df[split_role_population_values])
    return create_dropdown_options_list(labels=values)


@callback(
    Output(MD_FILTERS, "data", allow_duplicate=True),
    State(PATHNET_FILTERS_IN_DROPDOWN, "value"),
    State(PATHNET_FILTERS_OUT_DROPDOWN, "value"),
    State(MD_FILTERS, "data"),
    Input(PATHNET_MD_FILTERS_SUBMIT_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def update_metadata_filters_by_pathnet_filters(in_filters, out_filters, curr_filters, n_clicks):
    if not n_clicks or (not in_filters and not out_filters):
        return ""

    final_filters = []

    if in_filters:
        in_filters = " OR ".join([f"({filter})" for filter in in_filters])
        final_filters.append(f"({in_filters})")

    if out_filters:
        out_filters = " OR ".join([f"({filter})" for filter in out_filters])
        final_filters.append(f"NOT ({out_filters})")

    if curr_filters:
        final_filters.append(f"({curr_filters})")

    return " AND ".join(final_filters)
