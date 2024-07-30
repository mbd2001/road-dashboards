import itertools

import numpy as np
import plotly.graph_objects as go

from road_dashboards.road_eval_dashboard.graphs.precision_recall_curve import calc_fb


def compute_z_score_for_binomial_distribution(score1, score2, n1, n2):
    if n1 == 0 or n2 == 0 or score1 == score2:
        return 0
    p = (n1 * score1 + n2 * score2) / (n1 + n2)
    z = (score1 - score2) / np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return np.abs(z)


def choose_symbol(filter, reds, greens):
    if filter in greens:
        return "triangle-up"
    elif filter in reds:
        return "triangle-down"
    return "diamond-wide"


def get_greens_reds(data, interesting_columns, effective_samples, score_func):
    greens = {net: set() for net in data.net_id}
    reds = {net: set() for net in data.net_id}
    for col in interesting_columns:
        n1 = effective_samples[f"overall_{col}"]
        n2 = effective_samples[f"overall_{col}"]
        for (ind1, row1), (ind2, row2) in itertools.combinations(data.iterrows(), r=2):
            stat_value1 = score_func(row1, col)
            stat_value2 = score_func(row2, col)
            if stat_value2 and stat_value1 and n1 and n2:
                z_score = compute_z_score_for_binomial_distribution(stat_value1, stat_value2, n1, n2)
                if z_score > 1.96:  # threshold for 95%
                    greens[row1.net_id if stat_value1 > stat_value2 else row2.net_id].add(col)
                    reds[row2.net_id if stat_value1 > stat_value2 else row1.net_id].add(col)
    for net in data.net_id:
        batches_to_remove = greens[net].intersection(reds[net])
        greens[net] -= batches_to_remove
        reds[net] -= batches_to_remove
    return greens, reds


def draw_meta_data_filters(
    data,
    interesting_columns,
    score_func,
    hover=False,
    effective_samples={},
    title="",
    xaxis="Filter",
    yaxis="Fb Score",
    count_items_name="lane marks",
):
    if all(f"overall_{col}" in effective_samples for col in interesting_columns):
        greens, reds = get_greens_reds(data, interesting_columns, effective_samples, score_func)
    else:
        greens, reds = {}, {}

    fig = go.Figure()
    for ind, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=interesting_columns,
                y=[score_func(row, col) for col in interesting_columns],
                marker=(
                    dict(
                        symbol=[
                            choose_symbol(col, reds.get(row.net_id, []), greens.get(row.net_id, []))
                            for col in interesting_columns
                        ],
                        size=10,
                    )
                    if effective_samples
                    else None
                ),
                name=row.net_id,
                hovertext=(
                    [f"{count_items_name}: " + str(row[f"count_{col}"]) for col in interesting_columns]
                    if hover
                    else None
                ),
            )
        )
    fig.update_layout(
        title=f"<b>{title}<b>",
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        xaxis=dict(constrain="domain"),
        font=dict(size=16),
        legend=dict(orientation="h", yanchor="bottom", y=-1, xanchor="center", x=0.5),
    )
    return fig


def calc_fb_per_row(row, filter):
    precision = row[f"precision_{filter}"]
    recall = row[f"recall_{filter}"]
    fb = calc_fb(precision, recall)
    return fb
