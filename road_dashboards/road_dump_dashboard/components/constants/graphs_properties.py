from dataclasses import dataclass
from typing import Collection


@dataclass
class CountGraphProperties:
    name: str
    ignore_filter: str = None
    group_by_column: str = None
    diff_column: str = None
    interesting_cases: dict = None
    extra_columns: list = None
    full_grid_row: bool = False
    include_slider: bool = False
    slider_default_value: int = 0

    def __post_init__(self):
        assert not (
            self.diff_column and not self.group_by_column
        ), "you can't pass diff column without groupby column to compare to"
        assert not (
            self.interesting_cases and self.group_by_column
        ), "you can query by main column or by interesting_cases, but not both at the same time"
        assert not (
            self.interesting_cases and not self.extra_columns
        ), "passing interesting cases requires you to specify the extra columns that needed from the data"

        if isinstance(self.extra_columns, str):
            self.extra_columns = [self.extra_columns]

        if self.group_by_column and not self.extra_columns:
            self.extra_columns = [col for col in [self.group_by_column, self.diff_column] if col is not None]


@dataclass
class ConfMatGraphProperties:
    name: str
    column_to_compare: str
    ignore_filter: str = None
    extra_columns: list = None
    full_grid_row: bool = False

    def __post_init__(self):
        if isinstance(self.extra_columns, str):
            self.extra_columns = [self.extra_columns]

        if not self.extra_columns:
            self.extra_columns = [self.column_to_compare]


@dataclass
class GraphsPerPage:
    count_graphs: Collection[CountGraphProperties] = None
    conf_mat_graphs: Collection[ConfMatGraphProperties] = None

    def __post_init__(self):
        self.count_graphs = self._graph_list_to_dict(self.count_graphs)
        self.conf_mat_graphs = self._graph_list_to_dict(self.conf_mat_graphs)

    @staticmethod
    def _graph_list_to_dict(graph_list):
        if graph_list is None:
            return None

        return {graph.name: graph.__dict__ for graph in graph_list}


meta_data_graphs = GraphsPerPage(
    count_graphs=[
        CountGraphProperties(
            name="Top View Perfects Exists",
            group_by_column="is_tv_perfect",
        ),
        CountGraphProperties(
            name="Gtem Exists",
            group_by_column="gtem_labels_exist",
        ),
        CountGraphProperties(
            name="Curve Rad Distribution",
            group_by_column="curve_rad_ahead",
            full_grid_row=True,
            include_slider=True,
            slider_default_value=2,
            ignore_filter="curve_rad_ahead <> 99999",
        ),
        CountGraphProperties(name="Batch Distribution", group_by_column="batch_num", full_grid_row=True),
        CountGraphProperties(
            name="Road Type Distribution",
            interesting_cases={
                "highway": "mdbi_road_highway = TRUE",
                "country": "mdbi_road_country = TRUE",
                "urban": "mdbi_road_city = TRUE",
                "freeway": "mdbi_road_freeway = TRUE",
            },
            extra_columns=["mdbi_road_highway", "mdbi_road_country", "mdbi_road_city", "mdbi_road_freeway"],
        ),
        CountGraphProperties(
            name="Lane Mark Color Distribution",
            interesting_cases={
                "yellow": "rightColor_yellow = TRUE OR leftColor_yellow = TRUE",
                "white": "rightColor_white = TRUE OR leftColor_white = TRUE",
                "blue": "rightColor_blue = TRUE OR leftColor_blue = TRUE",
            },
            extra_columns=[
                "rightColor_yellow",
                "leftColor_yellow",
                "rightColor_white",
                "leftColor_white",
                "rightColor_blue",
                "leftColor_blue",
            ],
        ),
    ],
    conf_mat_graphs=[
        ConfMatGraphProperties(name="Top View Perfects Classification", column_to_compare="is_tv_perfect"),
        ConfMatGraphProperties(name="Gtem Classification", column_to_compare="gtem_labels_exist"),
    ],
)

lane_marks_graphs = GraphsPerPage(
    count_graphs=[
        CountGraphProperties(
            name="Role Distribution",
            group_by_column="role",
        ),
        CountGraphProperties(
            name="Color Distribution",
            group_by_column="color",
        ),
        CountGraphProperties(
            name="Type Distribution",
            group_by_column="type",
        ),
        CountGraphProperties(
            name="View Range Distribution",
            group_by_column="role",
        ),
        CountGraphProperties(
            name="Lane Mark Width Distribution",
            group_by_column="half_width",
            ignore_filter="type in ('dashed', 'solidDashed', 'dashedSolid', 'dashedDashed', 'decelerationDashed')",
            include_slider=True,
            slider_default_value=0,
        ),
        CountGraphProperties(
            name="Dashed Length Img Distribution",
            group_by_column="dashed_end_y",
            diff_column="dashed_start_y",
            ignore_filter="type in ('dashed', 'solidDashed', 'dashedSolid', 'dashedDashed', 'decelerationDashed')",
            include_slider=True,
            slider_default_value=0,
        ),
        CountGraphProperties(
            name="Batch Distribution", group_by_column="batch_num", full_grid_row=True
        ),  # TODO: add 'dashed_gap'
    ],
    conf_mat_graphs=[
        ConfMatGraphProperties(name="Role Classification", column_to_compare="role"),
        ConfMatGraphProperties(name="Color Classification", column_to_compare="color"),
        ConfMatGraphProperties(name="Type Classification", column_to_compare="type"),
    ],
)

pathnet_graphs = GraphsPerPage(
    count_graphs=[
        CountGraphProperties(name="Role Distribution", group_by_column="dp_role"),
        CountGraphProperties(
            name="Split Role Distribution", group_by_column="dp_split_role", ignore_filter="dp_split_role <> 'IGNORE'"
        ),
        CountGraphProperties(
            name="Primary Role Distribution",
            group_by_column="dp_primary_role",
            ignore_filter="dp_primary_role <> 'IGNORE'",
        ),
        CountGraphProperties(
            name="Merge Role Distribution", group_by_column="dp_merge_role", ignore_filter="dp_merge_role <> 'IGNORE'"
        ),
        CountGraphProperties(name="Oncoming Distribution", group_by_column="dp_points_oncoming"),
        CountGraphProperties(name="Batch Distribution", group_by_column="batch_num", full_grid_row=True),
    ],
    conf_mat_graphs=[
        ConfMatGraphProperties(name="Role Classification", column_to_compare="dp_role", full_grid_row=True),
        ConfMatGraphProperties(
            name="Split Role Classification",
            column_to_compare="dp_split_role",
            ignore_filter="dp_split_role <> 'IGNORE'",
        ),
        ConfMatGraphProperties(
            name="Primary Role Classification",
            column_to_compare="dp_primary_role",
            ignore_filter="dp_primary_role <> 'IGNORE'",
        ),
        ConfMatGraphProperties(
            name="Merge Role Classification",
            column_to_compare="dp_merge_role",
            ignore_filter="dp_merge_role <> 'IGNORE'",
        ),
        ConfMatGraphProperties(name="Oncoming Classification", column_to_compare="dp_points_oncoming"),
    ],
)
GRAPHS_PER_PAGE = {
    "meta_data": meta_data_graphs.__dict__,
    "lane_marks": lane_marks_graphs.__dict__,
    "pathnet": pathnet_graphs.__dict__,
}
