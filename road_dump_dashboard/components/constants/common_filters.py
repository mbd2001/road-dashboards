ROAD_TYPE_FILTERS = {
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
}

LANE_MARK_COLOR_FILTERS = {
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
}
