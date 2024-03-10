from typing import Literal, Sequence

from attr import define
from .terminate import TerminateAction

from .. import Board

from .base import Action

@define
class TidyUpAction(Action):
    type: Literal["tidyup"] = "tidyup"
    priority: int = 3

    def __str__(self):
        return f"{self.name}.tidyup()"

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        extra = []

        # Check if enough tiles are revealed
        if len(board.exposed_tiles) <= len(board.towns):
            board.expose_tiles()
        
        # Check ships and market
        board.empty_ships_and_market()
        
        # Eventually refill people_ship
        if board.people_ship <= 0:
            total_jobs = sum(town.count_vacant_building_jobs() for town in board.towns.values())
            total_jobs = max(total_jobs, len(board.towns))  # At least one per player
            if board.count("people") >= total_jobs:
                board.people_ship = board.pop("people", total_jobs)
            else:
                extra.append(TerminateAction(name=action.name, reason="No more people."))
        
        # Check that there are points left
        if board.points <= 0:
            extra.append(TerminateAction(name=action.name, reason="No more points."))

        return board, extra
    
    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        return [self]
