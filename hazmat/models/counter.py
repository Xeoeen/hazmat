
from .enums import ExitCode
from ..output import *


class ResultCounter(object):
    class Event(object):
        def __init__(self, exitCode, testName, duration, success):
            self.exitCode = exitCode
            self.testName = testName
            self.duration = duration
            self.success = success

    def __init__(self, baseDir, store = False):
        self.baseDir = baseDir
        self.store = store
        self.events = []

        self.errorCounter = dict()
        self.acCount = 0
        self.waCount = 0

    def addError(self, testName, duration, exitCode):
        if exitCode in self.errorCounter:
            self.errorCounter[exitCode] += 1
        else:
            self.errorCounter[exitCode] = 1

        if self.store:
            self.events.append(ResultCounter.Event(exitCode, testName, duration, False))

        if exitCode == ExitCode.TLE:
            return strTLE(testName)
        else:
            return strExc(exitCode, testName)

    def addResult(self, testName, duration, result):
        if result:
            self.acCount += 1
        else:
            self.waCount += 1
        if self.store:
            self.events.append(ResultCounter.Event(ExitCode.OK, testName, duration, result))

        if result:
            return strAC(testName, duration)
        else:
            return strWA(testName, duration)

    def __iadd__(self, other):
        if not isinstance(other, ResultCounter):
            raise Exception("Cannot add {} to ResultCounter".format(type(other)))

        for key, value in other.errorCounter.items():
            if key in self.errorCounter:
                self.errorCounter[key] += value
            else:
                self.errorCounter[key] = value

        self.acCount += other.acCount
        self.waCount += other.waCount
        self.events.extend(other.events)

        return self

    def status(self):
        printSuccess("AC {}".format(self.acCount), end = "")
        printError("WA {}".format(self.waCount), end = "")
        printArrow("")

        for key, value in self.errorCounter.items():
            printError(key.name, end = "")
            printArrow(value)

    def summary(self, level = 3):
        printInfo("Summary of run")
        if self.acCount > 0 and level > 2:
            printInfo("AC")
            for event in self.events:
                if event.exitCode == ExitCode.OK and event.success:
                    printAC(event.testName, event.duration)
        if self.waCount > 0 and level > 1:
            printInfo("WA")
            for event in self.events:
                if event.exitCode == ExitCode.OK and not event.success:
                    printWA(event.testName, event.duration)
        if level > 0:
            if ExitCode.TLE in self.errorCounter:
                printInfo("TLE")
                for event in self.events:
                    if event.exitCode == ExitCode.TLE:
                        printTLE(event.testName)
            if len(self.errorCounter) - int(ExitCode.TLE in self.errorCounter) > 0:
                printInfo("Fuckups")
                for event in self.events:
                    if event.exitCode != ExitCode.OK and event.exitCode != ExitCode.TLE:
                        printError(event.exitCode.name, end = "")
                        printArrow(event.testName)
