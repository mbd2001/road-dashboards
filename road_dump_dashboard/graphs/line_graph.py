import plotly.express as px


def draw_line_graph(data, names, values, title="", hover=None):
    data = data.sort_values(by=names)
    fig = px.line(data, x=names, y=values, color="dump_name", hover_data=hover, markers=True)
    fig.update_layout(
        title=f"<b>{title.title()}<b>",
        xaxis_title="Values",
        yaxis_title=title.title(),
        xaxis=dict(constrain="domain"),
        font=dict(size=16),
    )
    return fig
