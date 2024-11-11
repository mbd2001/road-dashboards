import uuid
from abc import abstractmethod
from dataclasses import FrozenInstanceError

from dash import html


class GridObject:
    _frozen: bool = False

    """
    Defines the properties of a basic grid object

    Attributes:
            full_grid_row (bool): optional. True if the grid object takes full line in the grid, False otherwise
            component_id (str): optional. Name for this instance of this grid object
    """

    def __init__(self, full_grid_row: bool = False, component_id: str = ""):
        self.full_grid_row = full_grid_row
        self.component_id = component_id or f"{type(self).__name__}_{uuid.uuid4().hex[:6]}"
        self._generate_ids()
        self._frozen = True
        self._callbacks()

    @abstractmethod
    def _generate_ids(self) -> None:
        """Generate the ids for this class"""

    @abstractmethod
    def layout(self) -> html.Div:
        """Defines the layout of this object"""

    @abstractmethod
    def _callbacks(self) -> None:
        """Define the relevant callbacks for this *and only this* class, using this class ids"""

    def _generate_id(self, generic_id: str) -> str:
        return f"{self.component_id}-{generic_id}"

    def __setattr__(self, attr, value):
        if getattr(self, "_frozen", None):
            raise FrozenInstanceError(f"cannot assign to field {attr!r}")
        return super().__setattr__(attr, value)
