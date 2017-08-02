from ..utils import normalize_dir
from .. output import *
from ..models import Generator, Solution
import os


def createSubParser(subParser):
    generateParser = subParser.add_parser("generate", help = "Live testing solution with validator and generator")
    createParser(generateParser)


def createParser(generateParser):
    solutionGroup = generateParser.add_argument_group("Solution options")
    solutionGroup.add_argument(dest = "solution", help = "Solution to generate output")
    solutionGroup.add_argument("--timeout", metavar = "sec", type = int, default = 5, help = "Maximum execusion time of solution")

    generatorGroup = generateParser.add_argument_group("Generator options")
    generatorGroup.add_argument("--generator", help = "Path to executive file thath generates tests", required = True)
    generatorGroup.add_argument("--message", "-m", dest = "generator_message", default = "", help = "This one goes to generator as stdin",)

    testsGroup = generateParser.add_argument_group("Tests options")
    testsGroup.add_argument("--prefix", help = "Constant prefix of tests names", required = True)
    testsGroup.add_argument("--zero-fill", "-zfill", type = int, help = "Leftpad of tests names")
    testsGroup.add_argument("--range", type = int, required = True, nargs = 2)

    outputPlaceGroup = generateParser.add_mutually_exclusive_group()
    outputPlaceGroup.add_argument("--dir", help = "Directory to place inputs and outputs", default = "Tests/")
    outputPlaceGroup.add_argument("--in-and-out", help = "Seperate directories for inputs and outputs", nargs = 2)
    generateParser.set_defaults(func = generateHandler)


def generateHandler(args):
    input_dir = args["dir"]
    output_dir = input_dir
    print(args)
    if args["in_and_out"] is not None:
        input_dir, output_dir = args["in_and_out"]

    input_dir = normalize_dir(input_dir)
    output_dir = normalize_dir(output_dir)
    prefix = args["prefix"]

    startPoint, endPoint = args["range"]
    if not startPoint < endPoint:
        printError("Given range is not valid")
        exit(1)

    if args["zero_fill"] is None:
        zero_fill = len(str(endPoint))
    else:
        zero_fill = args["zero_fill"]
    solution = Solution(name = args["solution"], timeout = args["timeout"])
    generator = Generator(name = args["generator"], message = args["generator_message"])

    try:
        for test_id in range(startPoint, endPoint):
            test_name = prefix + str(test_id).zfill(zero_fill)
            input_file = input_dir + test_name + ".in"
            output_file = output_dir + test_name + ".out"
            if not os.path.isfile(input_file) and not os.path.isfile(output_file):
                generator.generate(input_file)
                exit_code, duration = solution.run(input_file, output_file)
                if exit_code.value != 0:
                    raise Exception("Wrong return code {}".format(exit_code.name))
                else:
                    printAC(test_name, duration)
            else:
                printInfo("Skipping {} due to filenames coverage".format(test_name))
    except KeyboardInterrupt:
        printInfo("Running test canceled due to KeyboardInterrupt")
