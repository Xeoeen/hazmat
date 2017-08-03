from ..models import Solution, Validator
from ..utils import normalize_dir, subtree_dirs, get_parrarel_tests
from ..models.enums import RunStatus
from ..models.counter import ResultCounter
from .. import tmp_utils
from ..progressbar import tqdm
from ..output import *


def createSubParser(subParser):
    testParser = subParser.add_parser("test", help="Test your solution on tests", aliases = ['check'])
    createParser(testParser)


def createParser(testParser):
    solutionGroup = testParser.add_argument_group("Solution options")
    solutionGroup.add_argument(dest = "solution", help = "Solution of task")
    solutionGroup.add_argument("--timeout", metavar = "sec", type = float, help = "Maximum runtime of solution")

    testParser.add_argument("--in-directory", "-in", help = "Directory of tests' inputs", default= "Tests/", dest = "inTestDir")
    testParser.add_argument("--out-directory", "-out", help="Directory of tests' outputs", default="", dest = "outTestDir")

    validatorGroup = testParser.add_argument_group("Validation options")
    validatorGroup.add_argument("--validator", help = "Validation executive")
    validatorGroup.add_argument("--validator-need-input", dest = "inputneed", action = "store_true", help= "Validator requires input file")

    printGroup = testParser.add_argument_group("Printing options")
    printGroup.add_argument("--progressbar", help = "Show progressbar", action = "store_true")
    printGroup.add_argument("--summary", help="Show summary", default = 0, type = int)
    printGroup.add_argument("--print-level", dest= "print", type = int, default = 3)

    testParser.add_argument("--walk", action = "store_true", help = "Walk symetric reqursive through directory")
    testParser.add_argument("--break", action = "store_true", help = "Break on first error")
    testParser.set_defaults(func = testHandler)


def runTests(solution, validator, listTests, counter, breakOnError = False, progressbar = False, printLevel = 0):

    tmp = tmp_utils.create()
    if progressbar:
        gen = tqdm(listTests)
        print_func = gen.write
    else:
        gen = listTests
        print_func = print

    for inFile, outFile in gen:
        if progressbar:
            gen.set_description(inFile)
        status, duration = solution.run(inFile, tmp)
        if status == RunStatus.OK:
            res = validator.validate(inFile, outFile, tmp)
            counter.addResult(inFile, duration, res)
            if res and printLevel > 2:
                print_func(strAC(inFile, duration))
            elif not res and printLevel > 1:
                print_func(strWA(inFile, duration))

            if breakOnError:
                return False
        else:
            counter.addError(inFile, duration, status)
            if printLevel > 0:
                print_func(strTLE(inFile) if status == RunStatus.TLE else strExc(status, inFile))
            if breakOnError:
                return False
    return True


def testHandler(args):
    if args["outTestDir"] == "":
        args["outTestDir"] = args["inTestDir"]

    inTestDir = normalize_dir(args["inTestDir"])
    outTestDir = normalize_dir(args["outTestDir"])
    progressbar = args["progressbar"]

    solution = Solution(name = args["solution"], timeout = args["timeout"])
    validator = Validator.createFromArgs(args)

    if not solution.compile():
        printError("Could not compile solution")
        exit(121)

    listDir = subtree_dirs(inTestDir) if args['walk'] else [inTestDir]

    showSummary = (args["summary"] > 0)
    counter = ResultCounter(args["inTestDir"], store = showSummary)
    try:
        for curInDir in listDir:
            printInfo("Running folder " + curInDir)
            curOutDir = outTestDir + curInDir[len(inTestDir):]
            listTests = sorted(get_parrarel_tests(curInDir, curOutDir))
            if len(listTests) > 0:
                con = runTests(solution, validator, listTests, counter, breakOnError = args["break"], progressbar = progressbar, printLevel = args["print"])
                if not con:
                    printError("Breaking on RE or WA")
                    break
            else:
                printError("No valid tests in {}".format(curInDir))
                printInfo("Some tests might not have output or input")
                print()
        print()
    except KeyboardInterrupt:
        print()
        printInfo("Running tests canceled due to KeyboardInterrupt")
    finally:
        counter.status()
        if showSummary:
            counter.summary(args["summary"])
