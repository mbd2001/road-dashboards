from dataclasses import dataclass
from typing import List

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BaseColumn


@dataclass(kw_only=True)
class BaseGraphProperties:
    """
    Defines the base properties of a single graph

    Attributes:
            name (str): the name of the graph, used for the title and the id
            full_grid_row (bool): optional.
    """

    name: str
    full_grid_row: bool = False


@dataclass
class CasesGraphProperties(BaseGraphProperties):
    """
    Defines the properties of cases graph

    Attributes:
            interesting_cases (dict): dict of cases names -> sql description of the case
            extra_columns (list): the columns included in the interesting cases
            ignore_filter (str): optional. which rows to ignore when computing the query. can be turned off by the user
    """

    interesting_cases: dict
    extra_columns: List[BaseColumn]
    ignore_filter: str = ""


@dataclass
class GroupByGraphProperties(BaseGraphProperties):
    """
    Defines the properties of group by graph

    Attributes:
            group_by_column (str): the column over which we count group by
            diff_column (str): optional. column to compare to the group by column. computed as (abs(group_by - diff))
            include_slider (bool): optional. True if the graph should include slider
            slider_default_value (int): optional. default value for the slider
            ignore_filter (str): optional. which rows to ignore when computing the query. can be turned off by the user
    """

    group_by_column: BaseColumn
    diff_column: BaseColumn = None
    include_slider: bool = False
    slider_default_value: int = 0
    ignore_filter: str = ""

    def __post_init__(self):
        self.extra_columns = [col for col in [self.group_by_column, self.diff_column] if col]


@dataclass
class ConfMatGraphProperties(BaseGraphProperties):
    """
    Defines the properties of confusion matrix graph

    Attributes:
            column_to_compare (str): the relevant column to compare between 2 datasets
            ignore_filter (str): optional. which rows to ignore when computing the query. can be turned off by the user
    """

    column_to_compare: BaseColumn
    ignore_filter: str = ""

    def __post_init__(self):
        self.extra_columns = [self.column_to_compare]
