import json
import logging

from django.core.management import BaseCommand

from runner.config import KAFKA_TRANS_TOPIC, METRICS_WHITELIST, KAFKA_PREP_TOPIC
from runner.constants import VTRANSCODER_3D, VTRANSCODER_3D_SPECTATORS
from runner.utils.kafka import KafkaExporter, init_consumer_and_subscribe

logger = logging.getLogger('metric_collector')


def metric_collector():
    """Connects on Kafka Bus and collects metrics for active vTranscoders and spectators. """

    # Initialize consumer and exporter
    consumer = init_consumer_and_subscribe(topic=KAFKA_TRANS_TOPIC,
                                           group_id_suffix='IMMERSIVE_MEDIA_PREPROCESSING')
    kafka_exporter = KafkaExporter()

    # Metrics Dict
    metrics_per_resource_id = {}

    for msg in consumer:
        try:
            payload = json.loads(msg.value.decode('utf-8', 'ignore'))
        except json.JSONDecodeError as jde:
            logger.error(jde)
            continue

        # Check if VIM tag is the required
        vim_tag = payload['mano']['vim']['tag']
        if vim_tag not in [VTRANSCODER_3D, VTRANSCODER_3D_SPECTATORS]:
            logger.debug('VIM tag was {}. Ignoring ...'.format(vim_tag))
            continue

        # Check if metric is in whitelist
        if payload['metric']['name'] not in METRICS_WHITELIST:
            logger.debug('Metric was {}. Ignoring ...'.format(payload['metric']['name']))
            continue

        # Get metric details
        mano_vdu_id = payload['mano']['vdu']['id']
        metric = payload['metric']
        metric_name = metric['name']
        metric_value = metric['value']
        metric_timestamp = metric['timestamp']

        # If the metrics refer to spectators
        if vim_tag == VTRANSCODER_3D_SPECTATORS:
            client_id = payload['spectator']['client_id']
            group_id = payload['spectator']['group_id']
            resource_id = (client_id, group_id, mano_vdu_id)
            logger.debug('Received metric [{}] for resource [{}].'.format(metric_name, resource_id))
            if resource_id in metrics_per_resource_id.keys():
                if metrics_per_resource_id[resource_id][metric_name] is None:
                    metrics_per_resource_id[resource_id][metric_name] = metric_value
                if None not in metrics_per_resource_id[resource_id].values():
                    payload.pop('metric')
                    payload['timestamp'] = metric_timestamp
                    payload['measurements'] = metrics_per_resource_id[resource_id]
                    logger.info('Collected measurements for resource [{}]: `{}`'
                                .format(resource_id, payload['measurements']))
                    kafka_exporter.publish_message(KAFKA_PREP_TOPIC, payload)
                    metrics_per_resource_id[resource_id] = dict.fromkeys(metrics_per_resource_id[resource_id], None)
            else:
                logger.debug('Resource [] has now been recorded.'.format(resource_id))
                metrics_per_resource_id[resource_id] = {
                    'bitrate_aggr': None,
                    'bitrate_on': None,
                    'framerate_aggr': None,
                    'framerate_on': None,
                    'latency_aggr': None,
                    'working_fps': None,
                    'output_data_bytes': None,
                    'theoretic_load_percentage': None
                }
                metrics_per_resource_id[resource_id][metric_name] = metric_value

        # If the metrics refer to vTranscoders
        if vim_tag == VTRANSCODER_3D:
            for resource in metrics_per_resource_id.keys():
                if resource[-1] == mano_vdu_id:
                    logger.debug('Set metric [{}] for resource [{}].'.format(metric_name, resource))
                    metrics_per_resource_id[resource][metric_name] = metric_value


class Command(BaseCommand):
    def handle(self, *args, **options):
        metric_collector()
