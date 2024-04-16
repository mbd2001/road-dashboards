import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html

from road_eval_dashboard.components.components_ids import (
    VIEW_RANGE_HISTOGRAM,
    VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER,
    VIEW_RANGE_HISTOGRAM_CUMULATIVE,
    VIEW_RANGE_HISTOGRAM_ERR_EST,
    VIEW_RANGE_HISTOGRAM_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE,
    VIEW_RANGE_SUCCESS_RATE_ERR_EST,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE,
    VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP,
    VIEW_RANGE_SUCCESS_RATE_NAIVE_Z,
    VIEW_RANGE_SUCCESS_RATE_Z_RANGE,
    VIEW_RANGE_SUCCESS_RATE_Z_STEP,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper


def view_range_success_rate_card():
    return card_wrapper(
        [
            dbc.Row(loading_wrapper([dcc.Graph(id=VIEW_RANGE_SUCCESS_RATE, config={"displayModeBar": False})])),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=VIEW_RANGE_SUCCESS_RATE_NAIVE_Z,
                        on=False,
                        label="use naive Z",
                        labelPosition="top",
                    ),
                    daq.BooleanSwitch(
                        id=VIEW_RANGE_SUCCESS_RATE_ERR_EST,
                        on=True,
                        label="filter error estimation",
                        labelPosition="top",
                    ),
                    html.Div(
                        [
                            dcc.RangeSlider(
                                id=VIEW_RANGE_SUCCESS_RATE_Z_RANGE,
                                min=10,
                                max=250,
                                step=10,
                                value=[30, 120],
                            ),
                            html.Label("Z range", style={"text-align": "center"}),
                        ],
                        style={"width": "80%"},
                    ),
                    html.Div(
                        [
                            dcc.Slider(
                                id=VIEW_RANGE_SUCCESS_RATE_Z_STEP,
                                min=5,
                                max=50,
                                step=5,
                                value=10,
                            ),
                            html.Label("Z step", style={"text-align": "center"}),
                        ],
                        style={"width": "80%"},
                    ),
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


def view_range_histogram_card():
    return card_wrapper(
        [
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=VIEW_RANGE_HISTOGRAM, config={"displayModeBar": False})]),
                        width=11,
                    ),
                    dbc.Col(
                        dcc.Slider(
                            10,
                            50,
                            10,
                            id=VIEW_RANGE_HISTOGRAM_BIN_SIZE_SLIDER,
                            vertical=True,
                            marks={i: str(i) for i in range(10, 51, 10)},
                            value=10,
                        ),
                        width=1,
                    ),
                ]
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id=VIEW_RANGE_HISTOGRAM_NAIVE_Z,
                        on=False,
                        label="use naive Z",
                        labelPosition="top",
                    ),
                    daq.BooleanSwitch(
                        id=VIEW_RANGE_HISTOGRAM_CUMULATIVE,
                        on=True,
                        label="cumulative graph",
                        labelPosition="top",
                    ),
                    daq.BooleanSwitch(
                        id=VIEW_RANGE_HISTOGRAM_ERR_EST,
                        on=True,
                        label="filter error estimation",
                        labelPosition="top",
                    ),
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


def view_range_host_next_success_rate_card():
    return card_wrapper(
        [
            dbc.Row(
                loading_wrapper(
                    [
                        dcc.Graph(
                            id={"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT, "extra_filter": ""},
                            config={"displayModeBar": False},
                        )
                    ]
                )
            ),
            dbc.Stack(
                [
                    daq.BooleanSwitch(
                        id={"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_NAIVE_Z, "extra_filter": ""},
                        on=False,
                        label="use naive Z",
                        labelPosition="top",
                    ),
                    daq.BooleanSwitch(
                        id={"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_ERR_EST, "extra_filter": ""},
                        on=True,
                        label="filter error estimation",
                        labelPosition="top",
                    ),
                    html.Div(
                        [
                            dcc.RangeSlider(
                                id={"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_RANGE, "extra_filter": ""},
                                min=10,
                                max=250,
                                step=10,
                                value=[30, 120],
                            ),
                            html.Label("Z range", style={"text-align": "center"}),
                        ],
                        style={"width": "80%"},
                    ),
                    html.Div(
                        [
                            dcc.Slider(
                                id={"type": VIEW_RANGE_SUCCESS_RATE_HOST_NEXT_Z_STEP, "extra_filter": ""},
                                min=5,
                                max=50,
                                step=5,
                                value=10,
                            ),
                            html.Label("Z step", style={"text-align": "center"}),
                        ],
                        style={"width": "80%"},
                    ),
                ],
                direction="horizontal",
                gap=3,
            ),
        ]
    )


def get_host_next_graph(host_id, next_id, is_Z_id):
    return card_wrapper(
        [
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=host_id, config={"displayModeBar": False})]),
                        width=6,
                    ),
                    dbc.Col(
                        loading_wrapper([dcc.Graph(id=next_id, config={"displayModeBar": False})]),
                        width=6,
                    ),
                ]
            ),
            daq.BooleanSwitch(
                id=is_Z_id,
                on=False,
                label="show by Z",
                labelPosition="top",
            ),
        ]
    )
