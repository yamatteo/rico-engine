from itertools import product
from typing import Literal, Optional, Sequence

from attr import define

from .. import (BUILD_INFO, BUILDINGS, LARGE_BUILDINGS, Board, Building,
                WorkplaceData)
from .base import Action
from .refuse import RefuseAction
from .terminate import TerminateAction


@define
class BuilderAction(Action):
    building_type: Optional[Building] = None
    extra_person: bool = False
    type: Literal["builder"] = "builder"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.build({self.building_type}{' with worker' if self.extra_person else ''})"

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]

        extra_person_possibilities = (
            [False, True] if town.privilege("hospice") and board.people > 0 else [False]
        )

        type_possibilities: list[Building] = []
        for type in BUILDINGS:
            tier = BUILD_INFO[type]["tier"]
            cost = BUILD_INFO[type]["cost"]
            free_space = town.count_free_build_space()
            required_space = 2 if type in LARGE_BUILDINGS else 1
            quarries_discount = min(tier, town.active_quarries())
            builder_discount = 1 if town.role == "builder" else 0
            price = max(0, cost - quarries_discount - builder_discount)
            if (
                board.unbuilt[type] > 0  # A building of this type is available
                and town.buildings[type].placed == 0  # Town doesn't have it
                and town.money >= price  # Town has enough money
                and free_space >= required_space  # Town has enough space
            ):
                type_possibilities.append(type)

        return [RefuseAction(name=town.name)] + [
            BuilderAction(name=town.name, building_type=type, extra_person=extra)
            for (type, extra) in product(type_possibilities, extra_person_possibilities)
        ]

    def react(action, board: Board):
        town = board.towns[action.name]
        assert action.building_type is not None, f"Action {action} is not complete."

        board.give_building(action.building_type, to=town)
        if action.extra_person:
            assert (
                town.privilege("hospice") and board.people > 0
            ), "Can't ask for extra worker"
            board.people -= 1
            town.buildings[action.building_type] = WorkplaceData(1, 1)

        extra = []
        # Stop for building space
        if town.count_free_build_space() == 0:
            extra.append(
                TerminateAction(
                    name=action.name, reason="Game over: no more real estate."
                )
            )

        return board, extra
