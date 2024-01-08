import numpy as np
import plotly.graph_objects as go

from road_eval_dashboard.components.queries_manager import process_net_name, ROC_THRESHOLDS
from road_eval_dashboard.graphs.precision_recall_curve import calc_fb


def draw_roc_curve(data, prefix="", thresholds=ROC_THRESHOLDS):
    fig = go.Figure()
    fig.add_shape(type="line", line=dict(dash="dash"), x0=0, x1=1, y0=1, y1=0)

    for ind, row in data.iterrows():
        precision, tp_rate, fp_rate, fb_scores, best_fb, best_thresh, thresholds = get_roc_stat_for_net(
            row, thresholds=thresholds
        )

        net_id = process_net_name(row["net_id"])
        fb0 = fb_scores[np.argmin(np.abs(thresholds))]
        name = f"{net_id}, Nom Fb: {fb0: .3f} Best Fb: {best_fb:.3f}, Th: {best_thresh:.2f}"
        fig.add_trace(
            go.Scatter(
                x=fp_rate,
                y=tp_rate,
                name=name,
                mode="lines",
                hovertext=[f"Th: {thresholds[i]:.2f} Fb: {fb_scores[i]:.2f}" for i in range(thresholds.size)],
            )
        )

    fig.update_layout(
        title=f"<b>{prefix.title()} ROC Curve<b>",
        xaxis_title="FP Rate",
        yaxis_title="TP Rate (recall)",
        font=dict(size=16),
        legend=dict(orientation="h", y=-0.5),
    )
    fig["data"][0]["showlegend"] = True
    return fig


def get_roc_stat_for_net(data, thresholds=ROC_THRESHOLDS):
    fp = np.array([data[f"fp_{i}"] for i in range(thresholds.size)])
    tp = np.array([data[f"tp_{i}"] for i in range(thresholds.size)])
    fn = np.array([data[f"fn_{i}"] for i in range(thresholds.size)])
    tn = np.array([data[f"tn_{i}"] for i in range(thresholds.size)])

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    fp_rate = fp / (fp + tn)
    fb_scores = calc_fb(precision, recall)
    best_fb_ind = np.nanargmax(fb_scores)
    best_fb = fb_scores[best_fb_ind]
    best_thresh = thresholds[best_fb_ind]

    return precision, recall, fp_rate, fb_scores, best_fb, best_thresh, thresholds
