from copy import deepcopy
import random
from typing import Sequence

from attr import define

from .pseudos import generate_pseudos
from .actions import Action, GovernorAction
from .boards import Board


@define
class Game:
    play_order: list[str]
    actions: Sequence[Action]
    board: Board
    pseudos: dict[str, str]

    @property
    def expected(self) -> Action:
        return self.actions[0]

    @classmethod
    def start(cls, usernames: Sequence[str], shuffle=True):
        assert 3 <= len(usernames) <= 5, "Games are for three to five players."
        pseudos = generate_pseudos(usernames)
        play_order = [ pseudos[name] for name in usernames ]
        if shuffle:
            random.shuffle(play_order)
        board = Board.new(play_order, shuffle_tiles=shuffle)
        actions = [GovernorAction(name=play_order[0])]
        return cls(play_order=play_order, actions=actions, board=board, pseudos=pseudos)
    
    def astuple(self, wrt: str):
        output_tuple = tuple(self.board.asdict().values())
        for town in self.board.town_round_from(wrt):
            output_tuple += tuple(town.asdict().values())
        return output_tuple

    def copy(self) -> "Game":
        return Game(
            play_order=self.play_order,
            actions=deepcopy(self.actions),
            board=deepcopy(self.board),
            pseudos=self.pseudos,
        )


    def drop_and_merge(self, extra: Sequence[Action]):
        actions = self.actions[1: ]
        merged = []
        i, j = 0, 0
        while i < len(actions):
            if j < len(extra) and extra[j].priority > actions[i].priority:
                merged.append(extra[j])
                j += 1
            else:
                merged.append(actions[i])
                i += 1
        while j < len(extra):
            merged.append(extra[j])
            j += 1
        self.actions = merged

    def project(self, action: Action) -> "Game":
        game = deepcopy(self)
        game.take_action(action)
        return game

    def take_action(self, action: Action):
        assert action.responds_to(self.expected)
        self.board, extra = action.react(self.board)
        self.drop_and_merge(extra)
