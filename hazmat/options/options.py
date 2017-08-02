import argparse
import sys
from .. import modules


class OptionsDispacher:

    def __init__(self):

        self.parser = argparse.ArgumentParser(prog="HazMAT", description="Run, Test and Solve Tasks")
        self.parser.add_argument('--version', action='version', version='%(prog)s build 0.1')
        modules.useAllModules(self.parser)

    def run(self):
        arg = self.parser.parse_args()
        if arg.__contains__("func"):
            arg.func(vars(arg))
        if len(sys.argv) < 2:
            self.parser.print_help()
