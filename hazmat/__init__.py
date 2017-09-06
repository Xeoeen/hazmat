#!/usr/bin/env python3
from .options import OptionsDispacher
from . import tmp_utils
from .output import *


def main():
    try:
        OptionsDispacher().run()
    except FileNotFoundError as e:
        printError("FileNotFoundError")
        print(e)
        print("\tBe aware of relative paths in generator and validator")
    except PermissionError as e:
        printError("PermissionError")
        print(e)
        print("\t Be aware that some files need executive permission")
    finally:
        tmp_utils.clear_up()


if __name__ == "__main__":
    main()
