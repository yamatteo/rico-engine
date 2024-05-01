from .. import *
from hashlib import md5


class Pablo:
    """A bot that take decisions based on reinforcement learning, with some variation of Monte Carlo methods."""


    def __init__(
        self,
        name: str,
        # use_delta: bool = False,
        alpha: Optional[float] = None,
        epsilon: float = 0.1,
        action_space_dim = 16,
        reward_window = 1,
        state_space_dim = 16,
    ):
        self.name = name
        self.episode = []
        self.value_memory = 0
        self.action_memory = None
        self.reward_window = reward_window
        self.state_memory = None

        self.sah_values: dict[tuple[int, int], float] = dict()
        self.sah_counts: dict[tuple[int, int], int] = dict()

        self.state_space_dim = state_space_dim
        self.action_space_dim = action_space_dim

        self.alpha = alpha
        self.epsilon = epsilon
        # self.gamma = 0.99

    def decide(self, game: Game) -> Action:
        """Given the current game state, decides what action to take."""
        assert self.name == game.expected.name, "Not my turn!"

        board = game.board
        expected = game.expected

        state_hash = self.hash_state(game)

        choices: Sequence[Action] = expected.possibilities(board, cap=40)

        def eval_action(action: Action) -> float:
            return self.sah_values.get((state_hash, self.hash_action(action)), 0)

        # Take the best action, with an epsilon probability of random exploratory behavior
        if random.random() < self.epsilon:
            action = random.choice(choices)
        else:
            action = max(choices, key=eval_action)

        self.episode.append((state_hash, self.hash_action(action), game.board.towns[self.name].tally()))

        return action
    
    def hash_action(self, action: Action):
        data = str().join(map(str, self.project_action(action))).encode("utf8")
        return int.from_bytes(md5(data).digest(), byteorder="little") % self.action_space_dim
    
    def hash_state(self, game: Game):
        town_dict = game.board.towns[self.name].asdict_integers()
        data = str().join(map(str, town_dict.values())).encode("utf8")
        return int.from_bytes(md5(data).digest(), byteorder="little") % self.state_space_dim

    def project_state(self, game: Game):
        town_dict = game.board.towns[self.name].asdict_integers()
        return tuple(town_dict.values())

    def project_action(self, action: Action):
        if action.type == "role":
            return (
                action.type,
                action.role,
            )
        elif action.type == "builder":
            return (action.type, action.building_type, action.extra_person)
        elif action.type == "captain":
            return (action.type, action.selected_ship, action.selected_good)
        elif action.type == "craftsman":
            return (
                action.type,
                action.selected_good,
            )
        elif action.type == "mayor":
            dist = PeopleDistribution(action.people_distribution)
            production = [dist.get_production(good) for good in GOODS]
            quarries = dist.get_privilege("quarry_tile")
            privileges = [
                dist.get_privilege(building) for building in NONPROD_BUILDINGS
            ]
            return (action.type, *production, quarries, *privileges)
        elif action.type == "settler":
            return (action.type, action.tile, action.extra_person, action.down_tile)
        elif action.type == "storage":
            fully_conserved = sorted(
                (
                    action.large_warehouse_first_good or "None",
                    action.large_warehouse_second_good or "None",
                    action.small_warehouse_good or "None",
                )
            )
            return (action.type, *fully_conserved, action.selected_good)
        elif action.type == "trader":
            return (
                action.type,
                action.selected_good,
            )
        else:
            return (action.type,)

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"
        # self.update(game)

        # total_return = 0
        final_value = game.board.towns[self.name].tally()

        for i, (state, action, town_value) in enumerate(self.episode):
            prev_value = self.sah_values.get((state, action), 0)
            counter = self.sah_counts.get((state, action), 0) + 1
            try:
                reward = self.episode[i+self.reward_window][2] - town_value
            except IndexError:
                reward = final_value - town_value

            alpha = 1 / counter
            if self.alpha is not None:
                alpha = max(alpha, self.alpha)

            self.sah_values[(state, action)] = prev_value + alpha * (reward - prev_value)
            self.sah_counts[(state, action)] = counter


        # new_returns = dict()
        # for state, action, reward in reversed(self.episode):
        #     total_return = self.gamma * total_return + reward
        #     new_returns[(state, action)] = total_return

        # for (state, action), discounted_return in new_returns.items():
        #     prev_value = self.sah_values.get((state, action), 0)
        #     counter = self.sah_counts.get((state, action), 0) + 1

        #     alpha = 1 / counter
        #     if self.alpha is not None:
        #         alpha = max(alpha, self.alpha)

        #     self.sah_values[(state, action)] = prev_value + alpha * (discounted_return - prev_value)
        #     self.sah_counts[(state, action)] = counter

        self.episode = list()

    # def update(
    #     self, game: Game, state: Optional[int] = None, action: Optional[int] = None
    # ):
    #     self.episode.append((state, action, game.board.towns[self.name].tally()))
    #     current_value = game.board.towns[self.name].tally()
    #     reward = current_value - self.value_memory

    #     if self.state_memory is not None and self.action_memory is not None:
    #         self.episode.append((self.state_memory, self.action_memory, self.value_memory))
    #         # self.episode.append((self.state_memory, self.action_memory, reward))

    #     self.value_memory = game.board.towns[self.name].tally() if (state is not None and action is not None) else 0
    #     self.state_memory = state
    #     self.action_memory = action
    
    # def learn_from(self, other: "Pablo"):
    #     quotient = 1 + int(max(1, self.state_space_dim / other.state_space_dim) * max(1, self.action_space_dim / other.action_space_dim))
    #     for i in range(self.state_space_dim):
    #         other_i = i % other.state_space_dim
    #         for j in range(self.action_space_dim):
    #             other_j = j % other.action_space_dim
    #             if (other_i, other_j) in other.sah_values:
    #                 self.sah_values[(i, j)] = other.sah_values[(other_i, other_j)]
    #                 self.sah_counts[(i, j)] = other.sah_counts[(other_i, other_j)] // quotient

