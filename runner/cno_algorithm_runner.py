import json
import logging.config
import os
import os.path

from django.conf import settings

from markovdp.constants import MDP, MDP_DT, NO_OP
from markovdp.mdp_dt_model import MDPDTModel
from markovdp.mdp_model import MDPModel
from runner.constants import NO_OP
from runner.utils import reward as rewards

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


class CnoAlgorithmRunner(object):
    """CNO Algorithm Runner Class.

    A wrapper class for the MDP and MDPDT model classes, responsible
    for executing the MDP-based algorithmic flows.

    """
    REWARD_CRITERIONS = \
        ('cost', 'qoe', 'qoe_and_cost_combined', 'measurements', 'no_of_profiles')

    def __init__(self, conf_data):
        """CNO Algorithm Runner Constructor Class.

        Parameters
        ----------
        conf_data : dict
            A dictionary for the configuration of the algorithm

        """
        # Initialize the proper model
        self._model_type = conf_data['model']
        if self._model_type == MDP:
            self._model = MDPModel(conf_data)
        elif self._model_type == MDP_DT:
            self._model = MDPDTModel(conf_data)

        # Get the weights of each reward criterion
        self._reward_criterions = conf_data['reward_criterions']
        self._reward_criterions['cost'] = os.getenv('CNO_IM_COST', self._reward_criterions['cost'])
        self._reward_criterions['qoe'] = os.getenv('CNO_IM_QOE', self._reward_criterions['qoe'])
        self._reward_criterions['qoe_and_cost_combined'] = \
            os.getenv('CNO_IM_QOE_COST_COMBINED', self._reward_criterions['qoe_and_cost_combined'])
        self._reward_criterions['measurements'] = \
            os.getenv('CNO_IM_MEASUREMENTS', self._reward_criterions['measurements'])
        self._reward_criterions['no_of_profiles'] = \
            os.getenv('CNO_IM_NO_OF_PROFILES', self._reward_criterions['no_of_profiles'])

        # Set the training and result files.
        self.training_file = os.getenv('CNO_IM_TRAINING_FILE', conf_data['training_file'])
        self.results_file = os.getenv('CNO_IM_RESULTS_FILE', conf_data['results_file'])

        # No measurements have been received yet
        self.last_measurements = None

    @property
    def model(self):
        """Return the model."""
        return self._model

    @property
    def reward_criterions(self):
        """Return the reward type."""
        return self._reward_criterions

    def train(self):
        """Executes the initial training of the algorithm, provided the existence of training data."""

        # Skip training if training file does not exist
        if self.training_file is None or not os.path.isfile(self.training_file):
            logger.error('No training file, aborting training')
            return
        logger.debug("Starting training ...")

        # Randomly select experiences
        # os.system('shuf -n 1500 {} > training/random_experiences.txt'.format(self.training_file))
        # self.training_file = 'training/random_experiences.txt'

        experiences, skipped_experiences = 0, 0
        with open(self.training_file, 'r') as f:
            for line in f:
                old_measurements, action_list, new_measurements = json.loads(line)
                action = tuple(action_list)
                reward = self.get_reward(action=action,
                                         old_measurements=old_measurements,
                                         new_measurements=new_measurements)
                self._model.set_state(old_measurements)

                # Check if suggested action is legal and update model
                legal_actions = self._model.get_legal_actions()
                if action not in legal_actions:
                    skipped_experiences += 1
                    continue
                self._model.update(action, new_measurements, reward)

                experiences += 1
                if experiences % 100 == 0:
                    self._model.prioritized_sweeping()
                    logger.debug('Trained with experience {}'.format(experiences))

        logger.debug('Trained the model with {} experiences, skipped {}'.format(experiences, skipped_experiences))

    def set_state(self, measurements):
        """Sets the state of the model.

        Parameters
        ----------
        measurements : dict
            A dictionary of measurements

        """
        self.last_measurements = measurements
        self._model.set_state(measurements)
        logger.debug("State set based on measurements")

    def update(self, action, measurements, reward=None):
        """Updates the model and saves the experience.

        Parameters
        ----------
        action : tuple
            The recently taken action
        measurements : dict
            A dictionary of measurements
        reward : float
            The reward acquired after the action

        """
        if reward is None:
            reward = self.get_reward(action, self.last_measurements, measurements)
        experience = [self.last_measurements, action, measurements]
        if self.results_file is None:
            self.results_file = self.training_file
        if self.results_file is not None:
            with open(self.results_file, "a") as f:
                f.write(json.dumps(experience) + '\n')
                f.flush()
                logger.debug("Recorded experience")

        self.last_measurements = measurements
        self._model.update(action, measurements, reward)

    def set_splitting(self, split_criterion, cons_trans=True):
        """Sets the splitting criterion for MDP-DT.

        Args:
            split_criterion (str): The selected splitting criterion
            cons_trans:

        """
        if self._model_type != MDP_DT:
            logger.error("Splitting criteria apply only to MDP_DT models!")
            return

        self._model.set_splitting_criterion(split_criterion, cons_trans)

    def get_reward(self, action, old_measurements=None, new_measurements=None):
        """Computes the reward of the latest action.

        This function serves as a selector of the reward type, based on the initial configuration of the model.
        The types of the rewards that are supported include a QoE-based reward, a measurement-based reward, a
        mixed reward and a combined QoE and cost based reward.

        Parameters
        ----------
        action : tuple
            The executed action type and action value pair
        old_measurements : dict, optional
            A dictionary of the previous measurements
        new_measurements : dict, optional
            A dictionary of the last measurements

        Returns
        -------
        reward : float
            The computed reward

        """
        action_type, action_value = action
        reward = 1
        if action_type != NO_OP:
            cost_reward = 0 if self._reward_criterions['cost'] == 0 \
                else rewards.cost_reward(new_measurements['percentage_of_gpu_users'])
            measurements_reward = 0 if self._reward_criterions['measurements'] == 0 \
                else rewards.measurement_reward(old_measurements, new_measurements)
            no_of_profiles_reward = 0 if self._reward_criterions['no_of_profiles'] == 0 \
                else rewards.no_of_profiles_reward(old_measurements['no_of_profiles_produced'],
                                                   new_measurements['no_of_profiles_produced'])
            qoe_reward = 0 if self._reward_criterions['qoe'] == 0 \
                else rewards.qoe_reward(old_measurements['mean_opinion_score'], new_measurements['mean_opinion_score'])
            qoe_and_cost_combined_reward = 0 if self._reward_criterions['qoe_and_cost_combined'] == 0 \
                else rewards.qoe_and_cost_combined_reward(new_measurements['qoe_sum'],
                                                          new_measurements['transcoding_cost'])
            reward = \
                cost_reward * self._reward_criterions['cost'] + \
                measurements_reward * self._reward_criterions['measurements'] + \
                no_of_profiles_reward * self._reward_criterions['no_of_profiles'] + \
                qoe_and_cost_combined_reward * self._reward_criterions['qoe_and_cost_combined'] + \
                qoe_reward * self._reward_criterions['qoe']
        return reward * self._model.discount

    def get_legal_actions(self):
        """Retrieves the legal actions from the current state."""
        return self._model.get_legal_actions()

    def get_suggested_action(self):
        """Returns the suggested action for the current state."""
        return self._model.suggest_action()

    def set_stat_test(self, statistical_test):
        """Set statistical test for MDP-DT splitting

        Parameters
        ----------
        statistical_test : str
            The statistical test for splitting

        """
        self._model.statistical_test = statistical_test
