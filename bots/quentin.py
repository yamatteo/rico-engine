from collections import namedtuple
from random import choice, random
from typing import overload

from .. import Game, Board, Town, Action

from .direct_estimator import straight_board_estimator


Evaluated = namedtuple("Evaluated", ["action", "value"])


class Quentin:
    def __init__(self, name: str, estimator=straight_board_estimator, temperature=0):
        self.name = name
        self.estimator = estimator
        self.temperature = temperature

    def decide(self, game: Game) -> Action:
        expected = game.expected
        board = game.board

        if expected.type == "mayor":
            choices = expected.possibilities(board, cap=20)
        else:
            choices = expected.possibilities(board)
        
        if random() < self.temperature:
            return choice(choices)

        best_action = choices[0]
        best_value = None
        for action in choices:
            p_game = game.project(action)
            value = self.estimator(p_game.board, wrt=self.name)
            
            if best_value is None or value > best_value:
                best_action = action
                best_value = value
        return best_action
