from argparse import REMAINDER
from ..models import Solution
from ..output import *


def createSubParser(subParser):
    compileParser = subParser.add_parser("compile", help="Compile options")
    createParser(compileParser)


def createParser(compileParser):
    compileParser.set_defaults(func = compileHandler)
    compileParser.add_argument(dest = "solution", help = "Path to solution")
    compileParser.add_argument('--force', '-f', action='store_true')
    compileParser.add_argument('--output', help = "Path of output file", default = "")
    compileParser.add_argument('--flags', dest = "flags", nargs = REMAINDER, default =[])


def compileHandler(args):
    solution = Solution(name = args["solution"], timeout = 10)
    if not solution.info.need_compile:
        printInfo("No need to compile this file!")

    solution.compile(flags = args["flags"], force = args["force"], auto = False)
