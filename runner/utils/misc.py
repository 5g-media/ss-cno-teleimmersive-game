import json
import logging.config
from datetime import timedelta, datetime

from django.conf import settings
from django.db.models import Sum

from markovdp.constants import NO_OP
from runner.constants import GPU_PRODUCED_PROFILES
from runner.models import Spectator, VTranscoder
from runner.tasks import delete_vtranscoder

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


def get_or_create_vtranscoder(payload):
    """Checks existence of a VTranscoder object. It creates one if it does not exist

    Parameters
    ----------
    payload : dict
        A received vTranscoder payload

    """
    vnf_id = payload['mano']['vnf']['id']
    try:
        vtranscoder = VTranscoder.objects.get(vnf_id=vnf_id)
    except VTranscoder.DoesNotExist:
        vtranscoder = VTranscoder.objects.create(vnf_id=vnf_id, processing_unit='cpu',
                                                 produced_qualities=json.dumps([0]), mano_payload=json.dumps(payload))
        delete_on = datetime.utcnow() + timedelta(hours=1)
        delete_vtranscoder.apply_async((vtranscoder.id,), eta=delete_on)
    return vtranscoder


def update_transcoder(processing_unit=None, produced_profiles=None, vnf_id=None):
    """Updates the processing unit and produced profiles of the vTranscoders

    Parameters
    ----------
    processing_unit : str
        The vTranscoder processing unit
    produced_profiles : list
        The vTranscoder produced profiles
    vnf_id : str
        The VNF ID of the transcoder to update

    """
    vtranscoders = VTranscoder.objects.filter(vnf_id=vnf_id)
    if processing_unit is None:
        vtranscoders.update(produced_qualities=json.dumps(produced_profiles))
    else:
        vtranscoders.update(processing_unit=processing_unit,
                            produced_qualities=json.dumps(produced_profiles))


def get_or_create_spectator(payload, kafka_exporter):
    """Gets an existing Spectator object or creates a new one.

    Parameters
    ----------
    payload : dict
        A message payload received from the Kafka Bus
    kafka_exporter : KafkaExporter
        An instance of the KafkaExporter Class

    Returns
    -------
    spectator : Spectator
        A Spectator object

    """
    spectator = payload['spectator']
    group_id = spectator['group_id']
    client_id = spectator['client_id']
    transcoder_no = int(payload['mano']['vnf']['index'])
    other_transcoder_no = 1 if transcoder_no == 2 else 2

    try:
        spectator_obj = Spectator.objects.get(group_id=group_id, client_id=client_id, transcoder_no=transcoder_no)
        other_transcoder_profile = Spectator.objects.get(group_id=group_id, client_id=client_id,
                                                         transcoder_no=other_transcoder_no).profile
        return spectator_obj, {other_transcoder_no: other_transcoder_profile}
    except Spectator.DoesNotExist:
        spectator_obj = Spectator.objects.create(group_id=group_id, client_id=client_id, transcoder_no=transcoder_no)
        # Log Vdu object creation
        logger.debug('New Spectator object with client_id {}, belonging to group {} was created.'
                     .format(client_id, group_id))
        # If the spectator is new, advise it to read from quality 0
        if Spectator.objects.filter(group_id=group_id, client_id=client_id).count() == 1:
            kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, {1: 0, 2: 0})
        other_transcoder_profile = Spectator.objects.get(group_id=group_id, client_id=client_id,
                                                         transcoder_no=other_transcoder_no).profile
        return spectator_obj, {other_transcoder_no: other_transcoder_profile}


def update_spectator(spectator, action_type, action_value, measurements, mos):
    """Updates a Spectator object.

    Parameters
    ----------
    spectator : Spectator
        The Spectator object to update
    action_type : str
        The type of action
    action_value : double
        The value of action
    measurements : dict
        A dictionary of measurements
    mos : double
        The Mean Opinion Score

    """
    # Further updates for spectator under consideration
    spectator.action_type = action_type
    spectator.action_value = action_value if action_type != NO_OP else -1
    spectator.profile = spectator.profile if action_type == NO_OP else action_value
    spectator.has_received_metrics = True
    spectator.measurements = json.dumps(measurements)
    spectator.mos_score = mos
    spectator.save()
    logger.debug('[Group: {}, Client: {}] Update of spectator was successful'
                 .format(spectator.group_id, spectator.client_id))


