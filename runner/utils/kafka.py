import json
import logging
from time import time

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from runner.config import KAFKA_EXEC_TOPIC, KAFKA_VTRANS_QOE_TOPIC, KAFKA_SPECTATOR_CONF_TOPIC, KAFKA_SERVER, \
    KAFKA_CLIENT_ID, KAFKA_API_VERSION, KAFKA_PREP_TOPIC, KAFKA_GROUP_ID
from runner.constants import JPEG_PROFILES

logger = logging.getLogger(__name__)


class KafkaExporter(object):
    """An exporter of messages related to UC1 (Immersive Media) to Kafka Bus.

    Methods
    -------
    publish_message(topic, payload)
        Publish a message to a Kafka topic
    set_vtranscoder_processing_unit(payloads, processing_unit)
        Set the processing unit of the transcoders
    set_vtranscoder_profile(payloads, qualities_to_produce)
        Change the produced vTranscoder profiles
    set_vtranscoder_spectator_profile(client_id, group_id, quality)
        Set the profile to be consumed by the spectators
    send_no_action_message(payload)
        Send message that no action is executed
    send_qoe_for_visualization(payload, qoe_moss)
        Send the computed QoE value for visualization

    """

    def __init__(self):
        """Kafka Exporter Class Constructor."""
        self.__producer = self.__init_producer()

    @staticmethod
    def __init_producer():
        """Initializes a KafkaProducer.

        Returns
        -------
        producer : KafkaProducer
            A KafkaProducer Object for sending messages

        """
        # Initialize a Kafka Producer
        # See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html
        producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, client_id=KAFKA_CLIENT_ID,
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                 api_version=KAFKA_API_VERSION, )
        logger.info('Initialized Kafka Producer')
        return producer

    def publish_message(self, topic, payload):
        """Publishes a message payload to a given Kafka topic.

        Parameters
        ----------
        topic : str
            The topic to publish the Kafka message
        payload : dict
            The message to publish as a dict

        """
        request = self.__producer.send(topic, payload)
        try:
            request.get(timeout=60)
        except KafkaError as ke:
            logger.error(ke)

    def set_vtranscoder_processing_unit(self, payload, processing_unit='gpu'):
        """Send the message for placement to a node to execution.

        Parameters
        ----------
        payload : dict
            A VTranscoder MANO Payload
        processing_unit : {'gpu', 'cpu'}
            The processing unit to use for the vTranscoder

        """
        payload.update(
            {
                'analysis': {
                    'action': True
                },
                'execution': {
                    'planning': 'set_vtranscoder_processing_unit',
                    'value': processing_unit
                }
            }
        )
        # Publish to Kafka
        self.publish_message(KAFKA_EXEC_TOPIC, payload)
        logger.info('Published to Execution service for placement of transcoder {} to {} node'
                    .format(payload['mano']['vnf']['index'], processing_unit.upper()))
        logger.debug(
            'Published to Execution service for placement of transcoder {}, (NS: {}, VNF: {}, VDU: {}) to GPU node'
            .format(payload['mano']['vnf']['index'], payload['mano']['ns']['id'],
                    payload['mano']['vnf']['id'], payload['mano']['vdu']['id']))

    def set_vtranscoder_profile(self, payload, qualities_to_produce):
        """Send the message for setting vtranscoder profiles to execution.

        Parameters
        ----------
        payload : dict
            A VTranscoder MANO Payload
        qualities_to_produce : list
            A list of integers, qualities to produce

        """
        payload.update(
            {
                'analysis': {
                    'action': True
                },
                'execution': {
                    'planning': 'set_vtranscoder_profile',
                    'value': qualities_to_produce
                }
            }
        )
        # Publish to Kafka
        self.publish_message(KAFKA_EXEC_TOPIC, payload)
        logger.info('Published to Execution service for transcoder {} to produce qualities {}'
                    .format(payload['mano']['vnf']['index'], qualities_to_produce))
        logger.debug(
            'Published to Execution service for transcoder {} (NS: {}, VNF: {}, VDU: {}) to produce qualities {}'
            .format(payload['mano']['vnf']['index'], payload['mano']['ns']['id'],
                    payload['mano']['vnf']['id'], payload['mano']['vdu']['id'], qualities_to_produce))

    def set_vtranscoder_spectator_profile(self, client_id, group_id, qualities):
        """Send the message for setting vtranscoder spectator profile to conf.

        Parameters
        ----------
        client_id : str
            The spectator's client id
        group_id : str
            The spectator's group id
        qualities : dict
            The qualities to be consumed from the vTranscoder

        """
        message_to_conf = {
            'clients': [
                {
                    'client_id': client_id,
                    'timestamp': time(),
                    'use_these_qualities': [
                        {
                            'transcoder_id': '1',
                            'quality_id': qualities[1],
                            'skip_frames': 1 if qualities[1] in JPEG_PROFILES else 0
                        },
                        {
                            'transcoder_id': '2',
                            'quality_id': qualities[2],
                            'skip_frames': 1 if qualities[2] in JPEG_PROFILES else 0
                        }
                    ]
                }
            ]
        }

        # Publish to Kafka
        self.publish_message(KAFKA_SPECTATOR_CONF_TOPIC, message_to_conf)
        logger.info('Published to Spectator Conf service for spectator [{}] in group [{}] to consume quality [{}] for '
                    'Player 1'.format(client_id, group_id, qualities[1]))
        logger.info('Published to Spectator Conf service for spectator [{}] in group [{}] to consume quality [{}] for '
                    'Player 2'.format(client_id, group_id, qualities[2]))

    def send_no_action_message(self, payload):
        """Sends a message notifying executor that there is no action.

        Parameters
        ----------
        payload : dict
            The received payload

        """
        payload.update(
            {
                'analysis': {
                    'action': False
                }
            }
        )
        # Publish to Kafka
        self.publish_message(KAFKA_EXEC_TOPIC, payload)
        logger.info('No action was suggested')

    def send_qoe_for_visualization(self, payload, qoe_mos):
        """Publish QoE for visualization purposes.

        Parameters
        ----------
        payload : dict
            The received payload
        qoe_mos : float
            The Mean Opinion Score (MOS) to publish

        """
        payload.pop('measurements', None)
        payload.update(
            {
                'metric': {
                    'name': 'mean_opinion_score',
                    'value': qoe_mos,
                    'unit': '',
                    'timestamp': payload['timestamp']
                }
            }
        )

        # Publish to Kafka
        self.publish_message(KAFKA_VTRANS_QOE_TOPIC, payload)
        logger.info('Published QoE to corresponding topic. MOS Value: [{}]'.format(qoe_mos))


def init_consumer_and_subscribe(topic=KAFKA_PREP_TOPIC, group_id_suffix='IMMERSIVE_MEDIA'):
    """Initializes a KafkaConsumer and subscribe to topics

    Parameters
    ----------
    topic : str
        The topic to subscribe to
    group_id_suffix : str
        The suffix for the group ID

    Returns
    -------
    consumer : KafkaConsumer
        A KafkaConsumer Object

    """
    # Initialize a Kafka Consumer and subscribe
    # See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER, client_id=KAFKA_CLIENT_ID, enable_auto_commit=True,
                             api_version=KAFKA_API_VERSION, group_id=KAFKA_GROUP_ID.format(group_id_suffix.upper()))
    consumer.subscribe(topics=[topic, ])
    logger.info('Initialized Kafka Consumer & subscribed to pre-processing topic')
    return consumer
