import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_FILTERS,
    NETS,
    REM_ACCURACY_ERROR_THRESHOLD_SLIDER,
    REM_AVERAGE_ERROR,
    REM_AVERAGE_ERROR_Z_OR_SEC,
    REM_ROLES_DROPDOWN,
    REM_SOURCE_DROPDOWN,
)
from road_dashboards.road_eval_dashboard.components.graph_wrapper import graph_wrapper
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_sum_bins_metric_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import draw_meta_data_filters
from road_dashboards.road_eval_dashboard.pages.rem_page.utils import (
    IGNORES_FILTER,
    REM_FILTERS,
    REM_TYPE,
    SEC_BINS,
    SEC_FILTERS,
    Z_BINS,
    Z_FILTERS,
    get_base_graph_layout,
    get_rem_fig,
    get_rem_score,
)


def get_settings_layout(tab, slider_value=0.3):
    return card_wrapper(
        [
            html.H6("Choose Error Threshold", style={"margin-top": 10}),
            html.Div(
                [
                    dcc.Slider(
                        id={"rem_type": REM_TYPE, "out": REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "tab": tab},
                        min=0,
                        max=1,
                        step=0.1,
                        value=slider_value,
                    ),
                ],
                style={"margin-top": 5},
            ),
        ]
    )


def get_error_histogram_layout(tab):
    return card_wrapper(
        [
            dbc.Row(
                graph_wrapper(
                    {"rem_type": REM_TYPE, "out": REM_AVERAGE_ERROR, "tab": tab},
                )
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id={"rem_type": REM_TYPE, "out": REM_AVERAGE_ERROR_Z_OR_SEC, "tab": tab},
                        on=False,
                        label="Sec/Z",
                        labelPosition="top",
                        persistence=True,
                        persistence_type="session",
                    )
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


def get_accuracy_layout(tab, extra_layout_after_setting=None, slider_value=0.3):
    layout_children = [get_settings_layout(tab, slider_value)]
    if extra_layout_after_setting is not None:
        layout_children += [extra_layout_after_setting]
    return html.Div(
        layout_children
        + [
            get_base_graph_layout(
                filter_name, tab, sort_by_dist=filter_props.get("sort_by_dist", False), tab_type="accuracy"
            )
            for filter_name, filter_props in REM_FILTERS.items()
        ]
        + [get_error_histogram_layout(tab)]
    )


@callback(
    Output({"rem_type": REM_TYPE, "out": REM_AVERAGE_ERROR, "tab": MATCH}, "figure"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_AVERAGE_ERROR_Z_OR_SEC, "tab": MATCH}, "on"),
    Input(MD_FILTERS, "data"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State({"rem_type": REM_TYPE, "out": REM_AVERAGE_ERROR, "tab": MATCH}, "id"),
)
def get_average_error_graph(role, source, z_or_sec, meta_data_filters, nets, effective_samples, graph_id):
    tab = graph_id["tab"]
    sum_col = f"rem_{tab}_error_{source}"
    interesting_filters = Z_FILTERS if z_or_sec else SEC_FILTERS
    filter_name = "Z Bins" if z_or_sec else "Seconds"
    query = generate_sum_bins_metric_query(
        nets["gt_tables"],
        nets["meta_data"],
        sum_col=sum_col,
        interesting_filters=interesting_filters,
        meta_data_filters=meta_data_filters,
        extra_filters=IGNORES_FILTER.format(col=sum_col),
        extra_columns=["rem_point_sec", "rem_point_Z"],
        role=role,
    )
    data, _ = run_query_with_nets_names_processing(query)
    bins = Z_BINS if z_or_sec else SEC_BINS
    for bin in bins[:-1]:
        data[f"score_{bin}"] = data[f"score_{bin}"] / data[f"count_{bin}"]
    data = data.sort_values(by="net_id")
    fig = draw_meta_data_filters(
        data,
        list(interesting_filters.keys()),
        get_rem_score,
        effective_samples=effective_samples,
        title=f"Average Error By {source}",
        xaxis=filter_name,
        yaxis="Avg Error",
        hover=True,
    )
    return fig


@callback(
    Output(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": False,
            "tab": ALL,
            "tab_type": "accuracy",
        },
        "figure",
    ),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "tab": ALL}, "value"),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": False,
            "tab": ALL,
            "tab_type": "accuracy",
        },
        "id",
    ),
)
def get_none_dist_graph(meta_data_filters, role, source, error_threshold, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    source = source
    error_threshold = error_threshold[0]
    graph_id = graph_id[0]
    filter_name = graph_id["filter"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["filters"]
    tab = graph_id["tab"]
    fig = get_accuracy_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name.replace("_", " ").title(),
        source=source,
        error_threshold=error_threshold,
        role=role,
        tab=tab,
    )
    return [fig]


@callback(
    Output(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": ALL,
            "tab_type": "accuracy",
        },
        "figure",
    ),
    Input(MD_FILTERS, "data"),
    Input(REM_ROLES_DROPDOWN, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_SOURCE_DROPDOWN}, "value"),
    Input({"rem_type": REM_TYPE, "out": REM_ACCURACY_ERROR_THRESHOLD_SLIDER, "tab": ALL}, "value"),
    Input(
        {
            "out": "sort_by_dist",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": ALL,
            "tab_type": "accuracy",
        },
        "on",
    ),
    Input(NETS, "data"),
    State(EFFECTIVE_SAMPLES_PER_BATCH, "data"),
    State(
        {
            "out": "graph",
            "filter": MATCH,
            "rem_type": REM_TYPE,
            "sort_by_dist": True,
            "tab": ALL,
            "tab_type": "accuracy",
        },
        "id",
    ),
)
def get_dist_graph(meta_data_filters, role, source, error_threshold, sort_by_dist, nets, effective_samples, graph_id):
    if not nets:
        return no_update
    graph_id = graph_id[0]
    source = source
    error_threshold = error_threshold[0]
    filter_name = graph_id["filter"]
    tab = graph_id["tab"]
    filters = REM_FILTERS[filter_name]
    interesting_filters = filters["dist_filters"] if sort_by_dist else filters["filters"]
    fig = get_accuracy_fig(
        meta_data_filters=meta_data_filters,
        nets=nets,
        interesting_filters=interesting_filters,
        effective_samples=effective_samples,
        filter_name=filter_name.replace("_", " ").title(),
        source=source,
        error_threshold=error_threshold,
        role=role,
        tab=tab,
    )
    return [fig]


def get_accuracy_fig(
    meta_data_filters, nets, interesting_filters, effective_samples, filter_name, source, error_threshold, tab, role=""
):
    label = f"rem_{tab}_error_{source}"
    pred = error_threshold
    title = f"Accuracy By {source} With Threshold {error_threshold}"
    fig = get_rem_fig(
        meta_data_filters,
        nets,
        interesting_filters,
        effective_samples,
        filter_name,
        title,
        filter_name,
        "Success Rate",
        label,
        pred,
        role=role,
    )
    return fig
