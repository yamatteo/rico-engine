from typing import Literal, Sequence

from attr import define

from .. import Board

from .base import Action
from .role import RoleAction
from .terminate import TerminateAction


@define
class GovernorAction(Action):
    type: Literal["governor"] = "governor"
    priority: int = 0

    def __str__(self):
        return f"{self.name}.governor()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        board.set_governor(action.name)
        extra = [RoleAction(name=name) for name in board.round_from(action.name)]
        extra += [GovernorAction(name=board.next_to(action.name))]
        
        if not board.is_end_of_round():
            # Game just started, nothing else to do
            return board, extra

        # Increase money bonus of unchosen roles
        if board.money >= 3:
            board.reset_roles()
        else:
            return board, [ TerminateAction(name=action.name, reason="Not enough money for roles.")]

        return board, extra
