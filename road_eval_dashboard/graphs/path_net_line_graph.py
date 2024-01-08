import plotly.graph_objects as go

from road_eval_dashboard.graphs.meta_data_filters_graph import get_greens_reds, choose_symbol


def draw_path_net_graph(data, cols, title="", role="non-host", hover=False, effective_samples={}, score_func=lambda row, filter: row[f"score_{filter}"]):
    fig = go.Figure()
    if effective_samples:
        greens, reds = get_greens_reds(data, cols, effective_samples, score_func)
    else:
        greens, reds = None, None
    for ind, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=cols,
                y=[score_func(row, col) for col in cols],
                name=row.net_id,
                hovertext=["lane marks: " + f'{row[f"count_{col}"]}' for col in cols] if hover else None,
                marker=dict(
                    symbol=[choose_symbol(col, reds[row.net_id], greens[row.net_id]) for col in cols],
                    size=10,
                )
                if effective_samples
                else None,
            )
        )
    fig.update_layout(
        title=f"<b>{role.title()} {title.title()}<b>",
        xaxis_title="Time (s)",
        yaxis_title=title.title(),
        xaxis=dict(constrain="domain"),
        yaxis=dict(range=[0, 1]),
        font=dict(size=16),
    )
    return fig
