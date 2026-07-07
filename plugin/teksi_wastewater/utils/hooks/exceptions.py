# Base exception for all TEKSI Hook errors
class TeksiHookException(Exception):
    """Base class for all exceptions raised by TWW.

    Version Added:
        1.0.0
    """

class TeksiHookError(TeksiHookException):
    """Exception raised for errors by an invalid hook.

    Version Added:
        1.0.0
    """
