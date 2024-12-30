import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def basic_histogram_plot(
    data: pd.DataFrame, x: str, y: str, title: str = "", color: str | None = "dump_name"
) -> go.Figure:
    fig = px.bar(data, x=x, y=y, title=f"<b>{title}<b>", color=color)
    fig.update_layout(
        font=dict(size=16),
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    fig.update_layout(barmode="overlay")
    fig.update_traces(opacity=0.75)
    return fig
