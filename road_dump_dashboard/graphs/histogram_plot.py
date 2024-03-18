import plotly.express as px


def basic_histogram_plot(data, x, y, title="", color=None):
    print(data)
    fig = px.bar(data, x=x, y=y, title=f"<b>{title}<b>", color=color)
    fig.update_layout(
        showlegend=False,
        font=dict(size=16),
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    fig.update_layout(barmode="overlay")
    fig.update_traces(opacity=0.75)
    return fig
