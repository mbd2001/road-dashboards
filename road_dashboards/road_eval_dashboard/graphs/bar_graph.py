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


def comparison_bar_graph(data, x, y, facet_col, title="", text=None):
    text = y if text is None else text
    fig = px.bar(data, x=x, y=y, title=f"<b>{title}<b>", color=x, text=text, facet_col=facet_col, facet_col_spacing=0.2)
    fig.for_each_annotation(lambda a: a.update(text=""))

    x_titles = data[facet_col].unique()
    for i, x_title in enumerate(x_titles):
        fig.update_xaxes(title_text=x_title, row=1, col=i + 1)

    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_layout(
        font=dict(size=16),
        yaxis_title=y.replace("_", " ").title(),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
    )
    return fig
