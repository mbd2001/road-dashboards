import plotly.graph_objects as go


def draw_conf_diagonal_compare(normalize_mats, names, class_names, host=False):
    fig = go.Figure()
    for normalize_mat, name in zip(normalize_mats, names):
        fig.add_trace(
            go.Scatter(
                x=class_names,
                y=normalize_mat.to_numpy().diagonal(),
                name=name,
            )
        )
    fig.update_layout(
        title=f"<b>{'Host' if host else 'Overall'} TP Rate per Label<b>",
        xaxis_title="Label",
        yaxis_title="TP Rate",
        xaxis=dict(constrain="domain"),
        font=dict(size=16),
    )
    return fig
