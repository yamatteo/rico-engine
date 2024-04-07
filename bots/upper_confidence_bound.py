import math
import statistics
from typing import Optional, Sequence
from .. import Game, GOODS
from ..actions import *


class StorageUCB:
    def __init__(
        self, name: str, alpha: float = 0.01, c: float = 1, train: bool = True
    ):
        self.name = name  # Name of the player
        self.alpha = alpha  # step-size parameter, it's like the learning rate
        self.c = c  # Degree of exploration
        self.train = train  # Whether to update estimated values

        # Short term memory
        self.last_action = None
        self.last_value = None

        # Long term memory
        self.expected_rewards = dict()
        self.occurrences = dict()  # Count how many times an action has been chosen
        self.global_counter = 0  # Count how many decisions have been taken

    def __str__(self):
        null_q = self.expected_rewards.get((0, 0, 0, 0), 0)
        other_qs = [
            value for key, value in self.expected_rewards.items() if key != (0, 0, 0, 0)
        ]
        if other_qs:
            mean = statistics.mean(other_qs)
            std_dev = statistics.stdev(other_qs)
            return f"StorageUCB({null_q:+.2f}, {mean:+.2f} ± {2*std_dev:.2f})"
        else:
            return f"StorageUCB({null_q:+.2f}, None)"

    def decide(self, game: Game) -> Action:
        """Decides what good to store."""
        board = game.board
        expected = game.expected
        choices: Sequence[StorageAction] = expected.possibilities(board)

        self.global_counter += 1

        # How many points more then the best adversary
        current_value = board.delta_tally(expected.name)

        # Select the next action
        current_action = max(choices, key=self.evaluate_action)

        # Update estimates and remember current choices
        self.update(current_value, current_action)

        return current_action

    def evaluate_action(self, action: StorageAction) -> float:
        """The value of an action is its expected reward plus *something*.

        Each time an action is not chosen self.global_counter increase but
        self.occurrences (for that action) does not. In this way, each action
        that is not optimal is guaranteed to selected, eventually, infinitely
        many times, but with decreasing frequency (because of the log) and
        somewhat proportionally to its proximity to the optimal action.
        """
        projected_action = self.project_action(action)
        occurrences = self.occurrences.get(projected_action, 0) + 1
        return (
            self.expected_rewards.get(projected_action, 0)
            + self.c * (math.log(self.global_counter) / occurrences) ** 0.5
        )

    @staticmethod
    def project_action(action: StorageAction) -> tuple[int, ...]:
        """Project any StorageAction into a 4-tuple of integers between 0 and 5.

        Irrelevant information, like if some good is stored in the large or
        small warehouse, is removed.
        """
        trans = {None: 0} | {good: i + 1 for i, good in enumerate(GOODS)}
        fully_conserved = sorted(
            map(
                trans.get,
                (
                    action.large_warehouse_first_good,
                    action.large_warehouse_second_good,
                    action.small_warehouse_good,
                ),
            )
        )
        return (*fully_conserved, trans[action.selected_good])

    def reset(self):
        """Forget about last game."""
        self.last_action = None
        self.last_value = None

    def terminate(self, game: Game):
        """Update expected rewards before game is over."""
        board = game.board
        current_value = board.delta_tally(self.name)
        self.update(current_value, None)
        self.reset()

    def update(
        self, current_value: int, current_action: Optional[StorageAction] = None
    ):
        """Update expected rewards considering last action and its effect on the game state."""
        if not self.train:
            return

        if self.last_action is not None:
            projected_action = self.project_action(self.last_action)

            # The reward of the last action is how much our advantage as increased since we took it
            last_reward = current_value - self.last_value

            # Update the exponential moving average, with smoothing factor self.alpha
            previous_expected_reward = self.expected_rewards.get(projected_action, 0)
            self.expected_rewards[projected_action] = (
                previous_expected_reward
                + self.alpha * (last_reward - previous_expected_reward)
            )

        # Increase occurrences
        if current_action:
            projected_action = self.project_action(current_action)
            self.occurrences[projected_action] = (
                self.occurrences.get(projected_action, 0) + 1
            )

        # Remember current state and action for the next update
        self.last_value = current_value
        self.last_action = current_action




class TraderUCB:
    def __init__(
        self, name: str, alpha: float = 0.01, c: float = 1, train: bool = True
    ):
        self.name = name  # Name of the player
        self.alpha = alpha  # step-size parameter, it's like the learning rate
        self.c = c  # Degree of exploration
        self.train = train  # Whether to update estimated values

        # Short term memory
        self.last_action = None
        self.last_value = None

        # Long term memory
        self.expected_rewards = dict()
        self.occurrences = dict()  # Count how many times an action has been chosen
        self.global_counter = 0  # Count how many decisions have been taken

    def __str__(self):
        expected_rewards = [ f"{value:+.2f}" for value in self.expected_rewards.values() ]

        return f"TraderUCB({str(', ').join(expected_rewards)})"

    def decide(self, game: Game) -> TraderAction:
        """Decides what good to sell."""
        board = game.board
        expected = game.expected
        choices: Sequence[StorageAction] = expected.possibilities(board)

        self.global_counter += 1

        # How many points more then the best adversary
        current_value = board.delta_tally(expected.name)

        # Select the next action
        current_action = max(choices, key=self.evaluate_action)

        # Update estimates and remember current choices
        self.update(current_value, current_action)

        return current_action

    def evaluate_action(self, action: TraderAction) -> float:
        """The value of an action is its expected reward plus *something*.

        Each time an action is not chosen self.global_counter increase but
        self.occurrences (for that action) does not. In this way, each action
        that is not optimal is guaranteed to selected, eventually, infinitely
        many times, but with decreasing frequency (because of the log) and
        somewhat proportionally to its proximity to the optimal action.
        """
        projected_action = self.project_action(action)
        occurrences = self.occurrences.get(projected_action, 0) + 1
        return (
            self.expected_rewards.get(projected_action, 0)
            + self.c * (math.log(self.global_counter) / occurrences) ** 0.5
        )

    @staticmethod
    def project_action(action: TraderAction) -> tuple[int, ...]:
        """Project any TraderAction into a 1-tuple of int between 0 and 5."""
        trans = {None: 0} | {good: i + 1 for i, good in enumerate(GOODS)}
        return (trans[action.selected_good], )

    def reset(self):
        """Forget about last game."""
        self.last_action = None
        self.last_value = None

    def terminate(self, game: Game):
        """Update expected rewards before game is over."""
        board = game.board
        current_value = board.delta_tally(self.name)
        self.update(current_value, None)
        self.reset()

    def update(
        self, current_value: int, current_action: Optional[TraderAction] = None
    ):
        """Update expected rewards considering last action and its effect on the game state."""
        if not self.train:
            return

        if self.last_action is not None:
            projected_action = self.project_action(self.last_action)

            # The reward of the last action is how much our advantage as increased since we took it
            last_reward = current_value - self.last_value

            # Update the exponential moving average, with smoothing factor self.alpha
            previous_expected_reward = self.expected_rewards.get(projected_action, 0)
            self.expected_rewards[projected_action] = (
                previous_expected_reward
                + self.alpha * (last_reward - previous_expected_reward)
            )

        # Increase occurrences
        if current_action:
            projected_action = self.project_action(current_action)
            self.occurrences[projected_action] = (
                self.occurrences.get(projected_action, 0) + 1
            )

        # Remember current state and action for the next update
        self.last_value = current_value
        self.last_action = current_action

