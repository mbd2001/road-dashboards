import plotly.graph_objects as go

from road_dashboards.road_eval_dashboard.graphs.meta_data_filters_graph import choose_symbol, get_greens_reds


def draw_path_net_graph(
    data,
    cols,
    title="",
    role="non-host",
    effective_samples={},
    xaxis="Time (s)",
    yaxis=None,
    score_func=lambda row, score_filter: row[f"score_{score_filter}"],
    plot_bgcolor=None,
    hover=False,
    hover_func=lambda row, col: f"lane marks: {row[f'count_{col}']}",
):
    fig = go.Figure()
    if all(f"overall_{col}" in effective_samples for col in cols):
        greens, reds = get_greens_reds(data, cols, effective_samples, score_func)
    else:
        greens, reds = {}, {}

    for ind, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=cols,
                y=[score_func(row, col) for col in cols],
                name=row.net_id,
                hovertext=[hover_func(row, col) for col in cols] if hover else None,
                marker=(
                    dict(
                        symbol=[
                            choose_symbol(col, reds.get(row.net_id, []), greens.get(row.net_id, [])) for col in cols
                        ],
                        size=10,
                    )
                    if effective_samples
                    else None
                ),
            )
        )
    yaxis_title = yaxis or title
    fig.update_layout(
        title=f"<b>{role.title()} {title.title()}<b>",
        xaxis_title=xaxis,
        yaxis_title=yaxis_title.title(),
        xaxis=dict(constrain="domain"),
        yaxis=dict(range=[0, 1]),
        font=dict(size=16),
        legend_xanchor="center",
        legend=dict(orientation="h", yanchor="bottom", y=-1, xanchor="center", x=0.5),
        plot_bgcolor=plot_bgcolor,
    )
    return fig
