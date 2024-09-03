import plotly.express as px


def draw_line_graph(data, names, values, title="", hover=None, color=None):
    data = data.sort_values(by=names)
    fig = px.line(data, x=names, y=values, color=color, hover_data=hover, markers=True)
    fig.update_layout(
        title=f"<b>{title}<b>",
        xaxis_title=names.replace("_", " ").title(),
        yaxis_title=values.replace("_", " ").title(),
        xaxis=dict(constrain="domain"),
        font=dict(size=16),
    )
    return fig
