from typing import Sequence, Union
from attr import define, asdict

from ..boards import Board

from .. import ActionType as ActionType


@define
class Action:
    name: str
    type: ActionType
    priority: int

    def possibilities(self, board: Board, **kwargs) -> Sequence["Action"]:
        raise NotImplementedError

    def react(self, board: Board) -> tuple[Board, Sequence["Action"]]:
        raise NotImplementedError

    def responds_to(self, other: "Action") -> bool:
        exact_type = self.type == other.type
        exact_name = self.name == other.name
        complete = all(value is not None for value in asdict(self).values())
        return exact_type and exact_name and complete
        # refusal = self.type == "refuse" and other.type in [
        #     "builder",  # TODO check type
        #     "captain",  # TODO check type
        #     "craftsman",  # TODO check type
        #     "settler",  # TODO check type
        #     "storage",  # TODO check type
        #     "trader",  # TODO check type
        # ]
        # complete_payload = all(
        #     value is not None
        #     for value in asdict(
        #         self, filter=lambda k, v: k.name not in ["type", "name", "priority"]
        #     ).values()
        # )
        # return (exact_type or refusal) and exact_name and complete_payload
