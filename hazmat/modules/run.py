import os
from ..models import Solution, Validator
from ..models.enums import ExitCode
from ..utils import printFile
from ..output import *
from .. import tmp_utils


def createSubParser(subParser):
    runParser = subParser.add_parser("run", help="Run test options")
    createParser(runParser)


def createParser(runParser):
    solutionGroup = runParser.add_argument_group("Solution options")
    solutionGroup.add_argument(dest = "solution", help = "Solution to check")
    solutionGroup.add_argument("--timeout", "-t", metavar = "sec", help = "Maximal runtime of program", default = 5, type = int, dest="timeout")

    runParser.add_argument(dest = "inFile", help = "Path to test")
    runParser.add_argument("--out", dest = "outFile", default = "", help = "Test output file")
    runParser.add_argument("--show-input", "-is", dest = "showinput", action="store_true", help="Print input file")
    runParser.add_argument("--show-output", "-os", dest = "showoutput", action="store_true", help="Print outputs")

    validatorGroup = runParser.add_argument_group("Validator options")
    validatorGroup.add_argument("--validator", help = "Path to executiv that validats")
    validatorGroup.add_argument("--validator-need-input", dest = "inputneed", action = "store_true", help= "Validator requires input file")

    runParser.set_defaults(func = runHandler)


def runHandler(args):
    validator = Validator.createFromArgs(args)
    tmp = tmp_utils.create()
    solution = Solution(name = args["solution"], timeout = args["timeout"])
    if not solution.compile() and not solution.hasExec:
        printError("Cannot create binary and no binary avaible")
        exit(103)

    inFile = args["inFile"]
    if args["outFile"] == "":
        outFile = os.path.splitext(args["inFile"])[0] + ".out"
    else:
        outFile = args["outFile"]
        if not os.path.isfile(outFile):
            printWarning("Output file does not exist")
    show_input = args["showinput"]
    show_output = args["showoutput"]

    if not os.path.isfile(inFile):
        printError("This test doesn't exist ({})".format(inFile))
        exit(102)

    try:
        exitCode, duration = solution.run(inFile, tmp)
    except KeyboardInterrupt:
        printInfo("Running test canceled due to KeyboardInterrupt")
        exit(105)

    if exitCode != ExitCode.OK:
        printError(exitCode.name, end = "")
        printTime(duration)
        if show_input:
            printInfo("Input")
            printFile(inFile)
        exit(1)

    if os.path.isfile(outFile):

        result = validator.validate(inFile, tmp, outFile)
        if result:
            printAC(inFile, duration)
        else:
            printWA(inFile, duration)

        if show_input:
            printInfo("Input")
            printFile(inFile)

        if show_output:
            if result:
                printInfo("Output common")
                printFile(tmp)
            else:
                printInfo("Output {}".format(solution.execFile))
                printFile(tmp)
                printInfo("Output {}".format(outFile))
                printFile(outFile)
    else:
        printInfo(inFile, end="")
        printTime(duration)
        if show_output:
            printFile(tmp)
