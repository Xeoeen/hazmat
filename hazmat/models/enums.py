from enum import Enum


class ExitCode(Enum):
    OK = 0
    TLE = 1
    SIGINT = -2
    SIGABRT = -6
    SIGSEGV = -11
    SIGFLP = -8
    SIGTERM = -15
