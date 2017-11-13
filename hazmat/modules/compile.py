from ..models import Solution
from ..output import *


def createSubParser(subParser):
    compileParser = subParser.add_parser("build", help="Compile solution")
    createParser(compileParser)


def createParser(compileParser):
    compileParser.set_defaults(func = compileHandler)
    compileParser.add_argument(dest = "solution", help = "Solution of task")
    compileParser.add_argument('--force', '-f', action='store_true')
    compileParser.add_argument('--output', help = "Compiled version path", default = "")
    compileParser.add_argument('--flags', dest = "flags", default = None, help = "Optional flags to compiler")


def compileHandler(args):
    solution = Solution(name = args["solution"], timeout = 10)
    if not solution.info.need_compile:
        printInfo("No need to compile this file!")

    flags = args["flags"]
    if flags is not None:
        flags = flags.split(" ")
    solution.compile(flags = flags, force = args["force"], auto = False)
