from rich import print

from .actions.terminate import GameOver
from .bots.rufus import Rufus
from .game import Game


def test_mixed(bots):
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
    bots = {
        "Ad": Rufus("Ad"),
        "Be": Rufus("Be"),
        "Ca": Rufus("Ca"),
        "Da": Rufus("Da"),
    }
    test_mixed(bots)


