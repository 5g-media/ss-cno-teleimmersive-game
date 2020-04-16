import json
import logging.config
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import BaseCommand

from runner.config import KAFKA_SPECTATOR_METRICS_TOPIC
from runner.models import Spectator, VTranscoder
from runner.tasks import delete_spectator
from runner.utils.kafka import KafkaExporter, init_consumer_and_subscribe

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('spectators')


def create_spectator_and_init(kafka_exporter, client_id, group_id):
    """Creates a new spectator object for each transcoder and inits.

    Parameters
    ----------
    kafka_exporter : KafkaExporter
        A instance of the KafkaExporter Class
    client_id : str
        The id of the spectator client
    group_id : str
        The id of the spectator group

    """
    # Create spectators
    spectator_trans_1 = Spectator.objects.create(group_id=group_id, client_id=client_id, transcoder_no=1)
    spectator_trans_2 = Spectator.objects.create(group_id=group_id, client_id=client_id, transcoder_no=2)
    # Schedule deletion of spectators after an hour
    delete_on = datetime.utcnow() + timedelta(hours=1)
    delete_spectator.apply_async((spectator_trans_1.id,), eta=delete_on)
    delete_spectator.apply_async((spectator_trans_2.id,), eta=delete_on)
    # Log Vdu object creation
    logger.info('[Group: {}, Client: {}] New Spectator object was recorded and created.'.format(group_id, client_id))
    # Initialize spectator with quality 0
    kafka_exporter.set_vtranscoder_spectator_profile(client_id, group_id, {1: 0, 2: 0})


def record_and_init_spectators():

    # Initialize Kafka consumer and subscribe
    consumer = init_consumer_and_subscribe(topic=KAFKA_SPECTATOR_METRICS_TOPIC,
                                           group_id_suffix='IMMERSIVE_MEDIA_LCM')

    # Initialize Kafka Producer
    kafka_exporter = KafkaExporter()

    # Delete existing spectators & transcoders
    Spectator.objects.all().delete()
    VTranscoder.objects.all().delete()

    for msg in consumer:
        try:
            payload = json.loads(msg.value.decode('utf-8', 'ignore'))
        except json.JSONDecodeError:
            continue

        client_id = payload['client_id']
        group_id = payload['group_id']

        # Check if spectator exists
        spectators = Spectator.objects.filter(client_id=client_id, group_id=group_id)
        if spectators.exists():
            # logger.debug('[Group: {}, Client: {}] Spectator has already been recorded.'.format(group_id, client_id))
            continue
        # Create spectators and init
        create_spectator_and_init(kafka_exporter, client_id, group_id)


class Command(BaseCommand):
    def handle(self, *args, **options):
        record_and_init_spectators()
