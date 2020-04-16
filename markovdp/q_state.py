class QState(object):
    """QState Class.

    This class represents a Q-state in the MDP model.

    Attributes:
        _action_taken_times (int): The number of the action has been taken
        _action_type (str): The name of the action to execute
        _action_value (int): The value related to the action under execution
        _rewards (list): The rewards for each of the actions
        _transitions (list): The transitions from state to state

    Args:
        action (str, int): The type and value of action to be taken
        total_states (int): Total number of states in MDP model
        q_value (double): The Q-value of this Q-state
    """

    def __init__(self, action, total_states, q_value=0.0):
        """Q-state Class Constructor."""
        self._action = action
        self._action_type = action[0]
        self._action_value = action[1]
        self._action_taken_times = 0
        self._q_value = q_value
        self._transitions = [0] * total_states
        self._rewards = [0] * total_states
        self._total_states = total_states

    @property
    def action(self):
        """Gets the action that corresponds to this Q-state."""
        return self._action

    @property
    def action_taken_times(self):
        """The number of times this action has been taken"""
        return self._action_taken_times

    @property
    def q_value(self):
        """Gets the Q-value of the Q-state."""
        return self._q_value

    @q_value.setter
    def q_value(self, q_value):
        """The Q-value for this action."""
        self._q_value = q_value

    @property
    def rewards(self):
        """Gets list containing the total rewards gained after transitioning to each state."""
        return self._rewards

    @property
    def transitions(self):
        """Returns a list containing the number of transitions to each state."""
        return self._transitions

    def update(self, new_state, reward):
        """Updates the transition and reward estimations after the given transition.

        Args:
            new_state (State): The state the transition leads to
            reward (double): The reward acquired from the transition

        """
        self._action_taken_times += 1
        state_num = new_state.state_num
        self._transitions[state_num] += 1
        self._rewards[state_num] += reward

    def has_transition(self, state_num):
        """Checks if state has feasible transition.

        Args:
            state_num (int): The unique state number in the MDP model

        Returns:
            has_transition (bool): True if transition probability is non-zero

        """
        return self._transitions[state_num] > 0

    def get_transition(self, state_num):
        """Estimates transition probability to the given state.

        Args:
            state_num (int): The unique state number in the MDP model

        Returns:
            transition_prob (double): The transition probability to the given state

        """
        if self._action_taken_times == 0:
            return 1 / self._total_states
        else:
            return self._transitions[state_num] / self._action_taken_times

    def get_num_transitions(self, state_num):
        """Returns the number of recorded transitions to the given state.

        Args:
            state_num (int): The unique state number in the MDP model

        Returns:
            transitions (int): Number of recorded transitions to this state

        """
        return self._transitions[state_num]

    def get_reward(self, state_num):
        """Estimated reward after taking this action.

        Args:
            state_num (int): The unique state number in the MDP model

        Returns:
            reward (double): The reward after taking this action

        """
        if self._transitions[state_num] == 0:
            return 0.0
        else:
            return self._rewards[state_num] / self._transitions[state_num]

    def __str__(self):

        return "Action: {} \tQ-value: {}  \tTaken: {}".format(self._action, self._q_value, self._action_taken_times)

    def __repr__(self):

        return str(self)
