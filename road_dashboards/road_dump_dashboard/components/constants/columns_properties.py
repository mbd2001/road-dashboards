from dataclasses import dataclass

BASE_COLUMNS = ["population", "dump_name", "clip_name", "grabindex", "obj_id"]

COMMON_COLUMNS = BASE_COLUMNS + [
    "batch_num",
    "pred_name",
]


@dataclass
class BaseColumn:
    """
    Defines the base properties of a data column

    Attributes:
            name (str): the name of the column, as contained in the table scheme
    """

    name: str

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __hash__(self):
        return hash(self.name)

    def get_column_string(self):
        base_repr = f"A.{self.name}" if self.name in COMMON_COLUMNS else self.name
        return base_repr

    def get_column_as_original_name(self):
        column_string = self.get_column_string()
        as_original = f"{column_string} AS {self.name}"
        return as_original


@dataclass
class ArrayColumn(BaseColumn):
    """
    Defines the base properties of a data column which contains arrays

    Attributes:
            unnest (bool): unnest values of the arrays
            element_ind (int): optional. take only specific index from the array
            filter (int): optional. filter value from the array
            sorted (int): optional. sort the array
            sum (bool): optional. sum of the array
            max (bool): optional. max of the array
            min (bool): optional. min of the array
            len (bool): optional. length of the array
            avg (bool): optional. average of the array
    """

    unnest: bool = False
    element_ind: int = None
    filter: str = None
    sorted: bool = False
    sum: bool = False
    max: bool = False
    min: bool = False
    len: bool = False
    avg: bool = False

    def __post_init__(self):
        is_single_element = any([self.sum, self.max, self.min, self.len, self.avg])
        assert not (self.unnest is True and is_single_element is True), "you can't unnest array with single element"
        assert [self.element_ind is not None, self.sum, self.max, self.min, self.len, self.avg].count(
            True
        ) <= 1, "you can't apply multiple aggregation functions to single array"

    def get_column_string(self):
        base_repr = super().get_column_string()
        if self.filter:
            base_repr = f"filter({base_repr}, x -> x {self.filter})"

        if self.sorted:
            base_repr = f"array_sort({base_repr})"

        if self.unnest is True:
            return f"UNNEST({base_repr})"

        if self.element_ind:
            base_repr = f"element_at({base_repr}, {self.element_ind})"
        elif self.sum:
            base_repr = f"array_sum({base_repr})"
        elif self.max:
            base_repr = f"array_max({base_repr})"
        elif self.min:
            base_repr = f"array_min({base_repr})"
        elif self.len:
            base_repr = f"cardinality({base_repr})"
        elif self.avg:
            base_repr = f"array_average({base_repr})"

        return base_repr
