# TODO: create dataclasses

FILTERS_DICT = {
    "road_type": {
        "filters": {
            "highway": "mdbi_road_highway = TRUE OR mdbi_road_freeway = TRUE",
            "country": "mdbi_road_country = TRUE",
            "urban": "mdbi_road_city = TRUE",
        },
        "extra_columns": [
            "mdbi_road_highway",
            "mdbi_road_freeway",
            "mdbi_road_country",
            "mdbi_road_city",
        ],
    },
    "lane_mark_color": {
        "filters": {
            "yellow": "rightColor_yellow = TRUE OR leftColor_yellow = TRUE",
            "white": "rightColor_white = TRUE OR leftColor_white = TRUE",
            "blue": "rightColor_blue = TRUE OR leftColor_blue = TRUE",
        },
        "extra_columns": [
            "rightColor_yellow",
            "leftColor_yellow",
            "rightColor_white",
            "leftColor_white",
            "rightColor_blue",
            "leftColor_blue",
        ],
    },
}


COLUMNS_DICT = {  # TODO: consider adding post-process func option
    "lane_mark_width": {
        "main_column": "half_width",
        "extra_filters": "type in ('dashed', 'solidDashed', 'dashedSolid', 'dashedDashed', 'decelerationDashed')",
    },
    "dashed_length_img": {
        "main_column": "dashed_end_y",
        "diff_column": "dashed_start_y",
        "extra_filters": "type in ('dashed', 'solidDashed', 'dashedSolid', 'dashedDashed', 'decelerationDashed')",
    },
    "view_range": {
        "main_column": "view_range",
        "extra_filters": "view_range <> 0",
    },
}
