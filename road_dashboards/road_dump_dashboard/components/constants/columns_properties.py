from dataclasses import dataclass, field
from typing import ClassVar, List

BASE_COLUMNS = ["population", "dump_name", "clip_name", "grabindex", "obj_id", "batch_num"]


@dataclass
class Column:
    """
    Defines the base properties of a data column

    Attributes:
            name (str): the name of the column, as contained in the table scheme
    """

    name: str
    distinct_values: List[str] = field(default_factory=list)
    options: ClassVar = {}

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def get_column_string(self):
        base_repr = f"A.{self.name}" if self.name in BASE_COLUMNS else self.name
        return base_repr

    def get_column_as_original_name(self):
        column_string = self.get_column_string()
        as_original = f"{column_string} AS {self.name}"
        return as_original

    def title(self):
        return self.name.replace("_", " ").title()


@dataclass(eq=False)
class ArrayColumn(Column):
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
    round_n_decimal_place: int = None

    def __post_init__(self):
        is_single_element = any([self.sum, self.max, self.min, self.len, self.avg])
        assert not (self.unnest and is_single_element), "you can't unnest array with single element"
        assert [self.element_ind is not None, self.sum, self.max, self.min, self.len, self.avg].count(
            True
        ) <= 1, "you can't apply multiple aggregation functions to single array"

    def get_column_string(self):
        base_repr = super().get_column_string()
        if self.round_n_decimal_place is not None:
            base_repr = f"transform({base_repr}, x -> round(x, {self.round_n_decimal_place}))"

        if self.filter:
            base_repr = f"filter({base_repr}, x -> x {self.filter})"

        if self.sorted:
            base_repr = f"array_sort({base_repr})"

        if self.unnest:
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


@dataclass(eq=False)
class NumericColumn(Column):
    """
    Defines the base properties of a data column which contains floats

    Attributes:
            abs (bool): absolute value
            sign (bool): 1 if positive, -1 if negative, 0 else
            round_n_decimal_place (int): the number of decimal places to round to
            floor (bool): floor the value to the nearest integer
            ceil (bool): ceil the value to the nearest integer
    """

    abs: bool = False
    sign: bool = False
    round_n_decimal_place: int = None
    floor: bool = False
    ceil: bool = False
    options: ClassVar = {
        ">": "Greater",
        ">=": "Greater or equal",
        "<": "Less",
        "<=": "Less or equal",
        "=": "Equal",
        "<>": "Not Equal",
        "IS NULL": "Is NULL",
        "IS NOT NULL": "Is not NULL",
    }

    def __post_init__(self):
        assert [self.round_n_decimal_place is not None, self.floor, self.ceil].count(
            True
        ) <= 1, "don't use multiple rounding function"

    def get_column_string(self):
        base_repr = super().get_column_string()
        if self.round_n_decimal_place is not None:
            base_repr = f"round({base_repr}, {self.round_n_decimal_place})"
        elif self.floor:
            base_repr = f"floor({base_repr})"
        elif self.ceil:
            base_repr = f"ceil({base_repr})"

        if self.abs:
            base_repr = f"abs({base_repr})"

        if self.sign:
            base_repr = f"sign({base_repr})"

        return base_repr


@dataclass(eq=False)
class StringColumn(Column):
    """
    Defines the base properties of a data column which contains floats

    """

    len: bool = False
    lower: bool = False
    upper: bool = False
    options: ClassVar = {
        "=": "Equal",
        "<>": "Not Equal",
        "IS NULL": "Is NULL",
        "IS NOT NULL": "Is not NULL",
        "LIKE": "Like",
        "In": "IN",
        "Not In": "NOT IN",
    }

    def __post_init__(self):
        assert [self.lower, self.upper, self.len].count(True) <= 1, "unclear string manipulation"

    def get_column_string(self):
        base_repr = super().get_column_string()
        if self.len:
            return f"length({base_repr})"

        if self.lower:
            return f"lower({base_repr})"

        if self.upper:
            return f"upper({base_repr})"

        return base_repr


@dataclass(eq=False)
class BoolColumn(Column):
    """
    Defines the base properties of a data column which contains floats

    """

    distinct_values: List = field(default_factory=list["TRUE", "FALSE"])
    neg: bool = False
    options: ClassVar = {
        "=": "Equal",
        "<>": "Not Equal",
        "IS NULL": "Is NULL",
        "IS NOT NULL": "Is not NULL",
    }

    def get_column_string(self):
        base_repr = super().get_column_string()
        if self.neg:
            return f"NOT {base_repr}"

        return base_repr


@dataclass
class Case:
    name: str
    filter: str
    extra_columns: List[Column]

    def get_case_string(self):
        case_string = f"WHEN ({self.filter}) THEN '{self.name}'"
        return case_string
