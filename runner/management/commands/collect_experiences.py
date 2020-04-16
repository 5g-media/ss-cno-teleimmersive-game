import argparse
import random

from django.core.management import BaseCommand

from runner.cno_algorithm_runner import CnoAlgorithmRunner
from runner.constants import SET_VTRANS_CLIENT_PROFILE
from runner.utils.kafka import KafkaExporter, init_consumer_and_subscribe
from runner.utils.misc import *
from runner.utils.qoe import compute_qoe_psnr

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('experience_collector')


def collect_experiences(mdp_conf):
    # Initialize CNO Algorithm Runner and train
    runner = CnoAlgorithmRunner(mdp_conf)

    # Initialize Kafka consumer and subscribe
    consumer = init_consumer_and_subscribe(group_id_suffix='IMMERSIVE_MEDIA_EXP_COLLECTOR')

    # Initialize Kafka Exporter
    kafka_exporter = KafkaExporter()

    for msg in consumer:
        try:
            payload = json.loads(msg.value.decode('utf-8', 'ignore'))
        except json.JSONDecodeError as jde:
            logger.error(jde)
            continue

        # TODO: Was commented-out temporarily as not applicable
        # Check if message key refers to the current use case
        # if msg.key.decode('utf-8') != use_case:
        #     continue

        # Retrieve or create Spectator
        spectator, qualities_to_consume = get_or_create_spectator(payload, kafka_exporter)
        client_id, group_id = spectator.client_id, spectator.group_id
        transcoder_no = spectator.transcoder_no

        # Check if vTranscoder object is already saved
        vtranscoder = get_or_create_vtranscoder(payload)
        vtranscoder_payload = json.loads(vtranscoder.mano_payload)
        vtranscoder_processing_unit = vtranscoder.processing_unit
        vtranscoder_produced_profiles = json.loads(vtranscoder.produced_qualities)

        # Get measurements & compute QoE
        measurements = payload['measurements']

        # Compute QoE and publish
        # TODO: Try with both PSNR-based and ITU
        # qoe_mos = compute_vq_itu(measurements['framerate_on'], measurements['bitrate_on'])
        qoe_mos = compute_qoe_psnr(measurements['framerate_aggr'], spectator.profile)
        kafka_exporter.send_qoe_for_visualization(payload, qoe_mos)

        # Updated collection of measurements
        measurements = update_measurements(measurements=measurements, qoe_mos=qoe_mos, quality=spectator.profile,
                                           vtranscoder_produced_profiles=vtranscoder_produced_profiles,
                                           transcoder_no=transcoder_no)
        logger.debug('[Group: {}, Client: {}, Player: {}]. Measurements: {}'
                     .format(spectator.group_id, spectator.client_id, transcoder_no, measurements))
        logger.debug('[Group: {}, Client: {}, Player: {}]. Current MOS: [{}]'
                     .format(spectator.group_id, spectator.client_id, transcoder_no, qoe_mos))

        # This block is entered in case at least one action has already been executed. The reward is computed
        # and the model is updated in this block of code. This will always be executed, except for the first
        # time that a collection of metrics is received for a specific spectator and there will be no need for
        # reward computation and model updates.
        if spectator.has_received_metrics:
            action_type, action_value = \
                spectator.action_type, spectator.action_value if spectator.action_type != NO_OP else None
            # Get reward
            reward = runner.get_reward(action=(action_type, action_value),
                                       old_measurements=json.loads(spectator.measurements),
                                       new_measurements=measurements)
            # Record experience and update
            runner.update((action_type, action_value), measurements, reward)
            logger.debug('Reward for action was computed and model was updated.')

        # Set state and get suggested action
        runner.set_state(measurements)
        logger.debug('State was set.')

        # Choose a random action
        action_type, action_value = random.choice([(NO_OP, None),
                                                   (SET_VTRANS_CLIENT_PROFILE, 0),
                                                   (SET_VTRANS_CLIENT_PROFILE, 1),
                                                   (SET_VTRANS_CLIENT_PROFILE, 2),
                                                   (SET_VTRANS_CLIENT_PROFILE, 3),
                                                   (SET_VTRANS_CLIENT_PROFILE, 4),
                                                   (SET_VTRANS_CLIENT_PROFILE, 5)])
        if action_type == SET_VTRANS_CLIENT_PROFILE and action_value == spectator.action_value:
            action_type, action_value = NO_OP, None
        logger.debug('[Group: {}, Client: {}, Player: {}]. Suggested action is [{}] with value [{}]'
                     .format(spectator.group_id, spectator.client_id, transcoder_no, action_type, action_value))

        # Send required actions to Execution part of MAPE
        if action_type != NO_OP:
            # If the profile to which the spectator should switch to is a GPU-produced profile then we should check
            # if the vTranscoders are currently lying on a CPU-only node. If this is the case, a command is sent to
            # the vTranscoders to be placed on a node which includes a GPU. Further essential actions are to follow.
            if action_value in GPU_PRODUCED_PROFILES and vtranscoder_processing_unit == 'cpu':
                vtranscoder_processing_unit = 'gpu'
                # kafka_exporter.set_vtranscoder_processing_unit(vtranscoder_payload, vtranscoder_processing_unit)
            # In case the suggested profile is already produced, simply send a command to the proper spectator to
            # start consuming from this profile. No further actions are required.
            if action_value in vtranscoder_produced_profiles:
                qualities_to_consume.update({transcoder_no: action_value})
                kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, qualities_to_consume)
            else:
                # Profiles no. 3, 4 and 5 are GPU-produced video profiles that should not be produced simultaneously.
                # Hence if the decision is to switch to one of these profiles, the currently produced profiles should
                # be checked to ensure that only one of these profiles is produced. In case one of these profiles is
                # indeed produced then its production continues, the decision is ignored and the the spectator will be
                # switching to the profile (out of no. 3, 4 or 5) that is produced already.
                if action_value in GPU_PRODUCED_PROFILES and (3 in vtranscoder_produced_profiles
                                                              or 4 in vtranscoder_produced_profiles
                                                              or 5 in vtranscoder_produced_profiles):
                    if action_value == 3 and 3 in vtranscoder_produced_profiles and spectator.profile != 3:
                        action_type, action_value = SET_VTRANS_CLIENT_PROFILE, 3
                        qualities_to_consume.update({transcoder_no: action_value})
                        kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, qualities_to_consume)
                    elif action_value == 4 and 4 in vtranscoder_produced_profiles and spectator.profile != 4:
                        action_type, action_value = SET_VTRANS_CLIENT_PROFILE, 4
                        qualities_to_consume.update({transcoder_no: action_value})
                        kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, qualities_to_consume)
                    elif action_value == 5 and 5 in vtranscoder_produced_profiles and spectator.profile != 5:
                        action_type, action_value = SET_VTRANS_CLIENT_PROFILE, 5
                        qualities_to_consume.update({transcoder_no: action_value})
                        kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, qualities_to_consume)
                    else:
                        kafka_exporter.send_no_action_message(payload)
                        action_type, action_value = NO_OP, None
                else:
                    # If none of the profiles no. 3 and no. 4 are currently produced, no attention has to be paid at
                    # the produced profiles as there are no issues whatsoever. The production of whichever profile is
                    # selected can start from the vTranscoder and the spectator can start its consumption.
                    vtranscoder_produced_profiles.append(action_value)
                    kafka_exporter.set_vtranscoder_profile(vtranscoder_payload, vtranscoder_produced_profiles[1:])
                    qualities_to_consume.update({transcoder_no: action_value})
                    kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, qualities_to_consume)
        else:
            # If no-action is taken send the proper message.
            kafka_exporter.send_no_action_message(payload)
        logger.debug('[Group: {}, Client: {}, Player: {}]. The action that finally executed was [{}] with value [{}]'
                     .format(spectator.group_id, spectator.client_id, transcoder_no, action_type, action_value))

        # Update Spectator with action and measurements
        update_spectator(spectator, action_type, action_value, measurements, qoe_mos)

        # Check for qualities to stop production of. If the vTranscoders produce qualities which
        # are not currently consumed by any consumer, then the production of this qualities stops.
        consumed_qualities = check_for_unconsumed_qualities(vtranscoder_produced_profiles, transcoder_no)
        if consumed_qualities != vtranscoder_produced_profiles:
            vtranscoder_produced_profiles = consumed_qualities
            kafka_exporter.set_vtranscoder_profile(vtranscoder_payload, vtranscoder_produced_profiles[1:])

        # Check if GPU is not currently needed in order to migrate to a CPU-only node. As a GPU is more
        # expensive than CPU, the vTranscoders are migrated if there is no need for GPU-produced profiles.
        if vtranscoder_processing_unit == 'gpu' and not is_gpu_needed(vtranscoder_produced_profiles):
            vtranscoder_processing_unit = 'cpu'
            # kafka_exporter.set_vtranscoder_processing_unit(vtranscoder_payload, vtranscoder_processing_unit)

        # Update vTranscoder
        update_transcoder(processing_unit=vtranscoder_processing_unit,
                          produced_profiles=vtranscoder_produced_profiles,
                          vnf_id=vtranscoder.vnf_id)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--mdp_conf', nargs=1, help="MDP Config File in JSON Format", type=argparse.FileType('r'))

    def handle(self, *args, **options):
        mdp_conf = json.load(options['mdp_conf'][0])
        collect_experiences(mdp_conf)
