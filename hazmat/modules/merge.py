import os
import subprocess
from ..models import Solution
from ..output import *


def merge(solution, output, command):
    callList = command.format(solution, output).split()
    try:
        exit_code = subprocess.call(callList)
    except KeyboardInterrupt:
        printInfo("Running test canceled due to KeyboardInterrupt")
        exit(105)

    if exit_code != 0:
        raise Exception("Preprcessor error")


def createSubParser(subParser):
    mergeParser = subParser.add_parser("merge", help = "Eliminate local dependencies")
    createParser(mergeParser)


def createParser(mergeParser):
    mergeParser.set_defaults(func = mergeHandler)
    mergeParser.add_argument(dest = "solution", help = "Solution of task")
    mergeParser.add_argument(dest = "output", help = "Output file")
    mergeParser.add_argument("--force", "-f", action="store_true", help = "Don't mind overwritting")


def mergeHandler(args):

    solution = Solution(args["solution"])
    out_file = args["output"]
    if not solution.info.has_merge:
        printError("Unnable to detect merge command in config")
        exit(111)

    if not solution.hasSource:
        printError("No valid sorce code given!")
        exit(141)

    if os.path.isfile(out_file) and not args["force"]:
        printError("File exist already.\n\t Add --force / -f to overwrite!")
        exit(142)

    try:
        merge(solution.sourceFile, out_file, solution.info.merge_command)
        printSuccess("Merged {} into {}".format(solution.sourceFile, out_file))
    except:
        printError("Merging failed")
