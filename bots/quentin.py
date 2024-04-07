import random
from typing import Optional, Sequence

from .. import Action, Game, GOODS, TraderAction
from .upper_confidence_bound import StorageUCB, TraderUCB


class Quentin:
    """A bot that take some decisions based on reinforcement learning."""

    def __init__(self, name: str, storage: dict = {"type": "random"}, trader: dict = {"type": "random"}):
        self.name = name
        self.storage = quentinStorage(name=name, **storage)
        self.trader = quentinTrader(name=name, **trader)
        self.fallback = QuentinRandom()

    def decide(self, game: Game) -> Action:
        """Given the current game state, decides what action to take."""
        assert self.name == game.expected.name, "Not my turn!"
        if game.expected.type == "storage":
            return self.storage.decide(game)
        elif game.expected.type == "trader":
            return self.trader.decide(game)
        else:
            return self.fallback.decide(game)

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"
        self.storage.terminate(game)
        self.trader.terminate(game)


class QuentinRandom:
    """A bot that take random decisions."""

    def __init__(self, **kwargs):
        pass

    def __str__(self):
        return "QuentinRandom()"

    def decide(self, game: Game) -> Action:
        """Decides randomly among up to 20 random (but acceptable) actions."""
        return random.choice(game.expected.possibilities(game.board, cap=20))

    def terminate(self, game: Game):
        pass


class QuentinTraderBandit:
    def __init__(self, name: str, alpha: float = 0.05, epsilon: float = 0.1, train: bool = True):
        self.name = name  # Name of the player
        self.alpha = alpha  # step-size parameter, it's like the learning rate
        self.epsilon = (
            epsilon  # probability to take random action, to allow exploration
        )
        self.train = train  # Whether to update estimated values

        # Short term memory
        self.last_action = None
        self.last_value = None

        # Estimated reward of selling a good, or not selling anything
        self.action_values = {None: 0} | {good: 0 for good in GOODS}
    
    def __str__(self):
        values =  [f"{value:+.2f}" for value in self.action_values.values() ]
        return f"TraderBandit({str(', ').join(values)})"

    def decide(self, game: Game) -> Action:
        """Decides what good to sell."""
        board = game.board
        expected = game.expected
        choices: Sequence[TraderAction] = expected.possibilities(board)

        # How many points more then the best adversary
        current_value = board.delta_tally(expected.name)

        # Take the best action, with an epsilon probability of random exploratory behavior
        if random.random() < self.epsilon:
            current_action = random.choice(choices)
        else:
            current_action = max(
                choices, key=lambda action: self.action_values.get(action.selected_good)
            )
        
        # Update estimates and remember current choices
        self.update(current_value, current_action)

        return current_action

    def reset(self):
        """Forget about last game."""
        self.last_action = None
        self.last_value = None

    def terminate(self, game: Game):
        """Update estimated values before game is over."""
        board = game.board
        current_value = board.delta_tally(self.name)
        self.update(current_value, None)
        self.reset()

    def update(self, current_value: int, current_action: Optional[TraderAction] = None):
        """Update estimated values considering last action and its effect on the game state."""
        if not self.train:
            return 
        
        if self.last_action is not None:
            selected_good = self.last_action.selected_good

            # The reward of the last action is how much our advantage as increased since we took it
            last_reward = current_value - self.last_value

            # Update the exponential moving average, with smoothing factor self.alpha
            prev_action_value = self.action_values[selected_good]
            self.action_values[selected_good] = prev_action_value + self.alpha * (
                last_reward - prev_action_value
            )
        
        # Remember current state and action for the next update
        self.last_value = current_value
        self.last_action = current_action


def quentinTrader(type: str, **kwargs):
    if type == "bandit":
        return QuentinTraderBandit(**kwargs)
    elif type == "ucb":
        return TraderUCB(**kwargs)
    elif type == "random":
        return QuentinRandom()
    else:
        raise ValueError(f"Unknown type {type}.")

def quentinStorage(type: str, **kwargs):
    if type == "ucb":
        return StorageUCB(**kwargs)
    elif type == "random":
        return QuentinRandom()
    else:
        raise ValueError(f"Unknown type {type}.")


# class QuentinTrader:
#     def __init__(self, epsilon: float = 0.1):
#         self.epsilon = epsilon

#     @staticmethod
#     def get_status(board: Board, town: Town) -> tuple[int, ...]:
#         bonus = (
#             int(town.role == "trader" and not town.spent_role)
#             + int(town.privilege("small_market"))
#             + 2 * int(town.privilege("large_market"))
#         )
#         goods = (
#             int(
#                 town.has(good)
#                 and (town.privilege("office") or board.market.count(good) == 0)
#             )
#             for good in GOODS
#         )
#         return (bonus, *goods)
