from markovdp.q_state import QState


class QStateDT(QState):
    """Class to represent a q-state in a Decision Tree MDP model."""

    def remove_state(self, state_num):
        """Removes the transition and reward information for that Q-state.

        Args:
            state_num (int): The unique state number in the MDP model

        """
        self._action_taken_times -= self._transitions[state_num]
        self._transitions[state_num] = 0
        self._rewards[state_num] = 0

    def extend_states(self, num_states):
        """Adds extra states to the reward and transition info.

        Args:
            num_states (int): The number of the extra states to add.

        """
        self._total_states += num_states
        self._transitions += [0] * num_states
        self._rewards += [0] * num_states
