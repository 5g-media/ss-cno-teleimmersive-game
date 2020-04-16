import logging

from cno.celery import app
from runner.models import Spectator, VTranscoder

logger = logging.getLogger('spectators')


@app.task
def delete_vtranscoder(vtranscoder_id):
    """Delete a Vtranscoder object asynchronously.

    Parameters
    ----------
    vtranscoder_id : int
        The ID of the VTranscoder object to delete

    """
    try:
        vtranscoder = VTranscoder.objects.get(id=vtranscoder_id)
        vtranscoder_vnf_id = vtranscoder.vnf_id
        vtranscoder.delete()
        logger.info('[vTrans: {}] Session has expired and vTranscoder has been deleted.'.format(vtranscoder_vnf_id))
    except VTranscoder.DoesNotExist as dne:
        logger.error(dne)
    except KeyError as ke:
        logger.error(ke)


@app.task
def delete_spectator(spectator_id):
    """Delete a spectator asynchronously.

    Parameters
    ----------
    spectator_id : int
        The ID of the spectator object to delete

    """
    try:
        # spectator_id = kwargs['spectator_id']
        spectator = Spectator.objects.get(id=spectator_id)
        client_id, groud_id = spectator.client_id, spectator.group_id
        spectator.delete()
        logger.info('[Group: {}, Client: {}] Session has expired and spectator has been deleted.'
                    .format(groud_id, client_id))
    except Spectator.DoesNotExist as dne:
        logger.error(dne)
    except KeyError as ke:
        logger.error(ke)
