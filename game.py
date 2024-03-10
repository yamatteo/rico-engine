from copy import deepcopy
import random
from typing import Sequence

from attr import define
from cattrs.preconf.json import make_converter

from .pseudos import generate_pseudos
from .actions import *
from .boards import Board


def custom_action_structure(data, cls) -> Action:
    if data.get("type") == "builder":
        return BuilderAction(**data)
    elif data.get("type") == "captain":
        return CaptainAction(**data)
    elif data.get("type") == "governor":
        return GovernorAction(**data)
    elif data.get("type") == "role":
        return RoleAction(**data)
    elif data.get("type") == "terminate":
        return TerminateAction(**data)
    elif data.get("type") == "craftsman":
        return CraftsmanAction(**data)
    elif data.get("type") == "mayor":
        return MayorAction(**data)
    elif data.get("type") == "settler":
        return SettlerAction(**data)
    elif data.get("type") == "trader":
        return TraderAction(**data)
    else:
        raise ValueError(f"Invalid action type: {data.get('type')}")

game_converter = make_converter()
game_converter.register_structure_hook(Action, custom_action_structure)

@define
class Game:
    play_order: list[str]
    actions: Sequence[Action]
    past_actions: list[Action]
    board: Board
    pseudos: dict[str, str]

    @property
    def expected(self) -> Action:
        return self.actions[0]
    
    @classmethod
    def loads(cls, data: str) -> "Game":
        return game_converter.loads(data, cls)
        # return cattrs.structure(json.loads(data), cls)

    @classmethod
    def start(cls, usernames: Sequence[str], shuffle=True):
        assert 3 <= len(usernames) <= 5, "Games are for three to five players."
        pseudos = generate_pseudos(usernames)
        play_order = [ pseudos[name] for name in usernames ]
        if shuffle:
            random.shuffle(play_order)
        board = Board.new(play_order, shuffle_tiles=shuffle)
        actions = [GovernorAction(name=play_order[0])]
        return cls(play_order=play_order, actions=actions, board=board, pseudos=pseudos, past_actions=[])
    
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
            past_actions=deepcopy(self.past_actions)
        )
    
    def dumps(self) -> str:
        return game_converter.dumps(self)
        # return json.dumps(cattrs.unstructure(self))


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
        self.past_actions.append(action)
        self.drop_and_merge(extra)
    
    def current_round(self):
        wrt = self.board.get_governor_name() or self.expected.name
        return self.board.town_round_from(wrt)
