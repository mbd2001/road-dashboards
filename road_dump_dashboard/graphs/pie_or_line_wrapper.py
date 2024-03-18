from road_dump_dashboard.graphs.line_graph import draw_line_graph
from road_dump_dashboard.graphs.pie_chart import basic_pie_chart


def pie_or_line_wrapper(data, names, values, title="", hover=None):
    print(data)
    if data["dump_name"].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover)

    return fig
