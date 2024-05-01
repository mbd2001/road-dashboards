import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

VERT = np.array((range(0, 256, 4))).reshape(-1, 1)
IGNORE_VAL = -999
IMG_AXIS = {"width": [0, 771], "height": [0, 256]}
WORLD_AXIS = {"width": [-15, 15], "height": [-1, 150]}
FIGS_HEIGHT = 800


def draw_top_view(candidates):
    fig = go.Figure()
    for cand in candidates:
        idx = cand["obj_id"]
        x = cand["dp_points"][:, 0] if "dp_points" in cand.keys() else cand["pos_x"]
        z = cand["dp_points"][:, 2] if "dp_points" in cand.keys() else cand["pos_z"]
        color = select_color(cand.get("color"))
        type = cand.get("type")
        view_range = cand.get("view_range")
        max_view_range_idx = cand.get("max_view_range_idx")
        draw_line(fig, idx, color, x, y=z, type=type, view_range=view_range, max_view_range_idx=max_view_range_idx)

    fig.update_layout(showlegend=False, height=FIGS_HEIGHT)
    fig.update_xaxes(range=WORLD_AXIS["width"])
    fig.update_yaxes(range=WORLD_AXIS["height"])
    graph = dcc.Graph(config={"displayModeBar": False}, figure=fig, style={"display": "none"})
    return graph


def draw_img(image, candidates, dump_name, clip_name, grab_index):
    fig = px.imshow(image, color_continuous_scale="gray", origin="lower", aspect="auto")
    for cand in candidates:
        idx = cand["obj_id"]
        x = cand["dv_dp_points"][:, 0] if "dv_dp_points" in cand.keys() else cand["pos"]
        y = cand["dv_dp_points"][:, 1] if "dv_dp_points" in cand.keys() else VERT
        color = select_color(cand.get("color"))
        type = cand.get("type")
        half_width = cand.get("half_width")
        view_range = cand.get("view_range")
        max_view_range_idx = cand.get("max_view_range_idx")
        draw_line(
            fig,
            idx,
            color,
            x,
            y,
            half_width=half_width,
            type=type,
            view_range=view_range,
            max_view_range_idx=max_view_range_idx,
        )

    fig.update_layout(title=f"{dump_name} <br><sup>{clip_name}, {grab_index}</sup>", coloraxis_showscale=False, height=FIGS_HEIGHT)
    fig.update_xaxes(showticklabels=False, range=IMG_AXIS["width"])
    fig.update_yaxes(showticklabels=False, range=IMG_AXIS["height"])
    graph = dcc.Graph(config={"displayModeBar": False}, figure=fig, style={"display": "none"})
    return graph


def select_color(color_str=None):
    if color_str is None or color_str == "ignore":
        return "green"
    return color_str


def draw_line(fig, idx, color, x, y, half_width=None, type=None, view_range=None, max_view_range_idx=None):
    x, y, half_width = cut_max_view_range(x, y, half_width=half_width, max_view_range_idx=max_view_range_idx)
    valid = x > IGNORE_VAL
    if not np.any(valid):
        return

    x, y, half_width = remove_ignores(valid, x, y, half_width)
    if half_width is not None:
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
                legendgroup=idx,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            marker=dict(size=4, color=color),
            legendgroup=idx,
            name=f"candidate {idx}",
            hovertemplate=parser_annotation(type, view_range),
        )
    )


def cut_max_view_range(x, y, half_width=None, max_view_range_idx=None):
    if max_view_range_idx is not None:
        x = x[:max_view_range_idx]
        y = y[:max_view_range_idx]
        if half_width:
            half_width = half_width[:max_view_range_idx]
    return x, y, half_width


def remove_ignores(valid, x, y, half_width=None):
    x = x[valid]
    y = y[valid]
    half_width = half_width[valid] if half_width is not None else None
    return x, y, half_width


def parser_annotation(type=None, view_range=None):
    view_range = f"vr={view_range}" if view_range else ""
    txt_str = ", ".join(label.title() for label in [type, view_range] if label)
    return txt_str
