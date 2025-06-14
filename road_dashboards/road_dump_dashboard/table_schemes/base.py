from __future__ import annotations

import inspect
from typing import Literal, get_origin, overload

from pypika import Field, Table
from pypika.queries import Selectable
from pypika.terms import BasicCriterion, Criterion, Term
from pypika.utils import builder


class Column(Field):
    def __init__(
        self,
        name: str,
        column_type: type,
        drawable: bool = False,
        alias: str | None = None,
        table: Selectable | None = None,
        ignore: Criterion | None = None,
    ) -> None:
        super().__init__(name=name, alias=alias if alias else name, table=table)
        self.type = column_type
        self.drawable = drawable
        self.ignore = ignore

    @builder
    def replace_table(self, current_table: Table, new_table: Table) -> Column:
        self.table = new_table if self.table == current_table and self in new_table else self.table

    def contains(self, expr: str) -> "BasicCriterion":
        return self.like(f"%{expr}%")

    def startswith(self, expr: str) -> "BasicCriterion":
        return self.like(f"{expr}%")

    def endswith(self, expr: str) -> "BasicCriterion":
        return self.like(f"%{expr}")


class Base(Table):
    clip_name: Column = Column("clip_name", str, drawable=True)
    grabindex: Column = Column("grabindex", int, drawable=True)
    obj_id: Column = Column("obj_id", int, drawable=True)
    dump_name: Column = Column("dump_name", str, drawable=True)
    population: Column = Column("population", str)

    @classmethod
    @overload
    def get_columns(
        cls, names_only: Literal[True] = True, include_list_columns: bool = False, only_drawable: bool = False
    ) -> list[str]: ...

    @classmethod
    @overload
    def get_columns(
        cls, names_only: Literal[False] = True, include_list_columns: bool = False, only_drawable: bool = False
    ) -> list[Column]: ...

    @classmethod
    @overload
    def get_columns(
        cls, names_only: bool = True, include_list_columns: bool = False, only_drawable: bool = False
    ) -> list[str | Column]: ...

    @classmethod
    def get_columns(
        cls, names_only: bool = True, include_list_columns: bool = False, only_drawable: bool = False
    ) -> list[str | Column]:
        cls_columns: list[tuple[str, Column]] = inspect.getmembers(
            cls,
            lambda column: isinstance(column, Column)
            and (include_list_columns or get_origin(column.type) != list)
            and (not only_drawable or (only_drawable and column.drawable)),
        )
        return [column.name if names_only else column for _, column in cls_columns]

    def __init__(self, table_name: str, dataset_name: str):
        super().__init__(table_name)
        self.dataset_name = dataset_name

    def __getattribute__(self, item: str) -> any:
        try:
            attr = super().__getattribute__(item)
            return attr.replace_table(current_table=None, new_table=self) if isinstance(attr, Term) else attr
        except AttributeError:
            raise

    def __getattr__(self, item):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __getitem__(self, name: str):
        raise KeyError(name)

    def __contains__(self, item: Term) -> bool:
        try:
            super().__getattribute__(item.alias)
            return True
        except AttributeError:
            return False
