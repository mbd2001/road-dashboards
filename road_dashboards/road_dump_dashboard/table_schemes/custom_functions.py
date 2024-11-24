import base64
import pickle as pkl
from typing import Any

import pandas as pd
from pypika.queries import QueryBuilder
from pypika.terms import Function
from road_database_toolkit.athena.athena_utils import query_athena


def dump_object(obj: Any) -> str:
    return base64.b64encode(pkl.dumps(obj)).decode("utf-8")


def load_object(dump_obj: str) -> Any:
    return pkl.loads(base64.b64decode(dump_obj))


def execute(query: QueryBuilder) -> pd.DataFrame:
    results, _ = query_athena(query=str(query), database="run_eval_db")
    return results


def df_to_jump(df: pd.DataFrame):
    return df.to_string(header=False, index=False) + f"\n#format: {' '.join(df.columns)}"


class Round(Function):
    def __init__(self, column, round_to_n_decimal, alias=None):
        super().__init__("ROUND", column, round_to_n_decimal, alias=alias)


class FormatNumber(Function):
    def __init__(self, column, alias=None):
        super().__init__("FORMAT_NUMBER", column, alias=alias)


class Arbitrary(Function):
    def __init__(self, column, alias=None):
        super().__init__("ARBITRARY", column, alias=alias)
