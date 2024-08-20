from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from scipy import interpolate

VERT = np.array(range(0, 256, 4))
IGNORE_VAL = -999
IMG_AXIS = {"width": [0, 771], "height": [0, 256]}
WORLD_AXIS = {"width": [-15, 15], "height": [-1, 150]}
FIGS_HEIGHT = 800
COLOR_SCHEME = px.colors.qualitative.Plotly


@dataclass
class CandidateParams:
    obj_id: int
    color: str
    x: np.array
    y: np.array
    type: Optional[str] = None
    role: Optional[str] = None
    half_width: Optional[np.array] = None
    view_range: Optional[int] = None
    max_view_range_idx: Optional[int] = None
    dashed_y: Optional[np.array] = None

    def __post_init__(self):
        self.color = self.select_color(self.color, self.obj_id)
        self.x, self.y, self.half_width, self.dashed_y = self.cut_max_view_range(
            self.x, self.y, self.half_width, self.dashed_y, self.max_view_range_idx
        )
        self.x, self.y, self.half_width, self.dashed_y = self.remove_ignores(
            self.x, self.y, self.half_width, self.dashed_y
        )

    @staticmethod
    def select_color(color_str=None, obj_id=None):
        if color_str == "ignore":
            return "green"

        elif color_str:
            return color_str

        return COLOR_SCHEME[obj_id % len(COLOR_SCHEME)]

    @staticmethod
    def cut_max_view_range(x, y=None, half_width=None, dashed_y=None, max_view_range_idx=None):
        if max_view_range_idx is not None:
            x = x[:max_view_range_idx]
            y = y[:max_view_range_idx] if y is not None else None
            half_width = half_width[:max_view_range_idx] if half_width is not None else None

        max_y = np.max(y, initial=0) if y is not None else None
        dashed_y = (
            dashed_y[(dashed_y[:, 0] <= max_y) & (dashed_y[:, 1] <= max_y)]
            if dashed_y is not None and max_y is not None
            else None
        )
        return x, y, half_width, dashed_y

    @staticmethod
    def remove_ignores(x, y, half_width=None, dashed_y=None):
        dashed_y = (
            dashed_y[(dashed_y[:, 0] > IGNORE_VAL) & (dashed_y[:, 1] > IGNORE_VAL)] if dashed_y is not None else None
        )
        valid = x > IGNORE_VAL
        x = x[valid]
        y = y[valid] if y is not None else None
        half_width = half_width[valid] if half_width is not None else None
        return x, y, half_width, dashed_y


def get_candidate(cand: dict, is_img: bool = True):
    obj_id = int(cand["obj_id"])
    color = cand.get("color")
    type = cand.get("type")
    role = cand.get("role")
    view_range = cand.get("max_view_range")
    max_view_range_idx = cand.get("max_view_range_idx")
    if is_img is True:
        x = cand["dv_dp_points"][:, 0] if "dv_dp_points" in cand.keys() else cand["pos"]
        y = cand["dv_dp_points"][:, 1] if "dv_dp_points" in cand.keys() else VERT
        half_width = cand.get("half_width")
        dashed_y = get_aggregated_dashed_y(cand.get("dashed_start_y"), cand.get("dashed_end_y"))
        cand = CandidateParams(
            obj_id=obj_id,
            color=color,
            type=type,
            role=role,
            view_range=view_range,
            max_view_range_idx=max_view_range_idx,
            x=x,
            y=y,
            half_width=half_width,
            dashed_y=dashed_y,
        )
    else:
        x = cand["dp_points"][:, 0] if "dp_points" in cand.keys() else cand["pos_x"]
        z = cand["dp_points"][:, 2] if "dp_points" in cand.keys() else cand["pos_z"]
        cand = CandidateParams(
            obj_id=obj_id,
            color=color,
            type=type,
            view_range=view_range,
            max_view_range_idx=max_view_range_idx,
            x=x,
            y=z,
        )
    return cand


def get_aggregated_dashed_y(start_y=None, end_y=None):
    if start_y is None or end_y is None:
        return

    dashed_y = np.column_stack((start_y, end_y))
    return dashed_y


def draw_top_view(candidates: List[dict]):
    fig = go.Figure()
    for cand_dict in candidates:
        cand = get_candidate(cand_dict, is_img=False)
        draw_line(fig, cand)

    fig.update_layout(showlegend=False, height=FIGS_HEIGHT)
    fig.update_xaxes(range=WORLD_AXIS["width"])
    fig.update_yaxes(range=WORLD_AXIS["height"])
    graph = dcc.Graph(config={"displayModeBar": False}, figure=fig, style={"display": "none"})
    return graph


def draw_img(image, candidates, dump_name, clip_name, grab_index):
    fig = px.imshow(image, color_continuous_scale="gray", origin="lower", aspect="auto")
    for cand_dict in candidates:
        cand = get_candidate(cand_dict)
        draw_line(fig, cand)

    fig.update_layout(
        title=f"{dump_name} <br><sup>{clip_name}, {grab_index}</sup>", coloraxis_showscale=False, height=FIGS_HEIGHT
    )
    fig.update_xaxes(showticklabels=False, range=IMG_AXIS["width"])
    fig.update_yaxes(showticklabels=False, range=IMG_AXIS["height"])
    graph = dcc.Graph(config={"displayModeBar": False}, figure=fig, style={"display": "none"})
    return graph


def draw_line(fig, cand):
    if cand.half_width is not None:
        if (
            cand.dashed_y is not None
            and cand.type is not None
            and ("deceleration" in cand.type.lower() or "dash" in cand.type.lower())
        ):
            draw_interpolated_dashed_points(fig, cand)
        else:
            draw_line_width(fig, cand.x, cand.y, cand.half_width, cand.color, cand.obj_id)

    draw_line_scatter(fig, cand.x, cand.y, cand.obj_id, cand.color, cand.type, cand.role, cand.view_range)


def draw_interpolated_dashed_points(fig, cand):
    interp_half_w = interpolate.interp1d(cand.y, cand.half_width, fill_value="extrapolate", assume_sorted=True)
    interp_x = interpolate.interp1d(cand.y, cand.x, fill_value="extrapolate", assume_sorted=True)

    dashed_half_w = np.maximum(interp_half_w(cand.dashed_y), 0.5)
    dashed_x = interp_x(cand.dashed_y)
    for curr_x, curr_y, curr_half_w in zip(dashed_x, cand.dashed_y, dashed_half_w):
        draw_line_width(fig, curr_x, curr_y, curr_half_w, cand.color, cand.obj_id)


def draw_line_width(fig, x, y, half_width, color, obj_id):
    x_left_limit = x - half_width
    x_right_limit = x + half_width
    x_limits = np.concatenate([x_left_limit, x_right_limit[::-1]])
    extended_y = np.concatenate([y, y[::-1]])
    fig.add_trace(
        go.Scatter(
            x=x_limits,
            y=extended_y,
            opacity=0.3,
            fill="toself",
            fillcolor=color,
            line_color="rgba(255,255,255,0)",
            showlegend=False,
            legendgroup=obj_id,
        )
    )


def draw_line_scatter(fig, x, y, obj_id, color, type=None, role=None, view_range=None):
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            legendgroup=obj_id,
            name=f"candidate {obj_id}",
            hovertemplate=parser_annotation(type, role, view_range),
            line=dict(color=color, width=2),
        )
    )


def parser_annotation(type=None, role=None, view_range=None):
    view_range = f"vr={view_range}" if view_range else ""
    txt_str = ", ".join(label.title() for label in [type, role, view_range] if label)
    return txt_str
