from functools import partial
from .estimators import Estimator, upper_confidence_bound
from .. import *


def project_state(game: Game, *, wrt: str) -> str:
    town_dict = game.board.towns[wrt].asdict_strings()
    data = str(" ").join(
        [
            str().join([town_dict[k] for k in kg])
            for kg in [
                ["is_governor", "role", "spent_role", "spent_wharf"],
                GOODS,
                ["people", "money", "points"],
                [f"placed_{t}" for t in TILES],
                [f"worked_{t}" for t in TILES],
                [f"placed_{b}" for b in BUILDINGS],
                [f"worked_{b}" for b in BUILDINGS],
            ]
        ]
    )
    return data

class Nadal:
    """A bot that take decisions based on reinforcement learning, with some variation of planning."""

    def __init__(
        self,
        name: str,
        max_counter=100,
        target_policy=("epsilon", 0.01),
        behavior_policy=("epsilon", 0.1),
    ):
        self.name = name

        self.state_returns = dict()
        # self.episode = []
        # self.value_memory = 0
        # self.role_memory = None
        # self.round_times = [0]

        # self.init_value = init_value
        self.max_counter = max_counter
        # self.reward_window = reward_window

        # match reward_window:
        #     case 'rounds':
        #         self.update = self.update_with_rounds
        #     case int(n):
        #         self.update = partial(self.update_with_fixed_timestep, n=n)

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

        state = project_state(game, wrt=self.name)

        choices = expected.possibilities(board, cap=30)
        future_games = [ game.project(act) for act in choices ]
        states, values = [], []
        for future_game in future_games:
            future_state = project_state(future_game, wrt=self.name)
            try:
                future_value = float(self.state_returns[future_state])
            except KeyError:
                self.state_returns[future_state] = Estimator(value=future_game.board.towns[self.name].tally(), max_counter=self.max_counter)
                future_value = float(self.state_returns[future_state])
            states.append(future_state)
            values.append(future_value)
        
        updated_value = max(values)
        try:
            self.state_returns[state].put(updated_value)
        except KeyError:
            self.state_returns[state] = Estimator(value=updated_value, max_counter=self.max_counter)
        

        
        # for act in choices.keys():
        #     if (state, act) not in self.state_action_values:
        #         self.state_action_values[(state, act)] = Estimator(
        #             self.init_value, self.max_counter
        #         )
        # for act in choices.keys():
        #     if act not in self.action_rewards:
        #         self.action_rewards[act] = Estimator(
        #             self.init_value, self.max_counter
        #         )

        # selected_action, b_policy_weights = self.behavior_policy(state, list(choices.keys()))
        # _, t_policy_weights = self.target_policy(state, list(choices.keys()))
        # current_value = game.board.towns[self.name].tally()

        index, state = self.behavior_policy(states, values)

        # action_projections[selected_action[0]] = action_projections.get(selected_action[0], set()) | {selected_action}

        # self.episode.append(
        #     dict(
        #         reward=current_value - self.value_memory,
        #         state=state,
        #         actions=list(choices.keys()),
        #         b_policy_weights=b_policy_weights,
        #         t_policy_weights=t_policy_weights,
        #         selected_action=selected_action,
        #     )
        # )
        # self.value_memory = current_value

        return choices[index]

    # def update_with_fixed_timestep(self, *, n=1):
    #     T = len(self.episode)-1
    #     for tau in range(len(self.episode)-1):
    #         start_state = self.episode[tau]["state"]
    #         start_action = self.episode[tau]["selected_action"]
    #         G = sum([ self.episode[i]["reward"] for i in range(tau+1, min(tau+n+1, T))])
    #         if tau + n + 1 < T:
    #             stop_state = self.episode[tau + n + 1]["state"]
    #             stop_action = self.episode[tau + n + 1]["selected_action"]
    #             G += float(self.state_action_values[(stop_state, stop_action)])
    #         self.state_action_values[(start_state, start_action)].put(G)
    
    # def update_with_rounds(self):
    #     ep = self.episode
    #     episode_return = self.value_memory
    #     for t in self.round_times:
    #         state = ep[t]["state"]
    #         try:
    #             self.state_returns[state].put(episode_return)
    #         except KeyError:
    #             self.state_returns[state] = Estimator(episode_return, max_counter=self.max_counter)
    #     for (start, stop) in zip(self.round_times[:-1], self.round_times[1:]):
    #         start_value = float(self.state_returns[ep[start]["state"]])
    #         stop_value = float(self.state_returns[ep[stop]["state"]])
    #         transition_reward = (stop_value - start_value) / (stop - start)
    #         for t in range(start, stop):
    #             action = ep[t]["selected_action"]
    #             reward = ep[t+1]["reward"]
    #             try:
    #                 self.action_rewards[action].put(reward+transition_reward)
    #             except KeyError:
    #                 self.action_rewards[action] = Estimator(reward+transition_reward, max_counter=self.max_counter)

    # def update_round_times(self, game: Game):
    #     town = game.board.towns[self.name]
    #     if self.role_memory is not None and town.role is None:
    #         self.round_times.append(len(self.episode))
    #     self.role_memory = town.role

    def terminate(self, game: Game):
        """Things to do when the game ends."""
        assert (
            game.expected.type == "governor" and game.board.endgame_reason is not None
        ), "Game is not over!"

        # current_value = game.board.towns[self.name].tally()
        # self.round_times.append(len(self.episode))
        # self.episode.append(
        #     dict(
        #         reward=current_value - self.value_memory,
        #         state=None,
        #         actions=[],
        #         b_policy_weights=[],
        #         t_policy_weights=[],
        #         selected_action=None,
        #     )
        # )
        # self.value_memory = current_value
        # self.update()
        # self.value_memory = 0
        # self.round_times = [0]
        # self.episode = []
        # self.role_memory = None

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

    def epsilon_policy(self, states: list[str], values: list[float], *, epsilon: float):
        if random.random() < epsilon:
            return random.choice(list(enumerate(states)))
        i = max(
            range(len(states)), key=lambda i: values[i] + 0.01*random.random()
        )
        return i, states[i]