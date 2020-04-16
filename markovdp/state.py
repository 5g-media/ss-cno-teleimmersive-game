class State(object):
    """State Class.

    The role of this class is to represent a state in the MDP Model.

    Attributes:
        _q_states (list): The q-states of this state
        _value (double): The value of the state
        _best_q_state (Q-state): Q-state with highest Q-value
        _times_visited (int): The number of visits to this state

    Args:
        parameters (list): The list of parameters of this state
        state_num (int): Unique number of state in MDP model
        total_states (int): The total number of visited states

    """

    def __init__(self, parameters=None, state_num=0, total_states=0):
        """State class constructor."""
        self._best_q_state = None
        self._parameters = [] if parameters is None else list(parameters)
        self._q_states = []
        self._state_num = state_num
        self._times_visited = 0
        self._total_states = total_states
        self._value = 0

    @property
    def best_q_state(self):
        """Gets the Q-state with the highest Q-value"""
        return self._best_q_state

    @property
    def parameters(self):
        """Gets list of the parameters for this state."""
        return self._parameters

    @property
    def q_states(self):
        """Gets Q-states for the current state."""
        return self._q_states

    @property
    def state_num(self):
        """Gets the unique number of the state in the MDP model."""
        return self._state_num

    @property
    def total_states(self):
        """Gets the total number of states in MDP model."""
        return self._total_states

    @total_states.setter
    def total_states(self, total_states):
        self._total_states = total_states

    @property
    def value(self):
        """The current value of the state."""
        return self._value

    def visit(self):
        """Increments the number of times the state has been visited."""
        self._times_visited += 1

    def get_optimal_action(self):
        """Returns the optimal action for this state."""
        return self._best_q_state.action

    def best_action_num_taken(self):
        """Number of executions of the optimal action."""
        return self._best_q_state.action_taken_times()

    def update_value(self):
        """Updates the value of the state based on the values of its Q-states."""
        self._best_q_state = self._q_states[0]
        self._value = self._q_states[0].q_value
        for q_state in self._q_states:
            if q_state.q_value > self._value:
                self._best_q_state = q_state
                self._value = q_state.q_value

    def add_new_parameter(self, name, values):
        """Adds a new parameter-value pair to the list of parameters of the state.

        Args:
            name (str): Name of parameter
            values (double): Value of the parameter

        """
        self._parameters.append((name, values))

    def get_parameter(self, parameter):
        """Returns the value for the given parameter.

        Args:
            parameter (str): The name of a parameter

        Returns:
            value (double): The value of the parameter

        """
        for param, value in self.parameters:
            if param == parameter:
                return value
        return None

    def add_q_state(self, q_state):
        """ Adds a new Q-state to this State.

        Args:
            q_state (object): The Q-state to add to current State

        """
        self._q_states.append(q_state)
        if self._best_q_state is None:
            self._best_q_state = q_state

    def get_q_state(self, action):
        """Gets the Q-state that corresponds to the given action.

        Args:
            action (str, int): An action tuple with action name and value

        Returns:
            q_state (QState): Q-state corresponding to action

        """
        for q_state in self._q_states:
            if q_state.action == action:
                return q_state

    def get_max_transitions(self):
        """Maximum transition probability for any action.

        Returns:
            transitions (dict): Maximum transition probability per transition

        """
        transitions = {}
        for i in range(self._total_states):
            for q_state in self._q_states:
                if q_state.has_transition(i):
                    if i in transitions:
                        transitions[i] = max(transitions[i], q_state.get_transition(i))
                    else:
                        transitions[i] = q_state.get_transition(i)

        return transitions

    def get_legal_actions(self):
        """Returns all the possible actions from this state.

        Returns:
            actions (str, int): Possible actions for this state.

        """
        return [q_state.action for q_state in self._q_states]

    def __str__(self):
        return "{}: {}".format(self._state_num, str(self._parameters))

    def __repr__(self):
        return str(self)

    def print_detailed(self):
        """Prints the details of the state and its Q-states."""
        print("{}: {}, visited: {}".format(self._state_num, str(self._parameters), self._times_visited))
        for qs in self._q_states:
            print(qs)
        print()
