import time
import os
from subprocess import DEVNULL, TimeoutExpired, call
from .enums import RunStatus
from .. import config
from ..output import *


class Solution(object):
    compileTimeout = 10

    def __init__(self, name, timeout = 1000):
        self.timeout = timeout
        baseName, extension = os.path.splitext(name)
        if extension not in config.providers:
            printError("Non valid provider in config")
            exit(110)

        self.sourceFile = name
        self.info = config.providers[extension]
        if self.info.need_compile:
            self.execFile = baseName + ".bin"
        else:
            self.execFile = name

        self.hasSource = os.path.isfile(self.sourceFile)
        self.hasExec = os.path.isfile(self.execFile)
        self.prefix = ""
        if not self.execFile.startswith("/"):
            self.prefix = "./"

        if not self.hasSource and not self.hasExec:
            print("non valid solution no execFile and sourceFile")
            exit(141)

    def internal_compile(self, flags):
        try:
            exitCode = call(self.info.query(self.sourceFile, self.execFile, flags).split(), timeout = self.compileTimeout)

        except TimeoutExpired:
            printWarning("Compile timeout")
            return False
        except KeyboardInterrupt:
            exit(105)

        if exitCode == 0:
            if flags is None:
                printInfo("Compiled {} with flags".format(self.sourceFile) + " ".join(self.info.default_flags))
            else:
                printInfo("Compiled {} with flags".format(self.sourceFile) + " ".join(flags))
            return True
        else:
            printWarning("Error in compiling")
            return False

    def compile(self, flags = None, force = False, auto = True):
        if self.info.need_compile is False:
            return True
        if self.hasSource:
            if force or not self.hasExec:
                return self.internal_compile(flags)
            else:
                if os.path.getmtime(self.sourceFile) > os.path.getmtime(self.execFile):
                    return self.internal_compile(flags)
                else:
                    if not auto:
                        printInfo("No need to compile")
                    return True
        else:
            printError("No source file {}".format(self.sourceFile))
            return False

    def run(self, inFile, outFile, outErr = DEVNULL):
        try:
            startTime = time.time()
            exitCode = call(self.prefix + self.execFile, stdin = open(inFile, "r"), stdout = open(outFile, "w"), stderr = outErr, timeout = self.timeout)
            endTime = time.time()
            durationTime = endTime - startTime
            durationTime = round(durationTime, 2)
        except TimeoutExpired:
            return RunStatus.TLE, 0

        return RunStatus(exitCode), durationTime
