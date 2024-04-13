# import math
# import statistics
# import numpy as np
# import tinygrad
# from typing import Optional, Sequence
# from .. import Game, GOODS
# from ..actions import *


# class CaptainSGB:
#     def __init__(
#         self, name: str, num_player: int, alpha: float = 0.01, train: bool = True
#     ):
#         self.name = name  # Name of the player
#         self.alpha = alpha  # step-size parameter, it's like the learning rate
#         self.train = train  # Whether to update estimated values
#         self.smallest_ship_size = num_player + 1

#         # Short term memory
#         self.last_action = None
#         self.last_value = None
#         self.last_weights = None

#         # Long term memory
#         self.average_reward = 0
#         self.preferences = [0] * (1 + 3 * 5)
#         # Three possible ship times five possible goods, plus no shipment.

#     def __str__(self):
#         preferences = [f"{p:.1f}" for p in self.preferences]
#         return (
#             f"CaptainSGB(ar={self.average_reward:+.1f}, {str(', ').join(preferences)})"
#         )

#     def decide(self, game: Game) -> CaptainAction:
#         """Decides what good to load."""
#         board = game.board
#         expected = game.expected

#         choices: Sequence[CaptainAction] = expected.possibilities(board)
#         projections = {self.project_action(action): action for action in choices}
#         preferences = tinygrad.Tensor(
#             [
#                 self.preferences[i] if i in projections.keys() else -np.inf
#                 for i in range(16)
#             ]
#         )
#         weights=preferences.softmax().numpy()

#         # How many points more then the best adversary
#         current_value = board.delta_tally(expected.name)

#         # Select the next action
#         current_action = projections[random.choices(range(16), weights=weights)[0]]

#         # Update estimates and remember current choices
#         self.update(current_value, current_action, weights)

#         return current_action

#     def project_action(self, action: CaptainAction) -> int:
#         """Project any CaptainAction into an integer between 0 and 15."""
#         if action.selected_ship is None or action.selected_good is None:
#             return 0
#         ship_size = action.selected_ship - self.smallest_ship_size
#         good = GOODS.index(action.selected_good)
#         return 5*ship_size + good + 1

#     def reset(self):
#         """Forget about last game."""
#         self.last_action = None
#         self.last_value = None
#         self.last_weights = None

#     def terminate(self, game: Game):
#         """Update expected rewards before game is over."""
#         board = game.board
#         current_value = board.delta_tally(self.name)
#         self.update(current_value, None)
#         self.reset()

#     def update(
#         self, current_value: int, current_action: Optional[StorageAction] = None, current_weights = None
#     ):
#         """Update expected rewards considering last action and its effect on the game state."""
#         if not self.train:
#             return

#         if self.last_action is not None:
#             projected_action = self.project_action(self.last_action)

#             # The reward of the last action is how much our advantage as increased since we took it
#             last_reward = current_value - self.last_value

#             # Update the average reward, with smoothing factor self.alpha
#             self.average_reward = (
#                 self.average_reward
#                 + self.alpha * (last_reward - self.average_reward)
#             )

#             # Update preferences
#             for i in range(16):
#                 if i == projected_action:
#                     self.preferences[i] = self.preferences[i] + self.alpha * (last_reward - self.average_reward) * (1 - self.last_weights[i]) 
#                 else:
#                     self.preferences[i] = self.preferences[i] - self.alpha * (last_reward - self.average_reward) * self.last_weights[i]

#         # Remember current state and action for the next update
#         self.last_value = current_value
#         self.last_action = current_action
#         self.last_weights = current_weights
