import plotly.express as px


def basic_bar_graph(data, x, y, title="", color=None, bar_width=0.4):
    fig = px.bar(data, x=x, y=y, title=f"<b>{title}<b>", color=color, text=y)
    fig.update_layout(
        showlegend=False,
        font=dict(size=16),
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    fig.update_traces(
        texttemplate="%{text:.3f}",
        textposition="inside",
        textfont=dict(color="white", size=16),
        width=[bar_width] * len(data.index),
    )
    return fig
