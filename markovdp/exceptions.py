class ParameterError(Exception):
    """Error class for unsupported or missing parameters."""

    def __init__(self, message, logger=None):

        super(ParameterError, self).__init__(message)

        if logger is not None:
            logger.error(message)


class StateNotSetError(Exception):
    """Raised when the model is used before setting the initial state."""

    def __init__(self, logger=None):

        super(StateNotSetError, self).__init__("State has not been set")

        if logger is not None:
            logger.error("State has not been set")


class InternalError(Exception):
    """Raised for errors that are caused by internal bugs. These will never happen."""

    def __init__(self, message, logger=None):

        super(InternalError, self).__init__(message)

        if logger is not None:
            logger.error(message)


class ConfigurationError(Exception):
    """Error class for errors in the configuration file."""

    def __init__(self, message, logger=None):

        super(ConfigurationError, self).__init__(message)

        if logger is not None:
            logger.error(message)
