from rich import print as pprint

from .actions import GameOver
from .bots.rufus import Rufus
from .bots.quentin import Quentin
from .game import Game

def one_game_worth_of_data():
    bots = {
        "Ad": Quentin("Ad"),
        "Be": Quentin("Be"),
        "Ca": Quentin("Ca"),
        "Da": Quentin("Da"),
    }
    usernames = list(bots.keys())
    game = Game.start(usernames)
    data = []

    while True:
        try:
            name = game.expected.name
            bot = bots[name]
            board = game.board
            town = board.towns[name]
            inputs = list(board.asdict().values())
            for town in board.town_round_from(name):
                inputs.extend(town.asdict().values())

            # outputs = town.tally_details()
            # # Some sanity checks
            # assert outputs[0] == sum(outputs[1:])
            # assert outputs[1] == inputs[10] + 2*inputs[11] + 4*inputs[12] + 8*inputs[13] + 16*inputs[14] + 32*inputs[15] + 64*inputs[16]
            
            data.append((name, tuple(inputs)))
            action = bot.decide(game)
            pprint(action)
            game.take_action(action)
        except GameOver as reason:
            # print("GAME OVER.", reason)
            scores = {town.name: town.tally_details()[0] for town in game.board.towns.values()}
            print(
                "Game over.",
                ", ".join(f"{name}:{score}" for name, score in scores.items()),
            )
            break
    data = { state: scores[name] for name, state in data }
    return data


def manual_test_mixed(bots):
    usernames = list(bots.keys())
    game = Game.start(usernames)
    while True:
        try:
            bot = bots[game.expected.name]
            action = bot.decide(game)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally_details()[0] for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


if __name__ == "__main__":
    # bots = {
    #     "Ad": Quentin("Ad"),
    #     "Be": Quentin("Be"),
    #     "Ca": Quentin("Ca"),
    #     "Da": Quentin("Da"),
    # }
    # manual_test_mixed(bots)
    print(one_game_worth_of_data())


