from django.conf import settings

# =================================
#          KAFKA SETTINGS
# =================================
KAFKA_SERVER = settings.KAFKA_SERVER
KAFKA_CLIENT_ID = 'cognitive-network-optimizer'
KAFKA_GROUP_ID = 'CNO_{}'
KAFKA_API_VERSION = (1, 1, 0)
KAFKA_PREP_TOPIC = 'ns.instances.prep'
KAFKA_SPECTATOR_METRICS_TOPIC = 'spectators.vtranscoder3d.metrics'
KAFKA_SPECTATOR_CONF_TOPIC = 'spectators.vtranscoder3d.conf'
KAFKA_TRANS_TOPIC = 'ns.instances.trans'
KAFKA_VTRANS_QOE_TOPIC = 'app.vtranscoder3d_spectators.qoe'
KAFKA_EXEC_TOPIC = 'ns.instances.exec'

# =================================
#        METRICS WHITELIST
# =================================
METRICS_WHITELIST = [
    'bitrate_aggr',
    'bitrate_on',
    'framerate_aggr',
    'framerate_on',
    'latency_aggr',
    'working_fps',
    'output_data_bytes',
    'theoretic_load_percentage'
]
