from rich import print

from .game import Game, GameOver
from .bots.pablo import Pablo
from .bots.quentin import Quentin
from .bots.rufus import Rufus


def single_game(bots):
    usernames = list(bots.keys())
    game = Game.start(usernames)
    while True:
        try:
            bot = bots[game.expected.name]
            action = bot.decide(game)
            game.take_action(action)
        except GameOver:
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
    N = 10000
    M = 10
    P = 1000
    bots = {
        "Ad": Pablo("Ad", alpha=0.01, epsilon=0.1, state_space_dim=1, action_space_dim=1024),
        "Be": Quentin("Be"),
        "Ca": Rufus("Ca"),
        "Da": Rufus("Da"),
    }

    usernames = list(bots.keys())
    cumulative_scores = {name: 0 for name in usernames}
    i = 0
    for n in range(N):
        scores = single_game(bots)

        for name in usernames:
            cumulative_scores[name] += scores[name]

        # # Single score accumulation
        # if (n+1)%P == 0:
        #     print(f" ROUND {n+1}:")
        #     for name, score in cumulative_scores.items():
        #         print(f"   {name} > {score/n:.3f} points")
        #     print()

        # Piecewise score accumulation
        if (n+1)%P == 0:
            i += 1
            print(f" ROUND {n+1}:")
            for name, score in cumulative_scores.items():
                print(f"   {name} > {score/P:.3f} points")
            print()
            cumulative_scores = {name: 0 for name in usernames}
            # old_bot = bots["Ad"]
            # bots["Ad"] = Pablo("Ad", alpha=0.01, epsilon=max(0.1, 1-0.1*i), state_space_dim=2 ** i, action_space_dim=1024)
            # bots["Ad"].learn_from(old_bot)

    print(f"SESSION is OVER.")

