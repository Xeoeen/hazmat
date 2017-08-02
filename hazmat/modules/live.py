import os
from shutil import copyfile
from ..utils import normalize_dir
from ..output import *
from ..models import Solution, Generator, Validator, ResultCounter
from ..models.enums import ExitCode
from ..progressbar import tqdm
from .. import tmp_utils


def createSubParser(subParser):
    liveParser = subParser.add_parser("live", help = "Live testing solution with validator and generator")
    createParser(liveParser)


def createParser(liveParser):
    solutionGroup = liveParser.add_argument_group("Solution options")
    solutionGroup.add_argument(dest = "solution", help = "Solution to check")
    solutionGroup.add_argument("--timeout", "-t", metavar = "sec", help = "Maximal runtime of program", default = 5, type = int, dest="timeout")

    outputGroup = liveParser.add_argument_group("Output generator options")
    outputGroup.add_argument(dest = "used", help = "Solution to generate right outputs")
    outputGroup.add_argument("--timeout-checker", "-tc", metavar = "sec", help = "Maximal runtime of checker", default = 10, type = int, dest ="timeoutchecker")

    validatorGroup = liveParser.add_argument_group("Validator options")
    validatorGroup.add_argument("--validator", help = "Path to executiv that validats")
    validatorGroup.add_argument("--validator-need-input", dest = "inputneed", action = "store_true", help= "Validator requires input file")

    liveParser.add_argument("--break", help="Break on first non-AC", action = "store_true")
    liveParser.add_argument("--number-of-runs", "-n", dest = "num", help = "Numbers of tests to run", default = 10, type = int)

    generatorGroup = liveParser.add_argument_group("Generator options")
    generatorGroup.add_argument("--generator", "-gen", metavar = "GEN", help = "Path to executive that generates tests", required = True)
    generatorGroup.add_argument("--message", "-m", help="This one goes to generator as stdin", default = "")

    printGroup = liveParser.add_argument_group("Printing options")
    printGroup.add_argument("--progressbar", help = "Show progressbar", action = "store_true")
    printGroup.add_argument("--summary", help="Show summary", default = 0, type = int)
    printGroup.add_argument("--print-level", dest= "print", type = int, default = 3)

    liveParser.add_argument('--save', help="Saves non-AC tests in given dir", default = "")

    liveParser.set_defaults(func = liveHandler)


def liveHandler(args):
    breakOnWA = args['break']
    solution = Solution(name = args["solution"], timeout = args["timeout"])
    outputGenerator = Solution(name = args["used"], timeout = args["timeoutchecker"])
    progressbar = args["progressbar"]
    printLevel = args["print"]
    showSummary = (args["summary"] > 0)

    if not solution.compile():
        exit(103)

    validator = Validator.createFromArgs(args)
    counter = ResultCounter("LIVE", store = showSummary)

    generator = Generator(name = args["generator"], message = args["message"])

    n = args["num"]
    test = tmp_utils.create()
    wzo = tmp_utils.create()
    unknow = tmp_utils.create()
    saveNonAC = False
    saveDest = ""
    if args["save"] != "":
        saveNonAC = True
        saveDest = normalize_dir(args['save'])
        if not os.path.isdir(saveDest):
            printError("Given non-AC save point does't exit")
            exit(101)

    if progressbar:
        testYield = tqdm(range(n))
        print_func = testYield.write
    else:
        testYield = range(n)
        print_func = print

    try:
        for _i in testYield:
            generator.generate(test)
            if progressbar:
                testYield.set_description("Number {}".format(_i))
            s1, d1 = solution.run(test, unknow)
            s2, d2 = outputGenerator.run(test, wzo)
            if s2 != ExitCode.OK:
                printError("Checker fucked up with {} on {}".format(s2, _i))
                continue
            if s1 != ExitCode.OK:
                if saveNonAC:
                    copyfile(test, saveDest + str(_i) + ".in")
                if printLevel > 0:
                    print_func(ounter.addError(str(_i) + ".in", d1, s1))
                continue

            result = validator.validate(test, wzo, unknow)
            if result and printLevel > 2:
                print_func(counter.addResult(str(_i) + ".in", d1, result))
            elif not result and printLevel > 1:
                print_func(counter.addResult(str(_i) + ".in", d1, result))
            else:
                counter.addResult(str(_i) + ".in", d1, result)
            if not result:
                if saveNonAC:
                    copyfile(test, saveDest + str(_i) + ".in")
                if breakOnWA:
                    break
        print()
    except KeyboardInterrupt:
        printInfo("Running test canceled due to KeyboardInterrupt")
    finally:
        counter.status()
        if showSummary:
            counter.summary(args["summary"])
