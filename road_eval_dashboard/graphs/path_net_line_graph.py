import plotly.graph_objects as go


def draw_path_net_graph(data, distances, title="", role="non-host", hover=False):
    fig = go.Figure()
    for ind, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=distances,
                y=[row[f"score_{dist}"] for dist in distances],
                name=row.net_id,
                hovertext=["lane marks: " + str(row[f"count_{str(col).replace('.', '_')}"]) for col in distances] if hover else None,
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
