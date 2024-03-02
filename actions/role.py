from typing import Literal, Optional, Sequence

from attr import define

from .. import ROLES, Board, Role
from .base import Action
from .builder import BuilderAction
from .captain import CaptainAction
from .craftsman import CraftsmanAction
from .mayor import MayorAction
from .settler import SettlerAction
from .storage import StorageAction
from .terminate import TerminateAction
from .tidyup import TidyUpAction

from .trader import TraderAction






@define
class RoleAction(Action):
    role: Optional[Role] = None
    type: Literal["role"] = "role"
    priority: int = 2

    def __str__(self):
        return f"{self.name}.take_role({self.role})"

    def possibilities(self, board: Board, **kwargs) -> list["RoleAction"]:
        return [
            RoleAction(name=self.name, role=role)
            for role, data in board.roles.items()
            if data.available 
        ]

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        town = board.towns[action.name]
        role = action.role

        assert role is not None, f"{action!r} is not complete."
        assert town.role is None, f"Player {town.name} already has role ({town.role})."
        

        board.give_role(role, to=town)
        extra: Sequence[Action] = []

        if role == "settler":
            extra = [
                SettlerAction(name=name) for name in board.round_from(town.name)
            ] + [TidyUpAction(name=action.name)]
        elif role == "mayor":
            if board.has("people"):
                board.give(1, "people", to=town)
            while board.people_ship:
                for some_town in board.town_round_from(town.name):
                    if board.people_ship > 0:
                        board.people_ship -= 1
                        some_town.people += 1
                    else:
                        break

            extra.extend(MayorAction(name=name) for name in board.round_from(town.name))
            extra.append(TidyUpAction(name=action.name))

        elif role == "builder":
            extra = [BuilderAction(name=name) for name in board.round_from(town.name)]
        elif role == "craftsman":
            for some_town in board.town_round_from(town.name):
                for good, amount in some_town.production().items():
                    possible_amount = min(amount, board.count(good))
                    board.give(possible_amount, good, to=some_town)
            extra = [CraftsmanAction(name=town.name)]
        elif role == "trader":
            extra = [
                TraderAction(name=name) for name in board.round_from(town.name)
            ] + [TidyUpAction(name=action.name)]
        elif role == "captain":
            extra = (
                [CaptainAction(name=name) for name in board.round_from(town.name)]
                + [StorageAction(name=name) for name in board.round_from(town.name)]
                + [TidyUpAction(name=action.name)]
            )
        elif role in ["prospector1", "prospector2"]:
            if board.has("money"):
                board.give(1, "money", to=town)
                extra = []
            if board.count("money") <= 0:
                extra = [TerminateAction(name=action.name, reason="No more money.")]

        return board, extra
