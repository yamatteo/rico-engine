import random
from typing import Callable, Optional, Sequence

from .. import Game, Action, Board


class EpsilonGreedyBandit:
    def __init__(
        self,
        name: str,
        projection: Callable,
        alpha: float = 0.01,
        epsilon: float = 0.1,
        init_value: float = 0,
        train: bool = True,
        use_delta: bool = False,
    ):
        self.name = name  # Name of the player
        self.project_action = projection  # Project an action into an hashable tuple
        self.alpha = alpha  # step-size parameter, it's like the learning rate
        self.epsilon = (
            epsilon  # probability to take random action, to allow exploration
        )
        self.init_value = init_value
        self.train = train  # Whether to update estimated values
        self.use_delta = use_delta  # Whether to use points or point deltas as value

        # Short term memory
        self.last_action = None
        self.last_value = None

        # Long term memory
        self.expected_rewards = dict()

    def __repr__(self):
        n = len(self.expected_rewards)
        if n == 0:
            return f"EGB(empty, ε={self.epsilon:1.0e}, α={self.alpha:1.0e})"
        elif n <= 6:
            values = [f"{v:+.2f}" for v in self.expected_rewards.values()]
        else:
            values = [
                min(self.expected_rewards.values()),
                sum(self.expected_rewards.values()) / n,
                max(self.expected_rewards.values()),
            ]
            values = [f"{v:+.2f}" for v in values]
        return (
            f"EGB({str(', ').join(values)}, ε={self.epsilon:1.0e}, α={self.alpha:1.0e})"
        )

    def decide(self, game: Game) -> Action:
        board = game.board
        expected = game.expected
        choices: Sequence[Action] = expected.possibilities(board, cap=20)

        # Calculate current value
        current_value = self.eval_board(board)

        # Take the best action, with an epsilon probability of random exploratory behavior
        if random.random() < self.epsilon:
            current_action = random.choice(choices)
        else:
            current_action = max(choices, key=self.eval_action)

        # Update estimates and remember current choices
        self.update(current_value, current_action)

        return current_action

    def eval_action(self, action: Action) -> float:
        return self.expected_rewards.get(self.project_action(action), self.init_value)
    
    def eval_board(self, board: Board, name: Optional[str] = None) -> float:
        if name is None:
            name = self.name
        if self.use_delta:
            return board.delta_tally(name)
        else:
            return board.towns[name].tally()


    def terminate(self, game: Game):
        """Update estimated values before game is over."""
        board = game.board
        current_value = self.eval_board(board)
        self.update(current_value)
        self.update()

    def update(self, current_value: Optional[float] = None, current_action: Optional[Action] = None):
        if not self.train:
            return

        # Update rewards
        if current_value and self.last_action:
            projection = self.project_action(self.last_action)

            # The reward of the last action is how much our advantage as increased since we took it
            last_reward = current_value - self.last_value

            # Update the exponential moving average, with smoothing factor self.alpha
            prev_action_value = self.expected_rewards.get(projection, self.init_value)
            self.expected_rewards[projection] = prev_action_value + self.alpha * (last_reward - prev_action_value)

        # Remember current state and action for the next update
        self.last_value = current_value
        self.last_action = current_action
