import json
import logging.config
import random
import time
from datetime import datetime

import math
from django.core.management import BaseCommand
from kafka import KafkaProducer
from kafka.errors import KafkaError

from cno.settings.base import LOGGING
from simulation.config import KAFKA_API_VERSION, KAFKA_SERVER
from simulation.constants import mano

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def no_operation_measurements(measurements):
    new_measurements = {
        'cpu_util': random.uniform(measurements['cpu_util'] / 100 - 0.01, measurements['cpu_util'] / 100) * 100,
        'memory.usage': random.uniform(measurements['memory.usage'] / 100 - 0.01, measurements['memory.usage'] / 100) * 100,
        'disk.usage': random.uniform(measurements['disk.usage'] / 100 - 0.01, measurements['disk.usage'] / 100) * 100
    }
    return new_measurements


def get_measurements(cpu, memory, disk):
    measurements = {
        'cpu_util': random.uniform(*cpu) * 100,
        'memory.usage': random.uniform(*memory) * 100,
        'disk.usage': random.uniform(*disk) * 100
    }
    return measurements


def get_mix_and_match_measurements():
    mix_and_match_measurements = {
        'cpu_util': random.choice([random.uniform(0, 0.5), random.uniform(0.5, 0.75), random.uniform(0.75, 1)]) * 100,
        'memory.usage': random.choice([random.uniform(0, 0.5), random.uniform(0.5, 0.75), random.uniform(0.75, 1)]) * 100,
        'disk.usage': random.choice([random.uniform(0, 0.5), random.uniform(0.5, 0.75), random.uniform(0.75, 1)]) * 100
    }
    return mix_and_match_measurements


def compute_vq_itu():
    """Computes Video Quality according to the model suggested by the ITU."""

    # Coefficients
    coef = [0, 5.517, 0.0129, 3.459, 178.53, 1.02, 1.15, 0.000355, 0.114, 513.77, 0.736, -6.451, 13.684]

    # Video frame rate
    f_r_v = 11
    # Video bit rate in kbps
    b_r_v = (70000 * f_r_v * 8) / 1000
    # Packet loss rate
    p_pl_v = random.uniform(0, 2)

    # Degree of video quality robustness due to frame rate
    d_fr_v = coef[6] + coef[7] * b_r_v
    # Degree of video quality robustness due to packet loss
    d_ppl_v = coef[10] + coef[11] * math.exp(-f_r_v / coef[8]) + coef[12] * math.exp(-b_r_v / coef[9])

    # Maximum video quality a each Bit Rate
    o_fr = coef[1] + coef[2] * b_r_v
    i_ofr = coef[3] - (coef[3] / (1 + (b_r_v / coef[4]) ** 5))
    # Basic video quality affected by the coding distortion
    i_coding = i_ofr * math.exp(-((math.log(f_r_v) - math.log(o_fr)) ** 2) / (2 * d_fr_v ** 2))
    # Video quality
    v_q = 1 + i_coding * math.exp(-p_pl_v / d_ppl_v)

    # Format QoE value accordingly
    qoe_value = {
        "unit": "",
        "timestamp": datetime.now().isoformat(),
        "type": 'gauge',
        "name": 'mean_opinion_score',
        "value": v_q
    }

    return qoe_value


def produce(producer, msg, key):
    request = producer.send('ns.instances.prep', key=key.encode('utf-8'), value=msg)
    try:
        request.get(timeout=60)
    except KafkaError as ke:
        logger.error(ke)


def publish_metrics_for_cno():
    # Kafka Producer Set Up
    # https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, api_version=KAFKA_API_VERSION,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    # Wait for the training of the algorithm
    time.sleep(300)

    while True:
        # Simulate for high measurements
        old_measurements = get_measurements((0.5, 1), (0.5, 1), (0.5, 1))
        logger.info('Initial measurements: {}'.format(old_measurements))
        old_msg = {'measurements': old_measurements, 'mano': mano}
        produce(producer, old_msg, 'simulation')
        time.sleep(3)

        old_qoe = {'metric': compute_vq_itu(), 'mano': mano}
        logger.info('Initial QoE: {}'.format(old_qoe['metric']['value']))
        produce(producer, old_qoe, 'qoe')
        time.sleep(5)

        # New measurements and QoE for reward
        new_measurements = get_measurements((0, 0.5), (0, 0.5), (0, 0.5))
        logger.info('Measurements after action: {}'.format(new_measurements))
        new_msg = {'measurements': new_measurements, 'mano': mano}
        produce(producer, new_msg, 'simulation')
        time.sleep(3)

        new_qoe = {'metric': compute_vq_itu(), 'mano': mano}
        logger.info('After action QoE: {}'.format(new_qoe['metric']['value']))
        produce(producer, new_qoe, 'qoe')
        time.sleep(60)

        # Simulate for low measurements
        old_measurements = get_measurements((0.1, 0.5), (0.1, 0.5), (0.1, 0.5))
        logger.info('Initial measurements: {}'.format(old_measurements))
        old_msg = {'measurements': old_measurements, 'mano': mano}
        produce(producer, old_msg, 'simulation')
        time.sleep(3)

        old_qoe = {'metric': compute_vq_itu(), 'mano': mano}
        logger.info('Initial QoE: {}'.format(old_qoe['metric']['value']))
        produce(producer, old_qoe, 'qoe')
        time.sleep(5)

        # New measurements and QoE for reward
        new_measurements = no_operation_measurements(old_measurements)
        logger.info('Measurements after action: {}'.format(new_measurements))
        new_msg = {'measurements': new_measurements, 'mano': mano}
        produce(producer, new_msg, 'simulation')
        time.sleep(3)

        new_qoe = {'metric': compute_vq_itu(), 'mano': mano}
        logger.info('After action QoE: {}'.format(new_qoe['metric']['value']))
        produce(producer, new_qoe, 'qoe')
        time.sleep(60)


class Command(BaseCommand):
    def handle(self, *args, **options):
        publish_metrics_for_cno()
