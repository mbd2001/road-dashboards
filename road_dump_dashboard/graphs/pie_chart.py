import plotly.express as px


def basic_pie_chart(data, names, values, title="", hover=None):
    fig = px.pie(data, names=names, values=values, title=title, hover_data=hover)
    return fig
