import json
import logging.config

from django.conf import settings
from django.core.management import BaseCommand
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from runner.cno_algorithm_runner import CnoAlgorithmRunner
from simulation.config import KAFKA_TOPIC_PATTERN, KAFKA_API_VERSION, KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_GROUP_ID, \
    KAFKA_PLANNING_TOPIC

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


def simulate():
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER, client_id=KAFKA_CLIENT_ID, enable_auto_commit=True,
                             value_deserializer=lambda v: json.loads(v.decode('utf-8', 'ignore')),
                             api_version=KAFKA_API_VERSION, group_id=KAFKA_GROUP_ID)
    consumer.subscribe(pattern=KAFKA_TOPIC_PATTERN)
    logger.debug('Initialized Kafka Consumer & subscribed to pre-processing topic')

    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, client_id=KAFKA_CLIENT_ID,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                             api_version=KAFKA_API_VERSION, )
    logger.debug('Initialized Kafka Producer')

    # Initialize CNO Algorithm Runner for Simulation
    runner = CnoAlgorithmRunner('simulation')
    # Train MDP Model
    runner.train()

    # Run simulation for 100 collections of measurements
    awaiting_reward, old_measurements = False, {}
    for msg in consumer:
        if msg.key is None:
            continue
        if msg.key.decode('utf-8') != 'sim':
            continue

        if awaiting_reward:
            # Get reward
            reward = runner.get_reward((action_type, action_value), old_measurements, measurements)
            # Record experience and update
            runner.update((action_type, action_value), measurements, reward)
            old_measurements = measurements
            awaiting_reward = False
            continue

        # Get measurements, set state, get suggested action
        measurements = msg.value['measurements']
        runner.set_state(measurements)
        action_type, action_value = runner.get_suggested_action()
        logger.info('Received set of measurements {}. Suggested Action: {} {}'
                    .format(measurements, action_type, action_value))

        # Remove measurements from message
        # msg.pop('measurements')

        # Record the action and publish to (P)lanning for (E)xecution of action
        # analysis['analysis'] = {'action': action_type, 'value': action_value}

        # Publish to Kafka
        request = producer.send(KAFKA_PLANNING_TOPIC, {'analysis': {'action': action_type, 'value': action_value}})
        try:
            request.get(timeout=60)
        except KafkaError as ke:
            logger.error(ke)

    runner.model.print_state_details()

    logger.debug('Simulation has finished')


class Command(BaseCommand):
    def handle(self, *args, **options):
        simulate()
