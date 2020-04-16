from markovdp.exceptions import ParameterError, InternalError
from markovdp.q_state_dt import QStateDT


class DecisionNode(object):
    """DecisionNode Class.

    A decision node in the decision tree. This will only hold references to
    other nodes and does not represent a state of the MDP.

    Args:
        parent (DecisionNode)
        model (MDPModel)

    """

    def __init__(self, parent, model, parameter, limits, actions,
                 initial_q_values, num_states, replaced_state_num):

        self._parent = parent
        self._parameter = parameter
        self._limits = limits
        self._total_states = num_states + len(limits)
        self._model = model

        self._children = [LeafNode(self, model, actions, initial_q_values,
                                   replaced_state_num, num_states + len(limits))]

        for i in range(len(limits)):
            self._children.append(LeafNode(self, model, actions, initial_q_values,
                                           num_states + i, num_states + len(limits)))

    @staticmethod
    def is_leaf():
        """This is not a leaf node."""
        return False

    def replace_node(self, old_node, new_node):
        """Replaces given child node with the new one. This happens when one of the child nodes is split.

        Args:
            old_node (LeafNode): The leaf node under replacement
            new_node (DecisionNode): The new node to replace the old one

        """
        old_state_num = old_node.state_num

        for i in range(len(self._children)):
            if self._children[i].is_leaf() and self._children[i].state_num == old_state_num:
                self._children[i] = new_node
                return

        raise InternalError("Tried to replace a node that did not exist", self._model.logger)

    def split(self, param, limits):
        """Splits the children nodes. This should only be used when initializing the model with multiple parameters."""
        for child in self._children:
            child.split(param, limits)

    def remove_state(self, state_num):
        """Removes the transition and reward information for that state from the subtree."""
        for child in self._children:
            child.remove_state(state_num)

    def extend_states(self, num_states):
        """Adds num_states extra states to the reward and transition info for all states in the subtree."""
        self._total_states += num_states
        for child in self._children:
            child.extend_states(num_states)

    def get_leaves(self):
        """Returns all the leaves in the current subtree."""
        leaves = []
        for child in self._children:
            leaves += child.get_leaves()

        return leaves

    def get_state(self, measurements):
        """Returns the state on this subtree that corresponds to the given measurements.

        Args:
            measurements (dict): A dictionary of collected measurements

        Returns:
            state (State): The state corresponding to the measurements

        """
        if self._parameter not in measurements:
            raise ParameterError("Missing measurement: " + self._parameter, self._model.logger)

        m = measurements[self._parameter]
        for i, l in enumerate(self._limits):
            if m < l:
                return self._children[i].get_state(measurements)

        return self._children[-1].get_state(measurements)


class LeafNode(object):
    def __init__(self, parent, model, actions, q_values, state_num, num_states):

        self._parent = parent
        self._actions = actions
        self._initial_qvalues = q_values
        self._total_states = num_states
        self._model = model
        self._state_num = state_num
        self._transition_data = [[]] * num_states
        self._times_visited = 0
        self._value = 0
        self._q_states = []

        for name, values in actions.items():
            if values is None:
                action = (name, None)
                q_state = QStateDT(action, num_states, q_values)
                self._q_states.append(q_state)
                continue
            for value in values:
                action = (name, value)
                q_state = QStateDT(action, num_states, q_values)
                self._q_states.append(q_state)

    @property
    def q_states(self):
        """Gets all the qstates for all the actions from this state."""
        return self._q_states

    @property
    def state_num(self):
        """Get unique id for node in state."""
        return self._state_num

    @state_num.setter
    def state_num(self, state_num):
        self._state_num = state_num

    @property
    def transition_data(self):
        """Gets the list of measurements that are stored in this state."""
        return self._transition_data

    @property
    def value(self):
        """Gets the value of the state."""
        return self._value

    @staticmethod
    def is_leaf():
        """This is a leaf node."""
        return True

    def split(self, param, limits):
        """Replaces leaf node with a decision node in the decision tree and updates all the MDP states accordingly."""

        # Remove the leaf node from the model
        self._model.remove_state(self._state_num)

        # Create the decision node to replace it and add it to the model
        decision_node = DecisionNode(self._parent, self._model, param, limits, self._actions,
                                     self._initial_qvalues, self._total_states, self._state_num)
        self._model.add_states(decision_node.get_leaves())
        self._parent.replace_node(self, decision_node)

        # Retrain the model with the stored data
        self._model.retrain()

    def get_optimal_action(self):
        """The optimal action is the one with the biggest Q-value."""
        max_value, best_action = float("-inf"), None
        for q_state in self._q_states:
            if max_value < q_state.q_value:
                max_value = q_state.q_value
                best_action = q_state.action

        return best_action

    def get_legal_actions(self):
        """Returns all the possible actions from this state."""
        return [q_state.action for q_state in self._q_states]

    def store_transition(self, data, new_state_num):
        """Stores the given info for a transition to the given state number."""
        self._transition_data[new_state_num].append(data)
        self._times_visited += 1

    def get_leaves(self):
        """Returns all the leaves contained in this subtree, which is itself."""
        return [self]

    def get_state(self, measurements):
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
        return self

    def get_q_state(self, action):
        """Returns the qstate that corresponds to the given action from this state."""
        for q_state in self._q_states:
            if q_state.action == action:
                return q_state

    def update_value(self):
        """Updates the value of the state to be equal to the value of the best Q-state."""
        self._value = max([q_state.q_value for q_state in self._q_states])

    def remove_state(self, state_num):
        """Removes the transition and reward information for that state."""
        # if this is the state to be removed store all the transition data to the model
        if state_num == self._state_num:
            for data in self._transition_data:
                self._model.store_transition_data(data)

        # else only remove the transition data towards the removed state
        else:
            data = self._transition_data[state_num]
            self._transition_data[state_num] = []
            self._model.store_transition_data(data)

        # remove the information from the qstates
        num_visited = 0
        for q_state in self._q_states:
            num_visited += q_state.get_num_transitions(state_num)
            q_state.remove_state(state_num)
        self._times_visited -= num_visited

    def extend_states(self, num_states):
        """Adds num_states extra states to the reward and transition info."""
        self._total_states += num_states
        self._transition_data += [[] for _ in range(num_states)]
        for q_state in self._q_states:
            q_state.extend_states(num_states)

    def get_max_transitions(self):
        """Returns a dict containing the maximum transition probability to each state for each action."""
        transitions = {}
        for i in range(self._total_states):
            for q_state in self._q_states:
                if q_state.has_transition(i):
                    if i in transitions:
                        transitions[i] = max(transitions[i], q_state.get_transition(i))
                    else:
                        transitions[i] = q_state.get_transition(i)

        return transitions

    def __str__(self):
        return "State {}, visited = {}".format(self._state_num, self._times_visited)

    def __repr__(self):
        return str(self)

    def print_detailed(self):
        """Prints the node along with its Q-states."""
        print(self)
        for q_state in self._q_states:
            print(q_state)
