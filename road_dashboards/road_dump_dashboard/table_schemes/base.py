from __future__ import annotations

import inspect
from typing import Any, Literal, get_origin, overload

from pypika import Field, Table
from pypika.queries import Selectable
from pypika.terms import Term
from pypika.utils import builder

from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object


class Column(Field):
    def __init__(self, name: str, column_type: type, alias: str | None = None, table: Selectable | None = None) -> None:
        super().__init__(name=name, alias=alias if alias else name, table=table)
        self.type = column_type

    @builder
    def replace_table(self, current_table: Table, new_table: Table) -> Column:
        self.table = new_table if self.table == current_table and self in new_table else self.table


class Base(Table):
    clip_name: Column = Column("clip_name", str)
    grabindex: Column = Column("grabindex", int)
    obj_id: Column = Column("obj_id", int)
    dump_name: Column = Column("dump_name", str)
    population: Column = Column("population", str)
    batch_num: Column = Column("batch_num", int)

    @classmethod
    @overload
    def get_columns_dict(cls, dump_terms: Literal[True] = True, include_all_terms: bool = False) -> dict[str, str]: ...

    @classmethod
    @overload
    def get_columns_dict(
        cls, dump_terms: Literal[False] = True, include_all_terms: bool = False
    ) -> dict[Term, str]: ...

    @classmethod
    @overload
    def get_columns_dict(cls, dump_terms: bool = True, include_all_terms: bool = False) -> dict[str | Term, str]: ...

    @classmethod
    def get_columns_dict(cls, dump_terms: bool = True, include_all_terms: bool = False) -> dict[str | Term, str]:
        cls_term: list[tuple[str, Term]] = inspect.getmembers(
            cls,
            lambda term: isinstance(term, Term)
            and (include_all_terms or get_origin(getattr(term, "type", list[Any])) != list),
        )
        return {dump_object(term) if dump_terms else term: name for name, term in cls_term}

    def __init__(self, table_name: str, dataset_name: str):
        super().__init__(table_name)
        self.dataset_name = dataset_name

    def __getattribute__(self, item: str) -> Any:
        try:
            attr = super().__getattribute__(item)
            return attr.replace_table(current_table=None, new_table=self) if isinstance(attr, Term) else attr
        except AttributeError:
            raise

    def __getattr__(self, item):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __getitem__(self, name: str):
        raise KeyError(name)

    def __contains__(self, item: Column) -> bool:
        try:
            super().__getattribute__(item.alias)
            return True
        except AttributeError:
            return False
