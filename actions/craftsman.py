from typing import Literal, Optional, Sequence

from attr import define

from .. import GOODS, Good, Board

from .base import Action
from .refuse import RefuseAction


@define
class CraftsmanAction(Action):
    selected_good: Optional[Good] = None
    type: Literal["craftsman"] = "craftsman"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.supercraft({self.selected_good})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        good = action.selected_good
        town = board.towns[action.name]
        assert good is not None, "Action is not complete."
        assert town.production(good) > 0, f"Craftsman get one extra good of something he produces, not {good}."

        assert board.has(good), f"There is no {good} left in the game."
        board.give(1, good, to=town)
        return board, []

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        actions = list()
        for selected_good in GOODS:
            if town.production(selected_good) > 0 and board.has(selected_good):
                actions.append(
                    CraftsmanAction(name=town.name, selected_good=selected_good)
                )
        actions.append(RefuseAction(name=town.name))
        return actions
