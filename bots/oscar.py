from .estimators import Estimator, upper_confidence_bound
from .. import *
from hashlib import md5

action_projections = dict()
state_projections = dict()


class Oscar:
    """A bot that take decisions based on reinforcement learning, with some variation of TD methods."""

    def __init__(
        self,
        name: str,
        # use_delta: bool = False,
        # alpha: Optional[float] = None,
        # epsilon: float = 0.1,
        action_space_dim=2**10,
        # reward_window = 1,
        state_space_dim=2**10,
        init_value=0.0,
        max_counter=100,
        use_epsilon_gready=False,
        use_upper_confidence=False,
    ):
        self.name = name
        # self.episode = []
        self.last_value = 0
        self.last_action = None
        # self.reward_window = reward_window
        self.last_state = None

        # self.sah_values: dict[tuple[int, int], float] = dict()
        # self.sah_counts: dict[tuple[int, int], int] = dict()
        self.state_action_values: dict[tuple[int, int], Estimator] = dict()

        self.init_value = init_value
        self.state_space_dim = state_space_dim
        self.action_space_dim = action_space_dim
        self.max_counter = max_counter

        assert (use_epsilon_gready or use_upper_confidence) and not (
            use_epsilon_gready and use_upper_confidence
        )
        self.use_epsilon_gready = use_epsilon_gready
        self.use_upper_confidence = use_upper_confidence

        # self.alpha = alpha
        # self.epsilon = epsilon
        # self.gamma = 0.99

    def decide(self, game: Game) -> Action:
        """Given the current game state, decides what action to take."""
        assert self.name == game.expected.name, "Not my turn!"

        board = game.board
        expected = game.expected

        state = self.project_state(game)

        choices: Sequence[Action] = expected.possibilities(board, cap=40)

        # Take the best action, with an epsilon probability of random exploratory behavior
        if self.use_epsilon_gready and random.random() < self.epsilon:
            action = random.choice(choices)
        else:
            estimators = [
                self.state_action_values.get(
                    (state, self.project_action(action)),
                    Estimator(self.init_value, self.max_counter),
                )
                for action in choices
            ]
            if self.use_upper_confidence:
                values = upper_confidence_bound(estimators)
            else:
                values = [float(est) for est in estimators]
            action = max(zip(choices, values), key=lambda t: t[1])[0]

        self.update(
            game=game,
            state=state,
            choices=choices,
            selected_action=self.project_action(action),
        )

        return action

    def project_action(self, action: Action):
        def as_tuple(action: Action):
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

        data = str().join(map(str, as_tuple(action))).encode("utf8")
        projection = (
            int.from_bytes(md5(data).digest(), byteorder="little")
            % self.action_space_dim
        )
        action_projections[projection] = action_projections.get(projection, set()) | {
            str(action)
        }
        return projection

    def project_state(self, game: Game) -> int:
        town_dict = game.board.towns[self.name].asdict_integers()
        data = str().join(map(str, town_dict.values())).encode("utf8")
        projection = (
            int.from_bytes(md5(data).digest(), byteorder="little")
            % self.state_space_dim
        )
        state_projections[projection] = state_projections.get(projection, set()) | {
            str(town_dict)
        }
        return projection

    def update(
        self,
        game: Game,
        state: Optional[int] = None,
        choices: list[Action] = [],
        selected_action: Optional[int] = None,
    ):
        current_value = game.board.towns[self.name].tally()
        reward = current_value - self.last_value

        if state is not None:
            for possible_action in choices:
                action = self.project_action(possible_action)
                if (state, action) not in self.state_action_values:
                    self.state_action_values[(state, action)] = Estimator(self.init_value, self.max_counter)

        if self.last_state is not None and self.last_action is not None:
            # last_qsa = float(
            #     self.state_action_values[(self.last_state, self.last_action)]
            # )
            if choices:
                current_qsa = max(
                    float(self.state_action_values[(state, self.project_action(action))])
                    for action in choices
                )
            else:
                current_qsa = 0.0
            self.state_action_values[(self.last_state, self.last_action)].put(reward + current_qsa)
            # self.episode.append((self.last_state, self.last_action, self.last_value))
            # self.episode.append((self.state_memory, self.action_memory, reward))

        self.last_value = (
            current_value
            if (state is not None and selected_action is not None)
            else 0
        )
        self.last_state = state
        self.last_action = selected_action

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"
        self.update(game)

        # total_return = 0
        # final_value = game.board.towns[self.name].tally()

        # for i, (state, action, town_value) in enumerate(self.episode):
        #     prev_value = self.sah_values.get((state, action), 0)
        #     counter = self.sah_counts.get((state, action), 0) + 1
        #     try:
        #         reward = self.episode[i + self.reward_window][2] - town_value
        #     except IndexError:
        #         reward = final_value - town_value

        #     alpha = 1 / counter
        #     if self.alpha is not None:
        #         alpha = max(alpha, self.alpha)

        #     self.sah_values[(state, action)] = prev_value + alpha * (
        #         reward - prev_value
        #     )
        #     self.sah_counts[(state, action)] = counter

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

        # self.episode = list()

    # def learn_from(self, other: "Pablo"):
    #     quotient = 1 + int(max(1, self.state_space_dim / other.state_space_dim) * max(1, self.action_space_dim / other.action_space_dim))
    #     for i in range(self.state_space_dim):
    #         other_i = i % other.state_space_dim
    #         for j in range(self.action_space_dim):
    #             other_j = j % other.action_space_dim
    #             if (other_i, other_j) in other.sah_values:
    #                 self.sah_values[(i, j)] = other.sah_values[(other_i, other_j)]
    #                 self.sah_counts[(i, j)] = other.sah_counts[(other_i, other_j)] // quotient
