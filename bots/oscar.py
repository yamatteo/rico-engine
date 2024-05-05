from functools import partial
from .estimators import Estimator, upper_confidence_bound
from .. import *
from hashlib import md5

action_projections = dict()
state_projections = dict()


def index_building(building: Optional[Building]):
    return f"{[None, *BUILDINGS].index(building):02}"


def index_good(good: Optional[Good]):
    return str([None, *GOODS].index(good))


def index_role(role: Optional[Role]):
    return {
        None: "0",
        "builder": "B",
        "captain": "C",
        "craftsman": "F",
        "mayor": "M",
        "settler": "S",
        "trader": "T",
        "prospector": "P",
        "second_prospector": "P",
    }[role]


def index_tile(tile: Optional[Tile]):
    return str([None, *TILES].index(tile))


def project_action(action: Action) -> str:
    if action.type == "role":
        return f"R{index_role(action.role)}"
    elif action.type == "builder":
        return f"B{index_building(action.building_type)}{int(action.extra_person)}"
    elif action.type == "captain":
        return f"C{'0' if action.selected_ship is None else action.selected_ship}{index_good(action.selected_good)}"
    elif action.type == "craftsman":
        return f"F{index_good(action.selected_good)}"
    elif action.type == "mayor":
        dist = PeopleDistribution(action.people_distribution)
        production = [dist.get_production(good) for good in GOODS]
        quarries = dist.get_privilege("quarry_tile")
        privileges = [dist.get_privilege(building) for building in NONPROD_BUILDINGS]
        # data = (*production, quarries, *privileges)
        data = (*production, quarries)
        return "M" + str().join(map(str, data))
    elif action.type == "settler":
        return f"S{index_tile(action.tile)}{int(action.extra_person)}{int(action.down_tile)}"
    elif action.type == "storage":
        fully_conserved = sorted(
            map(
                index_good,
                (
                    action.large_warehouse_first_good,
                    action.large_warehouse_second_good,
                    action.small_warehouse_good,
                ),
            )
        )
        return "W" + str().join(fully_conserved) + index_good(action.selected_good)
    elif action.type == "trader":
        return "T" + index_good(action.selected_good)
    elif action.type == "governor":
        return "G"
    elif action.type == "tidyup":
        return "Y"
    else:
        return "?"


def project_state(game: Game, *, wrt: str) -> str:
    town_dict = game.board.towns[wrt].asdict_strings()
    data = str(" ").join(
        [
            str().join([town_dict[k] for k in kg])
            for kg in [
                ["is_governor", "role", "spent_role", "spent_wharf"],
                # GOODS,
                # ["people", "money", "points"],
                # [f"placed_{t}" for t in TILES],
                # [f"worked_{t}" for t in TILES],
                [f"placed_{b}" for b in BUILDINGS],
                # [f"worked_{b}" for b in BUILDINGS],
            ]
        ]
    )
    return data


