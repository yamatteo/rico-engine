from rich import print

from .actions import GameOver
from .bots.rufus import Rufus
from .bots.quentin import Quentin
from .game import Game


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
            bot.terminate(game)
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally_details()[0] for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break

def cumulative_test(bots, N=1):
    scores = {name: 0 for name in bots.keys()}
    usernames = list(bots.keys())
    for i in range(N):
        game = Game.start(usernames)
        while True:
            try:
                bot = bots[game.expected.name]
                action = bot.decide(game)
                # print("  ", action)
                game.take_action(action)
            except GameOver as reason:
                break
        for bot in bots.values():
            bot.terminate(game)
        for name, town in game.board.towns.items():
            scores[name] += town.tally()
        if (i+1) % 500 == 0:
            print(f"  GAME {i+1} is OVER.")
            for name, score in scores.items():
                print(f"   {name} > {score/(i+1):.3f} points")
        
    print("\nSession is over. Mean scores:")
    # for name, town in game.board.towns.items():
    #     scores[name] += town.tally()
    for name, score in scores.items():
        print(name, ">", score//N, "points")


if __name__ == "__main__":
    bots = {
        "Ad": Quentin("Ad", trader=dict(type="bandit", alpha=1e-3)),
        "Be": Rufus("Be"),
        "Ca": Rufus("Ca"),
        "Da": Rufus("Da"),
    }
    for _ in range(1):
        cumulative_test(bots, N=5000)
    
    bot = bots["Ad"]
    print(bot.trader.action_values)


