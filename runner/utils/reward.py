import math


def cost_reward(gpu_users):
    """Computes a cost-based reward.

    Parameters
    ----------
    gpu_users : float
        Percentage of GPU users

    Returns
    -------
    reward : float
        A cost-based reward

    """
    reward = 1
    if gpu_users != 0:
        if 0 < gpu_users < 0.5:
            reward = -2
        if 0.5 <= gpu_users < 0.75:
            reward = -1
        elif gpu_users > 0.75:
            reward = 1
    return reward


def measurement_reward(old_measurements, new_measurements):
    """Computes the reward based on action, old and new frame rate and bit rate.

    Parameters
    ----------
    old_measurements : dict
        A dictionary of the previous measurements
    new_measurements : dict
        A dictionary of the latest measurements

    Returns
    -------
    reward : float
        The computed measurement-based reward

    """
    reward = 0
    for metric in ['framerate_aggr', 'bitrate_aggr']:
        old_value, new_value = old_measurements[metric], new_measurements[metric]
        old_value = 0.001 if old_value == 0 else old_value
        reward += ((new_value - old_value) / old_value) * 100
    if reward == 0:
        return reward
    magnitude = int(math.log10(abs(reward)))
    if magnitude >= 1:
        reward /= math.pow(10, magnitude)
    return reward


def no_of_profiles_reward(old_no_of_profiles, new_no_of_profiles):
    """Compute the reward based on the number of profiles

    Parameters
    ----------
    old_no_of_profiles : int
        The number of profiles produced before
    new_no_of_profiles
        The number of profiles that are produced now

    Returns
    -------
    reward : int
        The reward based on the number of profiles

    """
    return old_no_of_profiles - new_no_of_profiles


def qoe_and_cost_combined_reward(qoe_sum, transcoding_cost):
    """Computes QoE reward, taking the cost into account

    Parameters
    ----------
    qoe_sum : float
        The sum of Mean Opinion Scores for all working spectators
    transcoding_cost : float
        An arbitrary transcoding cost

    Returns
    -------
    reward : float
        A reward based on the QoE of all spectators and cost

    """
    if qoe_sum > transcoding_cost:
        reward = qoe_sum / transcoding_cost
    else:
        reward = -(1 + (qoe_sum / transcoding_cost))
    if reward == 0:
        return reward
    magnitude = int(math.log10(abs(reward)))
    if magnitude >= 1:
        reward /= math.pow(10, magnitude)
    return reward


def qoe_reward(old_mos, new_mos):
    """Computes the reward based on action, prior and new Mean Opinion Score (MOS)

    Parameters
    ----------
    old_mos : float
        The initial MOS value
    new_mos : float
        The new MOS value

    Returns
    -------
    reward : float
        The computed reward

    """
    old_mos = 0.001 if old_mos == 0 else old_mos
    reward = ((new_mos - old_mos) / old_mos) * 100
    if reward == 0:
        return reward
    magnitude = int(math.log10(abs(reward)))
    if magnitude >= 1:
        reward /= math.pow(10, magnitude)
    return reward
