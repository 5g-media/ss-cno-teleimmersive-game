# =================================
#           MODEL NAMES
# =================================
MDP = 'MDP'
MDP_CD = 'MDP-CD'
MDP_DT = 'MDP-DT'
Q_DT = 'Q-DT'
Q_LEARNING = 'Q-learning'

# =================================
#         MODEL SETTINGS
# =================================
MODEL = 'model'
PARAMETERS = 'parameters'
OPTIONAL_PARAMETERS = 'optional_parameters'
INITIAL_PARAMETERS = 'initial_parameters'
MAX_OPTIONAL_PARAMETERS = 'max_optional_parameters'
ACTIONS = 'actions'
DISCOUNT = 'discount'
INITIAL_Q_VALUES = 'initial_q_values'
LEARNING_RATE = 'learning_rate'
TRAINING_WINDOW = 'training_window'
REWARD_IMPORTANCE = 'reward_importance'
QUALITY_RATE = 'quality_rate'
SPLIT_ERROR = 'split_error'
MIN_MEASUREMENTS = 'min_measurements'

# =================================
#         NO OPERATION
# =================================
NO_OP = 'no_operation'

# =================================
#      VALUES FOR PARAMETERS
# =================================
VALUES = 'values'
LIMITS = 'limits'

# =================================
#       UPDATE ALGORITHMS
# =================================
UPDATE_ALGORITHM = 'update_algorithm'
NO_UPDATE = 'no_update'
SINGLE_UPDATE = 'single_update'
VALUE_ITERATION = 'value_iteration'
PRIORITIZED_SWEEPING = 'prioritized_sweeping'
UPDATE_ALGORITHMS = [NO_UPDATE, SINGLE_UPDATE, VALUE_ITERATION, PRIORITIZED_SWEEPING]

# =================================
#      SPLITTING ALGORITHMS
# =================================
MID_POINT = 'mid_point'
ANY_POINT = 'any_point'
MAX_POINT = 'max_point'
INFO_GAIN = 'info_gain'
SPLIT_CRITERIA = [MID_POINT, ANY_POINT, MAX_POINT, INFO_GAIN]

# =================================
#       STATISTICAL TESTS
# =================================
STUDENT_TTEST = 'student_ttest'
WELCH_TTEST = 'welch_ttest'
MANN_WHITNEY_UTEST = 'mann_whitney_utest'
KOLMOGOROV_SMIRNOV = 'kolmogorov_smirnov'
