from road_dump_dashboard.graphs.line_graph import draw_line_graph
from road_dump_dashboard.graphs.pie_chart import basic_pie_chart


def pie_or_line_wrapper(data, names, values, title="", hover=None, color="dump_name"):
    if data[color].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

    return fig
