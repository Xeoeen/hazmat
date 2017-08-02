import os
from shutil import copy
from ..utils import normalize_dir
from .. import config
from ..output import *


def createSubParser(subParser):
    initParser = subParser.add_parser("init", help="Init solving task here")
    createParser(initParser)


def createParser(initParser):
    initParser.add_argument("--path", help = "Path to initialization", default = "./")
    initParser.add_argument("name", help = "Name of first file")
    initParser.add_argument("--type", help = "type of template used to init", default = "default")
    initParser.set_defaults(func=initHandler)


def initHandler(args):
    init_type = args["type"]
    directory = normalize_dir(args["path"])
    name, extension = os.path.splitext(args["name"])
    if extension not in config.providers:
        printError("Unsupported language {}".format(extension))
        print("\tMake sure you put it in config")
        exit(104)

    provider = config.providers[extension]

    if not provider.has_init:
        printError("No initialization data in config")
        print("\tMake sure you put it in config")
        exit(104)
    initData = provider.init_data

    if init_type not in initData:
        printError("No initialization of this type in config")
        print("\tMake sure you put it in config")
        exit(104)
    initData = initData[init_type]

    for folder_template in initData["dirs"]:
        folder = directory + folder_template.replace("{}", name)
        if not os.path.isdir(folder):
            os.makedirs(folder)

    for file_move in initData["files"]:
        src = file_move["src"]
        dest = directory + file_move["dest"].replace("{}", name)
        if os.path.isfile(dest):
            printWarning("File {} already exists SKIPPING".format(dest))
        else:
            copy(src, dest)
    print()
    printInfo("Initailized")