class Oscar:
    """A bot that take decisions based on reinforcement learning, with some variation of TD methods."""

    def __init__(
        self,
        name: str,
        reward_window = 1,
        init_value=0.0,
        max_counter=100,
        target_policy=("epsilon", 0.01),
        behavior_policy=("epsilon", 0.1),
    ):
        self.name = name

        self.action_rewards = dict()
        self.state_returns = dict()
        self.state_action_values: dict[tuple[int, int], Estimator] = dict()
        self.episode = []
        self.value_memory = 0
        self.role_memory = None
        self.round_times = [0]

        self.init_value = init_value
        self.max_counter = max_counter
        self.reward_window = reward_window

        match reward_window:
            case 'rounds':
                self.update = self.update_with_rounds
            case int(n):
                self.update = partial(self.update_with_fixed_timestep, n=n)

        match behavior_policy:
            case ("epsilon", epsilon):
                self.behavior_policy = partial(self.epsilon_policy, epsilon=epsilon)

        match target_policy:
            case ("epsilon", epsilon):
                self.target_policy = partial(self.epsilon_policy, epsilon=epsilon)

    def decide(self, game: Game) -> Action:
        """Given the current game state, decides what action to take."""
        assert self.name == game.expected.name, "Not my turn!"

        board = game.board
        expected = game.expected
        self.update_round_times(game)

        state = project_state(game, wrt=self.name)

        choices = {
            project_action(act): act for act in expected.possibilities(board, cap=40)
        }
        # for act in choices.keys():
        #     if (state, act) not in self.state_action_values:
        #         self.state_action_values[(state, act)] = Estimator(
        #             self.init_value, self.max_counter
        #         )
        for act in choices.keys():
            if act not in self.action_rewards:
                self.action_rewards[act] = Estimator(
                    self.init_value, self.max_counter
                )

        selected_action, b_policy_weights = self.behavior_policy(state, list(choices.keys()))
        _, t_policy_weights = self.target_policy(state, list(choices.keys()))
        current_value = game.board.towns[self.name].tally()

        action_projections[selected_action[0]] = action_projections.get(selected_action[0], set()) | {selected_action}

        self.episode.append(
            dict(
                reward=current_value - self.value_memory,
                state=state,
                actions=list(choices.keys()),
                b_policy_weights=b_policy_weights,
                t_policy_weights=t_policy_weights,
                selected_action=selected_action,
            )
        )
        self.value_memory = current_value

        return choices[selected_action]

    def update_with_fixed_timestep(self, *, n=1):
        T = len(self.episode)-1
        for tau in range(len(self.episode)-1):
            start_state = self.episode[tau]["state"]
            start_action = self.episode[tau]["selected_action"]
            G = sum([ self.episode[i]["reward"] for i in range(tau+1, min(tau+n+1, T))])
            if tau + n + 1 < T:
                stop_state = self.episode[tau + n + 1]["state"]
                stop_action = self.episode[tau + n + 1]["selected_action"]
                G += float(self.state_action_values[(stop_state, stop_action)])
            self.state_action_values[(start_state, start_action)].put(G)
    
    def update_with_rounds(self):
        ep = self.episode
        episode_return = self.value_memory
        for t in self.round_times:
            state = ep[t]["state"]
            try:
                self.state_returns[state].put(episode_return)
            except KeyError:
                self.state_returns[state] = Estimator(episode_return, max_counter=self.max_counter)
        for (start, stop) in zip(self.round_times[:-1], self.round_times[1:]):
            start_value = float(self.state_returns[ep[start]["state"]])
            stop_value = float(self.state_returns[ep[stop]["state"]])
            transition_reward = (stop_value - start_value) / (stop - start)
            for t in range(start, stop):
                action = ep[t]["selected_action"]
                reward = ep[t+1]["reward"]
                try:
                    self.action_rewards[action].put(reward+transition_reward)
                except KeyError:
                    self.action_rewards[action] = Estimator(reward+transition_reward, max_counter=self.max_counter)

    def update_round_times(self, game: Game):
        town = game.board.towns[self.name]
        if self.role_memory is not None and town.role is None:
            self.round_times.append(len(self.episode))
        self.role_memory = town.role

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"

        current_value = game.board.towns[self.name].tally()
        self.round_times.append(len(self.episode))
        self.episode.append(
            dict(
                reward=current_value - self.value_memory,
                state=None,
                actions=[],
                b_policy_weights=[],
                t_policy_weights=[],
                selected_action=None,
            )
        )
        self.value_memory = current_value
        self.update()
        self.value_memory = 0
        self.round_times = [0]
        self.episode = []
        self.role_memory = None

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

    def epsilon_policy(self, state: str, actions: Sequence[str], *, epsilon: float):
        best = max(
            actions, key=lambda act: float(self.action_rewards[act])
        )
        residual = epsilon / len(actions)
        weights = [residual + (1 - epsilon if act == best else 0) for act in actions]
        if random.random() < epsilon:
            return random.choice(actions), weights
        else:
            return best, weights