def check_for_unconsumed_qualities(vtranscoder_produced_qualities, transcoder_no):
    """Checks for unconsumed vTranscoder qualities

    Parameters
    ----------
    vtranscoder_produced_qualities : list
        The list of currently produced vTranscoder qualities
    transcoder_no : int
        The number of the transcoder

    Returns
    -------
    actual_consumed_qualities : list
        The list of qualities consumed by the spectators

    """
    unconsumed_qualities = []
    for quality in vtranscoder_produced_qualities[1:]:
        spectators_on_quality = Spectator.objects.filter(profile=quality, transcoder_no=transcoder_no)
        if not spectators_on_quality.exists():
            unconsumed_qualities.append(quality)
    if len(unconsumed_qualities) > 0:
        vtranscoder_produced_qualities = \
            [q for q in vtranscoder_produced_qualities if q not in unconsumed_qualities]
        logger.debug('Detected that qualities {} produced by the vTranscoders are not consumed. '
                     'Stopping production of these qualities'.format(unconsumed_qualities))
    return vtranscoder_produced_qualities


def is_gpu_needed(produced_profiles):
    """Checks if GPU is currently needed.

    Parameters
    ----------
    produced_profiles : list
        The profiles currently produced by the vTranscoders

    Returns
    -------
    True if GPU is needed, else False

    """
    profiles_needing_gpu = [x for x in produced_profiles if x in GPU_PRODUCED_PROFILES]
    return False if profiles_needing_gpu == [] else True


def percentage_of_gpu_users(transcoder_no):
    """Calculate percentage of spectators consuming a GPU profile.

    Parameters
    ----------
    transcoder_no : int
        The transcoder number to count GPU users for

    Returns
    -------
    percentage : float
        The percentage of spectators consuming a GPU profile.

    """
    return Spectator.objects.filter(transcoder_no=transcoder_no, profile__in=GPU_PRODUCED_PROFILES).count() / \
           Spectator.objects.filter(transcoder_no=transcoder_no).count()


def update_measurements(measurements, qoe_mos, quality, vtranscoder_produced_profiles, transcoder_no):
    """Update measurements with custom computations.

    The following metrics are not received from the (M)onitoring but instead, they are computed
    in the CNO. These metrics include the Mean Opinion Score, the number of profiles that are
    produced, the quality, the percentage of the users utilizing the GPU, the sum of MOS for all
    spectators and an arbitrary transcoding cost.

    Parameters
    ----------
    measurements : dict
        A collection of measurements received from Monitoring
    qoe_mos : float
        The computed Mean Opinion Score
    quality : int
        The quality consumed by the spectator
    vtranscoder_produced_profiles : list(int)
        The list of produced profiles
    transcoder_no : int
        The transcoder number denoting the player 1 or 2

    Returns
    -------
    measurements : dict
        The updated dict of measurements

    """
    measurements['mean_opinion_score'] = qoe_mos
    measurements['quality'] = quality
    measurements['no_of_profiles_produced'] = len(vtranscoder_produced_profiles)
    measurements['percentage_of_gpu_users'] = percentage_of_gpu_users(transcoder_no)
    measurements['qoe_sum'] = \
        Spectator.objects.filter(transcoder_no=transcoder_no).aggregate(Sum('mos_score'))['mos_score__sum']
    measurements['transcoding_cost'] = \
        0.5 + (1 if 1 in vtranscoder_produced_profiles else 0) + (1 if 2 in vtranscoder_produced_profiles else 0) + \
        (1 if (1 in vtranscoder_produced_profiles and 2 in vtranscoder_produced_profiles) else 0) + \
        (15 if is_gpu_needed(vtranscoder_produced_profiles) else 0)
    measurements['produced_profiles'] = vtranscoder_produced_profiles
    return measurements
