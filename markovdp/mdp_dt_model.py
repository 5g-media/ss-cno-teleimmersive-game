import logging.config
import math
import warnings
from pprint import pprint
from timeit import default_timer as timer

from django.conf import settings
from numpy import mean
from scipy import stats

from markovdp.constants import *
from markovdp.exceptions import ConfigurationError, InternalError, StateNotSetError, ParameterError
from markovdp.decision_tree import LeafNode

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


class MDPDTModel:
    """MDPDTModel Class.

    Class that represents a Markov Decision Process model with a decision tree state structure.

    """

    def __init__(self, conf):
        required_fields = [INITIAL_PARAMETERS, PARAMETERS, ACTIONS, DISCOUNT,
                           INITIAL_Q_VALUES, SPLIT_ERROR, MIN_MEASUREMENTS]

        for f in required_fields:
            if f not in conf:
                raise ConfigurationError("%s not provided in the configuration" % f, logger)

        self._discount = conf[DISCOUNT]
        self._parameters = list(conf[PARAMETERS])
        self._min_measurements = max(conf[MIN_MEASUREMENTS], 1)
        self._split_error = conf[SPLIT_ERROR]
        self._actions = conf[ACTIONS]
        self._initial_q_values = conf[INITIAL_Q_VALUES]
        self._initial_params = self._get_params(conf[INITIAL_PARAMETERS])
        self._current_state = None
        self._current_measurements = None
        self._new_states = []
        self._transition_data = []
        self._statistical_test = STUDENT_TTEST

        # initiate the decision tree
        self._root = LeafNode(self, self, self._actions, self._initial_q_values, 0, 1)
        self._states = [self._root]
        self._priorities = [0]
        for name, values in self._initial_params.items():
            self._root.split(name, values)

        # set the default update and splitting algorithms and initialize the split counters
        self._update_algorithm = SINGLE_UPDATE
        self._update_error = 0.1  # default value for value iteration and PS error
        self._max_updates = 100  # default value for prioritized sweeping updates
        self._split_criterion = MID_POINT
        self._considered_transitions = True
        self._allow_splitting = True
        self._splits = {}
        for p in self._parameters:
            self._splits[p] = 0

        logger.debug('Initialized MDPDT model with {} states'.format(len(self._states)))

    @property
    def allow_splitting(self):
        """Allow or prevent the decision tree from splitting its nodes."""
        return self._allow_splitting

    @allow_splitting.setter
    def allow_splitting(self, allow=True):
        self._allow_splitting = allow
        logger.debug("Allow splitting set to {}".format(allow))

    @property
    def discount(self):
        """Returns discount of reward."""
        return self._discount

    @property
    def splits(self):
        """Returns the number of splits that happened for each parameter."""
        return self._splits

    @property
    def statistical_test(self):
        """Set the statistical test to use for splitting."""
        return self._statistical_test

    @statistical_test.setter
    def statistical_test(self, stat_test):
        self._statistical_test = stat_test

    def set_update_algorithm(self, update_algorithm, update_error=0.1, max_updates=10):
        self._update_algorithm = update_algorithm
        self._update_error = update_error
        self._max_updates = max_updates
        logger.debug('Algorithm for updates set to {} with error = {} and max updates = {}'
                     .format(update_algorithm, update_error, max_updates))

    def set_splitting_criterion(self, split_criterion, consider_transitions=True):
        """Set the splitting criterion"""
        if split_criterion not in SPLIT_CRITERIA:
            raise ParameterError("Unknown splitting algorithm: " + split_criterion, logger)
        self._split_criterion = split_criterion
        self._considered_transitions = consider_transitions
        logger.debug("Splitting criterion set to {}, consider transitions set to {}"
                     .format(split_criterion, consider_transitions))

    def reset_decision_tree(self, vi_error=None):
        """Returns the decision tree to its initial state, preserving all measurements collected."""
        # collect the transition information from all the states
        self._transition_data = [t for s in self._states for ts in s.transition_data for t in ts]

        # recreate the decision tree
        self._root = LeafNode(self, self, self._actions, self._initial_q_values, 0, 1)
        self._states = [self._root]
        for name, param in self._initial_params.items():
            self._root.split(name, param)

        # store the transition data in the new states and recalculate the state values
        self.retrain()
        self.value_iteration(error=vi_error)

        # reset the split counters
        for param in self._parameters:
            self._splits[param] = 0

        logger.debug("Decision Tree has been reset")

    @staticmethod
    def _get_params(parameters):
        """Extract the defined limits or values for the initial parameters so that they can be used by a decision node.
        """
        new_params = {}
        for name, value in parameters.items():

            # for discrete values we define the midpoint as the margin
            if VALUES in value:
                if not isinstance(value[VALUES], list):
                    raise ConfigurationError("Provided values for %s must be in a list" % name, logger)
                if len(value[VALUES]) <= 1:
                    raise ConfigurationError("At least two values must be provided for " + name, logger)

                limits = []
                for i in range(len(value[VALUES]) - 1):
                    limits.append((value[VALUES][i] + value[VALUES][i + 1]) / 2)
                new_params[name] = limits

            # for continuous values we just ignore the outer margins
            elif LIMITS in value:
                if not isinstance(value[LIMITS], list):
                    raise ConfigurationError("Provided limits for %s must be in a list" % name, logger)
                if len(value[LIMITS]) <= 2:
                    raise ConfigurationError("At least three limits must be provided for " + name, logger)

                new_params[name] = value[LIMITS][1:-1]

            else:
                raise ConfigurationError("Values or limits must be provided for parameter " + name, logger)

        return new_params

    def replace_node(self, old_node, new_node):
        """Replaces the root node with the given decision node upon root node splitting.

        Args:
            old_node (DecisionNode): The old node under replacement
            new_node (DecisionNode): The new node replacing the old

        """
        if not self._root.is_leaf():
            raise InternalError("Tried to replace the root node but it was not a leaf node", logger)

        if old_node.state_num is not self._root.state_num:
            raise InternalError("Tried to replace the root node with a different initial node", logger)

        self._root = new_node

    def set_state(self, measurements):
        """Sets the current state based on the given measurements.

        Args:
            measurements (dict): A dictionary of measurements

        """
        self._current_measurements = measurements
        self._current_state = self._root.get_state(measurements)

    def remove_state(self, state_num):
        """Removes the state with the given state_num from the model

        Args:
            state_num (int): The number of the state under removal

        """
        self._root.remove_state(state_num)
        self._states[state_num] = None
        self._priorities[state_num] = 0

    def store_transition_data(self, data):
        """Stores the given transition data to be used later on for retraining.

        Args:
            data (list): A list of transition data

        """
        self._transition_data += data

    def add_states(self, states):
        """Adds new states to the model. The first will go in the empty spot and the rest at the end.

        Args:
            states (list(State)): A list of states to add to the model

        """
        # the first state will not be appended at the end
        self._root.extend_states(len(states) - 1)
        self._priorities += [0] * (len(states) - 1)
        self._new_states = states

        # place the first state in the empty spot and the rest at the end
        replaced_state_num = states[0].state_num
        if not self._states[replaced_state_num] is None:
            raise InternalError("Replaced state was not None")

        self._states[replaced_state_num] = states[0]
        self._states += states[1:]

    def suggest_action(self):
        """Suggest the optimal action to take from the current state.

        Returns:
            action (tuple): The optimal action from the current state

        """
        if self._current_state is None:
            raise StateNotSetError(logger)

        return self._current_state.get_optimal_action()

    def get_legal_actions(self):
        """Returns all the legal actions from the current_state."""
        if self._current_state is None:
            raise StateNotSetError(logger)

        return self._current_state.get_legal_actions()

    def update(self, action, measurements, reward):
        """Updates model after taking given action and ending up in the state corresponding to the measurements.

        Args:
            action (tuple): The recent taken action
            measurements (dict): The measurements collected after the action
            reward (double): The reward acquired through the specific action

        """
        if self._current_measurements is None:
            raise StateNotSetError(logger)

        # TODO move this where the splitting is decided
        self._current_state = self._root.get_state(self._current_measurements)

        # determine the new state
        new_state = self._root.get_state(measurements)
        new_num = new_state.state_num

        # store the transition information
        trans_data = (self._current_measurements, measurements, action, reward)
        self._current_state.store_transition(trans_data, new_num)

        # update the qstate
        q_state = self._current_state.get_q_state(action)
        q_state.update(new_state, reward)

        # update the model values according to the chosen algorithm
        if self._update_algorithm == SINGLE_UPDATE:
            self._q_update(q_state)
            self._current_state.update_value()
        elif self._update_algorithm == VALUE_ITERATION:
            self.value_iteration()
        elif self._update_algorithm == PRIORITIZED_SWEEPING:
            self.prioritized_sweeping()

        # consider splitting the initial_state
        if self._allow_splitting:
            self.split()

        # update the current state and store the last measurements
        self._current_state = new_state
        self._current_measurements = measurements

    def retrain(self):
        """Retrains the model with the transition data temporarily stored in the model."""
        for m1, m2, a, r in self._transition_data:
            # Determine the states involved in the transition
            old_state = self._root.get_state(m1)
            new_state = self._root.get_state(m2)

            # Store the transition data in the initial state of the transition
            new_num = new_state.state_num
            old_state.store_transition((m1, m2, a, r), new_num)

            # Update the qstate
            q_state = old_state.get_q_state(a)
            q_state.update(new_state, r)

        # clear the transition data from the model
        self._transition_data = []

    def chain_split(self):
        """Repeatedly attempts to split all the nodes until no splits are possible."""
        num_splits, did_split = 0, True
        while did_split:
            did_split = False
            states = list(self._states)
            for state in states:
                if self.split(state=state):
                    did_split = True
                    num_splits += 1

            if did_split:
                self.value_iteration()

        logger.debug("Chain splitting complete after {} splits".format(num_splits))

    def _q_update(self, q_state):
        """Runs a single update for the Q-value of the given state-action pair."""
        new_q_value = 0
        for i in range(len(self._states)):
            t = q_state.get_transition(i)
            r = q_state.get_reward(i)
            new_q_value += t * (r + self._discount * self._states[i].value)

        q_state.q_value = new_q_value

    def _v_update(self, state):
        """Recalculates values of all Q-states of the given state, updates the value of the state accordingly."""
        for q_state in state.q_states:
            self._q_update(q_state)

        state.update_value()

    def value_iteration(self, error=None):
        """Runs the value iteration algorithm on the model."""
        if error is None:
            error = self._update_error

        start = timer()
        repeat = True
        while repeat:
            repeat = False
            for state in self._states:
                old_value = state.value
                self._v_update(state)
                new_value = state.value
                if abs(old_value - new_value) > error:
                    repeat = True
        end = timer()

        logger.debug("Value iteration complete after {} seconds".format(end - start))

    def prioritized_sweeping(self, initial_state=None, error=None, max_updates=None, debug=False):
        """Runs prioritized sweeping starting from the given state."""
        if self._current_state is None and initial_state is None:
            raise StateNotSetError(logger)

        if initial_state is None:
            initial_state = self._current_state
        if error is None:
            error = self._update_error
        if max_updates is None:
            max_updates = self._max_updates

        # transition probabilities have changed for the initial state
        reverse_transitions = [{} for _ in self._states]
        for state in self._states:
            for state_num, t in state.get_max_transitions().items():
                reverse_transitions[state_num][state.state_num] = t

        state = initial_state
        for i in range(max_updates):

            # update the state value
            old_value = state.get_value()
            self._v_update(state)
            new_value = state.get_value()
            delta = abs(new_value - old_value)

            # update the priorities of the predecessors
            rev_transitions = reverse_transitions[state.state_num]
            for state_num, t in rev_transitions.items():
                self._priorities[state_num] = max(t * delta, self._priorities[state_num])

            # zero the updated state's priority
            self._priorities[state.state_num] = 0

            # Choose the next max priority state
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

    def stat_test(self, x1, x2):
        stat = None
        if self._statistical_test == STUDENT_TTEST:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _, stat = stats.ttest_ind(x1, x2)
        elif self._statistical_test == WELCH_TTEST:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _, stat = stats.ttest_ind(x1, x2, equal_var=False)
        elif self._statistical_test == MANN_WHITNEY_UTEST:
            try:
                _, stat_one_sided = stats.mannwhitneyu(x1, x2)
                stat = 2 * stat_one_sided
            except ValueError:
                stat = 1
        elif self._statistical_test == KOLMOGOROV_SMIRNOV:
            _, stat = stats.ks_2samp(x1, x2)
        return stat

    def split(self, state=None):
        # Initialize timer
        start = timer()

        # Check if state exists
        if state is None:
            state = self._current_state

        # Collect the transitions that occurred after taking the optimal action
        optimal_action = state.get_optimal_action()
        transitions = [t for ts in state.transition_data for t in ts if t[2] == optimal_action]

        if self._split_criterion == MID_POINT and len(transitions) == 0:
            return False

        # Mid point splitting
        incr_measurements, decr_measurements = [], []
        best_incr_par, best_decr_par = 0, 0
        # Other point splitting types
        q_values = []

        if self._considered_transitions:
            # Partition the transitions to those that would increase or decrease the q-value
            if self._split_criterion == MID_POINT:
                for m1, m2, a, r in transitions:
                    new_state_value = self._root.get_state(m2).value
                    q_value = r + self._discount * new_state_value
                    if q_value >= state.value:
                        incr_measurements.append(m1)
                    else:
                        decr_measurements.append(m1)
            else:
                for m1, m2, a, r in transitions:
                    new_state_value = self._root.get_state(m2).get_value()
                    q_value = r + self._discount * new_state_value
                    q_values.append((m1, q_value))
        else:
            # Partition the transitions to those that gave higher or lower rewards than average
            if self._split_criterion == MID_POINT:
                average_rewards = mean([t[3] for t in transitions])
                for m1, m2, a, r in transitions:
                    if r >= average_rewards:
                        incr_measurements.append(m1)
                    else:
                        decr_measurements.append(m1)
            else:
                for m1, m2, a, r in transitions:
                    q_values.append((m1, r))

        if min(len(incr_measurements), len(decr_measurements)) < self._min_measurements \
                and self._split_criterion == MID_POINT:
            return False

        if self._split_criterion == INFO_GAIN:
            # Calculate the information required for the current state
            state_value = state.get_value()
            high_q = sum(1 for q in q_values if q[1] > state_value)
            low_q = len(q_values) - high_q
            state_info = self._info(high_q, low_q)

        # Find the splitting point with the lowest null hypothesis probability
        best_par, best_point = None, None
        lowest_error = 1
        # Max point splitting
        max_diff = 0
        # Info Gain Splitting
        min_info = float('inf')

        if self._split_criterion == MID_POINT:
            for par in self._parameters:
                incr_par = [m[par] for m in incr_measurements]
                decr_par = [m[par] for m in decr_measurements]
                t1_error = self.stat_test(incr_par, decr_par)

                if t1_error < lowest_error:
                    lowest_error = t1_error
                    best_par = par
                    best_incr_par = incr_par
                    best_decr_par = decr_par
        else:
            for par in self._parameters:
                par_values = sorted([(q[0][par], q[1]) for q in q_values])
                # Only consider points that leave at least min_measurements points on either side
                for i in range(self._min_measurements, len(transitions) - self._min_measurements + 1):
                    # Only split between distinct measurements
                    if par_values[i][0] == par_values[i - 1][0]:
                        continue

                    low_values = [p[1] for p in par_values[:i]]
                    high_values = [p[1] for p in par_values[i:]]

                    if self._split_criterion == INFO_GAIN:
                        low_incr = sum(1 for q in low_values if q > state_value)
                        high_incr = sum(1 for q in high_values if q > state_value)
                        low_decr = len(low_values) - low_incr
                        high_decr = len(high_values) - high_incr
                        info = self._expected_info(low_incr, low_decr, high_incr, high_decr)

                        if info < min_info:
                            min_info = info
                            best_par = par
                            best_point = 0.5 * (par_values[i][0] + par_values[i - 1][0])

                        continue

                    t1_error = self.stat_test(low_values, high_values)

                    if self._split_criterion == MAX_POINT:
                        if t1_error > self._split_error:
                            continue
                        low_avg = mean(low_values)
                        high_avg = mean(high_values)
                        if abs(high_avg - low_avg) > max_diff:
                            max_diff = abs(high_avg - low_avg)
                            best_par = par
                            best_point = (par_values[i][0] + par_values[i - 1][0]) / 2
                    else:
                        if t1_error < lowest_error:
                            lowest_error, best_par = t1_error, par
                            best_point = (par_values[i][0] + par_values[i - 1][0]) / 2

        if self._split_criterion in [MID_POINT, ANY_POINT]:
            if best_par is None or lowest_error > self._split_error:
                return False
        elif self._split_criterion == MAX_POINT:
            if best_par is None:
                return False
        else:
            if best_par is None or min_info > state_info:
                return False

        if self._split_criterion == MID_POINT:
            incr_mean = mean(best_incr_par)
            decr_mean = mean(best_decr_par)
            best_point = (incr_mean + decr_mean) / 2

        # Perform a split at the selected point
        state.split(best_par, [best_point])
        self._splits[best_par] += 1

        # Recalculate the values of the new states generated by the split
        for state in self._new_states:
            self._v_update(state)
        self._new_states = []

        end = timer()

        logger.debug("Split with {} at {} with {} {} after {} seconds"
                     .format(best_par, best_point, self._split_criterion, max_diff, end - start))
        return True

    def _expected_info(self, p1, n1, p2, n2):
        """Returns the expected information required as per Quinlan's ID3."""
        s = p1 + n1 + p2 + n2
        s1 = p1 + n1
        s2 = p2 + n2

        return (s1 / s) * self._info(p1, n1) + (s2 / s) * self._info(p2, n2)

    @staticmethod
    def _info(p, n):
        """Returns the expected classification information as per Quinlan's ID3."""
        if n <= 0 or p <= 0:
            return 0
        else:
            return -(p / (p + n)) * math.log(p / (p + n), 2) - (n / (p + n)) * math.log(n / (p + n), 2)

    def get_percent_not_taken(self):
        """Returns the percentage of actions that have never been taken."""
        total = 0
        not_taken = 0
        for state in self._states:
            for q_state in state.q_states:
                total += 1
                if q_state.get_num_taken() == 0:
                    not_taken += 1

        return not_taken / total

    def print_transition_data(self):
        """Prints all the stored transition data for all the states in the model."""
        if self._transition_data:
            print("Temporary data in the model:")
            pprint(self._transition_data)

        for state in self._states:
            print("State %d:" % state.state_num)
            pprint(state.transition_data)

    def print_model(self, detailed=False):
        """Prints the states of the model. If detailed is True it also prints the Q-states."""
        for state in self._states:
            if detailed:
                state.print_detailed()
                print("")
            else:
                print(state)

    def print_state_details(self):
        """Prints the Q-states and the transition and reward lists for each Q-state."""
        for state in self._states:
            print("Node %d:" % state.state_num)
            for q_state in state.q_states:
                print(q_state)
                # print("Transitions:", qs.transitions)
                # print("Rewards:    ", qs.rewards)
            print("")
