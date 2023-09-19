import plotly.graph_objects as go


def draw_path_net_graph(data, distances, title="", role="non-host"):
    fig = go.Figure()
    for ind, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=distances,
                y=[row[f"score_{dist}"] for dist in distances],
                name=row.net_id,
            )
        )
    fig.update_layout(
        title=f"<b>{role.title()} {title.title()}<b>",
        xaxis_title="Time (s)",
        yaxis_title=title.title(),
        xaxis=dict(constrain="domain"),
        font=dict(size=16),
    )
    return fig
