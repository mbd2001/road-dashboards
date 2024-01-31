from dash import dcc
import dash_daq as daq
import dash_bootstrap_components as dbc
from road_eval_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper


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