"""Django settings for CNO project."""

import os

# ==================================
#           PROJECT ROOT
# ==================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))

# =================================
#             DEBUG
# =================================
DEBUG = os.getenv('CNO_IM_DEBUG')

# =================================
#           SECRET KEY
# =================================
SECRET_KEY = 'uw-@(dw=oq*p#qcs^u!hs9-w(_hiwd0=^$+@n9f!zb6wh8tm8-'

# ==================================
#      INSTALLED APPLICATIONS
# ==================================
INSTALLED_APPS = [
    'markovdp',
    'runner',
    'simulation'
]

# ==================================
#       RDBMS CONFIGURATION
# ==================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('CNO_IM_DB_NAME'),
        'USER': os.getenv('CNO_IM_DB_USER'),
        'PASSWORD': os.getenv('CNO_IM_DB_PASSWORD'),
        'HOST': os.getenv('CNO_IM_DB_HOST'),
        'PORT': os.getenv('CNO_IM_DB_PORT'),
    }
}

# ==================================
#         TIMEZONE SETTINGS
# ==================================
TIME_ZONE = 'UTC'
USE_TZ = True

# ==================================
#       MULTILINGUAL SETTINGS
# ==================================
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

# =================================
#        LOGGING SETTINGS
# =================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': "[%(asctime)s] - [%(name)s:%(lineno)s] - [%(levelname)s] %(message)s",
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
        },
        'markovdp': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/markovdp.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'simulation': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/simulation.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'runner': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/runner.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'spectators': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/spectators.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'metric_collector': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/metric_collector.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
        'experience_collector': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}/logs/experience_collector.log".format(PROJECT_ROOT),
            'mode': 'w',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 2024 * 2024,
            'backupCount': 5,
        },
    },
    'loggers': {
        'markovdp': {
            'level': 'DEBUG',
            'handlers': ['markovdp']
        },
        'simulation': {
            'level': 'DEBUG',
            'handlers': ['simulation']
        },
        'runner': {
            'level': 'DEBUG',
            'handlers': ['runner']
        },
        'spectators': {
            'level': 'DEBUG',
            'handlers': ['spectators']
        },
        'metric_collector': {
            'level': 'DEBUG',
            'handlers': ['metric_collector']
        },
        'experience_collector': {
            'level': 'DEBUG',
            'handlers': ['experience_collector']
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console']
    },
}

# =================================
#          KAFKA SETTINGS
# =================================
KAFKA_SERVER = os.getenv('CNO_IM_KAFKA_SERVER')
