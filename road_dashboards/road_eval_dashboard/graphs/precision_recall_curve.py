import numpy as np
import plotly.graph_objects as go

from road_dashboards.road_eval_dashboard.components.queries_manager import THRESHOLDS, process_net_name

f_beta = 1
B2 = f_beta**2


def draw_precision_recall_curve(data, prefix="", thresholds=THRESHOLDS):
    fig = go.Figure()
    fig.add_shape(type="line", line=dict(dash="dash"), x0=0, x1=1, y0=1, y1=0)

    for ind, row in data.iterrows():
        precision, recall, best_fb, best_thresh = get_fb_stat_for_net(row, thresholds=thresholds)

        net_id = process_net_name(row["net_id"])
        name = f"{net_id}, Best Fb: {best_fb:.3f}, Thresh: {best_thresh:.2f}"
        fig.add_trace(
            go.Scatter(
                x=recall,
                y=precision,
                name=name,
                mode="lines",
                hovertext=[f"Thresh: {thresholds[i]:.2f}" for i in range(thresholds.size)],
            )
        )

    fig.update_layout(
        title=f"<b>{prefix.title()} Precision-Recall Curve<b>",
        xaxis_title="Recall",
        yaxis_title="Precision",
        font=dict(size=16),
        legend=dict(orientation="h", y=-0.5),
    )
    fig["data"][0]["showlegend"] = True
    return fig


def calc_fb(precision, recall):
    return ((1 + B2) * precision * recall) / ((B2 * precision) + recall + 1e-10)


def get_fb_stat_for_net(data, thresholds=THRESHOLDS):
    precision = [data[f"precision_{i}"] for i in range(thresholds.size)]
    recall = [data[f"recall_{i}"] for i in range(thresholds.size)]

    fb_scores = np.array([calc_fb(i, j) for i, j in zip(precision, recall)])
    best_fb_ind = np.argmax(fb_scores)
    best_fb = fb_scores[best_fb_ind]
    best_thresh = thresholds[best_fb_ind]

    return precision, recall, best_fb, best_thresh


def calc_best_thresh(data):
    net_id_to_best_thresh = {}
    for ind, row in data.iterrows():
        _, _, _, best_thresh = get_fb_stat_for_net(row)

        net_id = row["net_id"]
        net_id_to_best_thresh[net_id] = best_thresh
    return net_id_to_best_thresh
