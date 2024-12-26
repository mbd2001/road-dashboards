import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def basic_pie_chart(
    data: pd.DataFrame, names: str, values: str, title: str = "", hover: str | list[str] | None = None
) -> go.Figure:
    fig = px.pie(data, names=names, values=values, title=title, hover_data=hover)
    fig.update_traces(textposition="inside", textinfo="percent")
    return fig
