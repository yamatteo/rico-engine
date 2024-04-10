import random
from typing import Optional, Sequence

from .. import *
from .upper_confidence_bound import UpperConfidenceBound
from .epsilon_greedy_bandit import EpsilonGreedyBandit


def project_action(action: Action) -> tuple:
    if action.type == "role":
        return (action.role,)
    elif action.type == "builder":
        return (action.building_type, action.extra_person)
    elif action.type == "captain":
        return (action.selected_ship, action.selected_good)
    elif action.type == "craftsman":
        return (action.selected_good,)
    elif action.type == "mayor":
        dist = PeopleDistribution(action.people_distribution)
        production = [dist.get_privilege(good) for good in GOODS]
        privileges = [dist.get_privilege(building) for building in NONPROD_BUILDINGS]
        return (*production, *privileges)
    elif action.type == "settler":
        return (action.tile, action.extra_person, action.down_tile)
    elif action.type == "storage":
        fully_conserved = sorted(
            (
                action.large_warehouse_first_good or "None",
                action.large_warehouse_second_good or "None",
                action.small_warehouse_good or "None",
            )
        )
        return (*fully_conserved, action.selected_good)
    elif action.type == "trader":
        return (action.selected_good,)
    else:
        return tuple()


class Quentin:
    """A bot that take decisions based on reinforcement learning."""

    def __init__(self, name: str):
        self.name = name
        self.parts = {
            action_type: EpsilonGreedyBandit(name=name, projection=project_action, init_value=5.0)
            for action_type in ACTIONS
        }

    def decide(self, game: Game) -> Action:
        """Given the current game state, decides what action to take."""
        assert self.name == game.expected.name, "Not my turn!"

        return self.parts[game.expected.type].decide(game)

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"
        for part in self.parts.values():
            part.terminate(game)
