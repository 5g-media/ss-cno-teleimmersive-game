import json
import logging
import random
import time
from datetime import datetime

from django.core.management import BaseCommand
from kafka import KafkaProducer
from kafka.errors import KafkaError

from cno.settings.base import LOGGING
from runner.config import KAFKA_API_VERSION, KAFKA_SERVER
from simulation.constants import mano

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def publish_metrics_for_qoe():
    # Kafka Producer Set Up
    # https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, api_version=KAFKA_API_VERSION,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    while True:
        # Push the metric values in batch per container ID
        prep_metric = {
            'mano': mano,
            'measurements':
                {
                    'working_fps': 11,
                    'output_mesh_size_bytes': 45000,
                    'output_textures_size_bytes': 25000,
                    'container_network_transmit_packets_dropped_total': random.uniform(0, 2)
                },
            'timestamp': datetime.now().isoformat()
        }
        request = producer.send('ns.instances.prep', key=b'qoe', value=prep_metric)
        try:
            request.get(timeout=60)
        except KafkaError as ke:
            logger.error(ke)

        time.sleep(30)


class Command(BaseCommand):
    def handle(self, *args, **options):
        publish_metrics_for_qoe()
