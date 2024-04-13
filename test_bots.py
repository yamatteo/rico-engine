from rich import print

from .game import Game, GameOver
from .bots.rufus import Rufus
from .bots.quentin import Quentin


def single_game(bots, print_internals=False):
    usernames = list(bots.keys())
    game = Game.start(usernames)
    while True:
        try:
            bot = bots[game.expected.name]
            action = bot.decide(game)
            game.take_action(action)
        except GameOver:
            if print_internals:
                print(f"  Round {m+1}. Bots internals:")
                print(bots["Ad"].parts)
            break
    for bot in bots.values():
        bot.terminate(game)
    return { name: town.tally() for name, town in game.board.towns.items() }

def many_games(bots, N, m):
    usernames = list(bots.keys())
    cumulative_scores = {name: 0 for name in usernames}
    for n in range(N):
        scores = single_game(bots, print_internals=(n+1 == N))
        for name in usernames:
            cumulative_scores[name] += scores[name]
    print(f"  GAME {N*m + n + 1} is OVER.")
    for name, score in cumulative_scores.items():
        print(f"   {name} > {score/N:.3f} points")
    print()
    return cumulative_scores




if __name__ == "__main__":
    N = 100
    M = 5
    bots = {
        "Ad": Quentin("Ad", use_delta=True, alpha=1e-3, epsilon=0.01),
        "Be": Quentin("Be", alpha=1e-3),
        "Ca": Quentin("Ca"),
        "Da": Rufus("Da"),
    }
    usernames = list(bots.keys())
    cumulative_scores = {name: 0 for name in usernames}
    for m in range(M):
        scores = many_games(bots, N=N, m=m)
        for name in usernames:
            cumulative_scores[name] += scores[name]
    print(f"SESSION is OVER.")
    print({ action_type: egb.expected_rewards for action_type, egb in bots["Ad"].parts.items() })


