from typing import Literal

from attr import define

from .. import GOODS, Board, ActionType
from .base import Action


@define
class RefuseAction(Action):
    type: Literal["refuse"] = "refuse"
    priority: int = 4

    def __str__(self):
        return f"{self.name}.refuse()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        return board, []
    
    def responds_to(self, other: "Action") -> bool:
        exact_name = self.name == other.name
        refusal_type = other.type in [
            "builder", 
            "captain", 
            "craftsman",  
            "settler", 
            "storage", 
            "trader", 
        ]
        return refusal_type and exact_name
