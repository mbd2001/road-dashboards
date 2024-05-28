from road_eval_dashboard.road_dump_dashboard.graphs import basic_pie_chart, draw_line_graph


def pie_or_line_wrapper(data, names, values, title="", hover=None, color="dump_name"):
    if data[color].nunique() == 1:
        fig = basic_pie_chart(data, names, values, title=title, hover=hover)
    else:
        fig = draw_line_graph(data, names, values, title=title, hover=hover, color=color)

    return fig
