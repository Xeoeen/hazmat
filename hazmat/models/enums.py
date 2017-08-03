from enum import Enum


class RunStatus(Enum):
    OK = 0
    TLE = -999
    SIGINT = -2
    SIGABRT = -6
    SIGSEGV = -11
    SIGFLP = -8
    SIGTERM = -15
    UNKNOWN = 1


def _RunStatus_parser(cls, value):
    if not isinstance(value, int):
        return super(RunStatus, cls).__new__(cls, value)
    else:
        return {0: RunStatus.OK,
                -999: RunStatus.TLE,
                -2: RunStatus.SIGINT,
                -6: RunStatus.SIGABRT,
                -11: RunStatus.SIGSEGV,
                -8: RunStatus.SIGFLP,
                -15: RunStatus.SIGTERM}.get(value, RunStatus.UNKNOWN)


setattr(RunStatus, '__new__', _RunStatus_parser)
