import logging.config

from django.conf import settings

from markovdp.constants import PARAMETERS, ACTIONS, DISCOUNT, INITIAL_Q_VALUES, VALUES, LIMITS, SINGLE_UPDATE, \
    VALUE_ITERATION, PRIORITIZED_SWEEPING, UPDATE_ALGORITHM
from markovdp.exceptions import ConfigurationError, StateNotSetError, ParameterError
from markovdp.q_state import QState
from markovdp.state import State

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


class MDPModel:
    """MDPModel Class.

    This class represents a full Markov Decision Process model.

    Attributes:
        _discount (double):
        _states (list(State)):
        _index_params (list):
        _index_states (list(State)):
        _current_state (State):
        _max_updates (int):
    Args:
        conf (dict): A dictionary including various configuration variables

    """

    def __init__(self, conf):
        required_fields = [PARAMETERS, ACTIONS, DISCOUNT, INITIAL_Q_VALUES, UPDATE_ALGORITHM]
        for field in required_fields:
            if field not in conf:
                raise ConfigurationError("{} not provided in the configuration".format(field))

        self._discount = conf[DISCOUNT]
        self._states = [State()]
        self._index_params = []
        self._index_states = list(self._states)
        self._current_state = None
        self._update_algorithm = conf[UPDATE_ALGORITHM]
        self._update_error = 0.05
        self._max_updates = 100

        self._assert_modeled_params(conf)
        parameters = self._get_params(conf[PARAMETERS])

        # create all the states of the model
        for name, param in parameters.items():
            self._index_params.append((name, param[VALUES]))
            self._update_states(str(name), param)

        # set the final number of states to all states
        num_states = len(self._states)
        for s in self._states:
            s.total_states = num_states

        self._set_maxima_minima(parameters, conf[ACTIONS])
        self._add_q_states(conf[ACTIONS], conf[INITIAL_Q_VALUES])

        # initialize the reverse transition indexes and priorities for prioritized sweeping
        self._reverse_transitions = []
        self._priorities = [0] * len(self._states)
        for i in range(len(self._states)):
            self._reverse_transitions.append({})

        logger.info('Initialized MDPModel Class')

    @property
    def discount(self):
        """Gets the discount for rewards."""
        return self._discount

    def set_update_algorithm(self, update_algorithm, update_error=0.1, max_updates=10):
        """Sets the update algorithm, error and max_updates

        Args:
            update_algorithm (str): The selected algorithm for updates
            update_error (double): The selected update error
            max_updates (int): The maximum number of updates

        """
        self._update_algorithm = update_algorithm
        self._update_error = update_error
        self._max_updates = max_updates
        logger.debug('Algorithm for updates set to {} with error = {} and max updates = {}'
                     .format(update_algorithm, update_error, max_updates))

    @staticmethod
    def _assert_modeled_params(conf):
        """Asserts that action dependent parameters are being modeled."""
        pass

    @staticmethod
    def _get_params(parameters):
        """
        The values of each model parameter are represented as a [min, max] touple.
        This method asserts that values are provided for all the parameters and converts
        distinct values to [min, max] tuples.
        """
        new_params = {}
        for param_name, param_values in parameters.items():

            new_params[param_name] = {}

            # we convert both values and limits to pairs of limits so we can treat them uniformly
            if VALUES in param_values:
                if not isinstance(param_values[VALUES], list):
                    raise ConfigurationError("Provided values for %s must be in a list" % param_name)
                if len(param_values[VALUES]) <= 1:
                    raise ConfigurationError("At least two values must be provided for " + param_name)

                values = []
                for v in param_values[VALUES]:
                    values.append((v, v))
                new_params[param_name][VALUES] = values

            elif LIMITS in param_values:
                if not isinstance(param_values[LIMITS], list):
                    raise ConfigurationError("Provided limits for %s must be in a list" % param_name)
                if len(param_values[LIMITS]) <= 2:
                    raise ConfigurationError("At least three limits must be provided for " + param_name)

                values = []
                for i in range(1, len(param_values[LIMITS])):
                    values.append((param_values[LIMITS][i - 1], param_values[LIMITS][i]))
                new_params[param_name][VALUES] = values

            if VALUES not in new_params[param_name]:
                raise ConfigurationError("Values or limits must be provided for parameter " + param_name)

        return new_params

    def set_state(self, measurements):
        """Initializes the current state based on the given measurements.

        Args:
            measurements (dict): A dictionary of collected measurements

        """
        self._current_state = self._get_state(measurements)

    def _update_states(self, name, new_parameter):
        """
        Extends the current states to include all the possible values of the
        given parameter, multiplying their number with the number of values
        of the parameter.
        """
        state_num = 0
        new_states = []
        for value in new_parameter[VALUES]:
            for state in self._states:
                new_state = State(state.parameters, state_num)
                new_state.add_new_parameter(name, value)
                new_states.append(new_state)
                state_num += 1

        self._states = new_states

    def _set_maxima_minima(self, parameters, actions):
        """Stores min and max values for the parameters that have actions which need to be limited.

        Args:
            parameters (dict): The parameters accounted in the MDP Model
            actions (tuple(str, int)): The action name and values tuples

        """
        pass

    def _add_q_states(self, actions, initial_q_value):
        """Adds the given actions to all the states.

        Args:
            actions (list(tuple)): The available action for execution
            initial_q_value (list(int)): The initial Q-values of the Q-states

        """
        num_states = len(self._states)
        for action_type, values in actions.items():
            if values is None:
                action = (action_type, None)
                for state in self._states:
                    if self._is_permissible(state, action):
                        state.add_q_state(QState(action, num_states, initial_q_value))
                continue
            for action_value in values:
                action = (action_type, action_value)
                for state in self._states:
                    if self._is_permissible(state, action):
                        state.add_q_state(QState(action, num_states, initial_q_value))

        for state in self._states:
            state.update_value()

    def _is_permissible(self, state, action):
        """Returns true if we are allowed to take that action from that state."""
        action_type, action_value = action
        return True

    def _get_state(self, measurements):  # TODO this with indexing
        """Returns the state that corresponds to given set of measurements."""
        for name, values in self._index_params:
            if name not in measurements:
                raise ParameterError("Missing measurement: " + name)

        for state in self._states:
            matches = True
            for name, values in state.parameters:
                min_v, max_v = values
                if measurements[name] < min_v or measurements[name] > max_v:
                    matches = False
                    break
            if matches:
                return state

    def suggest_action(self):
        """Suggest the next action based on the greedy criterion.

        Returns:
            optimal_action (tuple(str, int)): The suggested optimal action

        """
        if self._current_state is None:
            raise StateNotSetError()

        return self._current_state.get_optimal_action()

    def get_legal_actions(self):
        """Returns all the legal actions from the current_state.

        Returns:
            legal_actions (list(tuple)): A list of all the legal actions from the current state

        """
        if self._current_state is None:
            raise StateNotSetError()

        return self._current_state.get_legal_actions()

    def update(self, action, measurements, reward):
        """Updates model after the given action and ending up in the state corresponding to the given measurements.

        Args:
            action (tuple): The action taken
            measurements (dict): The measurements collected after the action was taken
            reward (double): The reward acquired after this action was taken

        """
        if self._current_state is None:
            raise StateNotSetError()

        self._current_state.visit()
        q_state = self._current_state.get_q_state(action)
        if q_state is None:
            return

        new_state = self._get_state(measurements)
        q_state.update(new_state, reward)

        if self._update_algorithm == SINGLE_UPDATE:
            self._q_update(q_state)
            self._current_state.update_value()
        elif self._update_algorithm == VALUE_ITERATION:
            self.value_iteration()
        elif self._update_algorithm == PRIORITIZED_SWEEPING:
            self.prioritized_sweeping()

        self._current_state = new_state

    def _q_update(self, q_state):
        """Runs a single update for the Q-value of the given state-action pair.

        Args:
            q_state (QState):  The Q-state to update Q-value for

        """
        new_q_value = 0
        for i in range(len(self._states)):
            t = q_state.get_transition(i)
            r = q_state.get_reward(i)
            new_q_value += t * (r + self._discount * self._states[i].value)

        q_state.q_value = new_q_value

    def _v_update(self, state):
        """Recalculates value of Q-states of the given state and updates accordingly.

        Args:
            state (State): The state to recalculate values for

        """
        for q_state in state.q_states:
            self._q_update(q_state)
        state.update_value()

    def value_iteration(self, error=None):
        """Runs the value iteration algorithm on the model.

        Args:
            error (double): The update error

        """
        if error is None:
            error = self._update_error

        repeat = True
        while repeat:
            repeat = False
            for state in self._states:
                old_value = state.value
                self._v_update(state)
                new_value = state.value
                if abs(old_value - new_value) > error:
                    repeat = True

    def prioritized_sweeping(self, initial_state=None, error=None, max_updates=None):
        """Runs prioritized sweeping starting from the given state.

        Args:
            initial_state (State): The initial state in the prioritized sweeping process
            error (double): The updating error
            max_updates (int): The max number of updates

        """
        if self._current_state is None and initial_state is None:
            raise StateNotSetError()

        if initial_state is None:
            initial_state = self._current_state
        if error is None:
            error = self._update_error
        if max_updates is None:
            max_updates = self._max_updates

        # transition probabilities have changed for the initial state
        max_transitions = initial_state.get_max_transitions()
        initial_s_num = initial_state.state_num
        for state_num, t in max_transitions.items():
            self._reverse_transitions[state_num][initial_s_num] = t

        state, num_updates = initial_state, 0
        for i in range(max_updates):

            num_updates += 1

            # Update the state value
            old_value = state.value
            self._v_update(state)
            new_value = state.value
            delta = abs(new_value - old_value)

            # Update the priorities of the predecessors
            rev_transitions = self._reverse_transitions[state.state_num]
            for state_num, t in rev_transitions.items():
                self._priorities[state_num] = max(t * delta, self._priorities[state_num])

            # zero the updated state's priority
            self._priorities[state.state_num] = 0

            # choose the next max priority state
            # TODO with Priority Queue - but needs to support item removal
            max_index, max_priority = 0, 0
            for j in range(len(self._priorities)):
                if self._priorities[j] > max_priority:
                    max_priority = self._priorities[j]
                    max_index = j

            # stop if the priority gets below the supplied limit
            if max_priority <= error:
                break

            state = self._states[max_index]

    def get_parameters(self):
        """Returns a list of the names of all the parameters in the states of the model."""
        return [name for name, _ in self._index_params]

    def get_percent_not_taken(self):
        """Returns the percentage of actions that have never been taken."""
        total, not_taken = 0, 0
        for state in self._states:
            for q_state in state.q_states:
                total += 1
                if q_state.action_taken_times == 0:
                    not_taken += 1

        return not_taken / total

    def print_model(self, detailed=False):
        """Prints the states of the model. If detailed is True it also prints the Q-states.

        Args:
            detailed (bool): Set to true in order to also print the Q-states

        """
        for state in self._states:
            if detailed:
                state.print_detailed()
            else:
                print(state)

    def print_state_details(self):
        """Prints the Q-states and the transition and reward lists for each Q-state."""
        for state in self._states:
            print("State: {}".format(state))
            for q_state in state.q_states:
                print(q_state)
                # print("Transitions:", qs.transitions)
                # print("Rewards:    ", qs.rewards)
            print()
