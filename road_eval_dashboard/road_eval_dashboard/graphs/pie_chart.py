import plotly.express as px


def basic_pie_chart(data, names, values, title="", color=None):
    fig = px.pie(data, names=names, values=values, color=color, title=title)
    return fig
