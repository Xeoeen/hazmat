import os
from subprocess import call, TimeoutExpired, DEVNULL


class Validator:
    timeOut = 5

    def createFromArgs(args):
        if args["validator"]:
            return Validator(needInput = args["inputneed"], checker = args["validator"], flags =[])
        else:
            return Validator()

    def __init__(self, checker = "diff", flags = ["-wq"], needInput = False):

        self.checker = checker
        self.flags = flags
        self.needInput = needInput

    def validate(self, inFile, outFileTrue, outFileToVal):
        inFile = os.path.realpath(inFile)
        outFileTrue = os.path.realpath(outFileTrue)
        outFileToVal = os.path.realpath(outFileToVal)
        callList = [self.checker]
        if self.needInput:
            callList.append(inFile)
        callList.append(outFileTrue)
        callList.append(outFileToVal)
        callList.extend(self.flags)

        try:
            exitCode = call(callList, timeout = Validator.timeOut, stdout = DEVNULL, stderr = DEVNULL)
        except TimeoutExpired:
            print("Validator {} got timeout on test {}!".format(self.checker, inFile))
            return False

        if exitCode == 0:
            return True
        else:
            return False
