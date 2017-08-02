#!/usr/bin/env python3
from .options import OptionsDispacher
from . import tmp_utils


def main():
    try:
        OptionsDispacher().run()
    finally:
        tmp_utils.clear_up()


if __name__ == "__main__":
    main()
