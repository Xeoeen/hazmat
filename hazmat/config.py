import json
import os

CONFIG_DIR = os.path.expanduser("~") + "/.config/hazmat/"
CONFIG_FILE = CONFIG_DIR + "hazmat.json"

with open(CONFIG_FILE) as config_file:
    global config
    config = json.load(config_file)


class Logistics(object):

    def __init__(self, name, extension):
        self.name = name
        self.extension = extension
        self.need_compile = False
        self.has_init = False
        self.has_merge = False

    def compile_info(self, compiler, formater, default_flags = []):
        self.need_compile = True
        self.compiler = compiler
        self.default_flags = default_flags
        self.formater = formater

    def init_info(self, data):
        self.has_init = True
        self.init_data = data

    def merge_info(self, command):
        self.merge_command = command
        self.has_merge = True

    def query(self, inFiles, outFile, flags = None):
        if not isinstance(inFiles, str):
            filesString = " ".join(inFiles)
        else:
            filesString = inFiles

        if not isinstance(flags, list):
            flags = self.default_flags

        flagsString = " ".join(flags)
        return self.formater.format(self.compiler, flagsString, filesString, outFile)

    def __str__(self):
        ret = self.name + '\t' + self.extension + '\n'
        if self.need_compile:
            ret += '\t' + self.compiler + '\t' + str(self.default_flags)
        return ret


providers = dict()

for el in config['languages']:
    log = Logistics(el['name'], el['extension'])
    if 'compile' in el:
        com = el['compile']
        log.compile_info(com['compiler'], com['format'], com['default-flags'])
    if 'init' in el:
        log.init_info(el['init'])
    if 'merge' in el:
        log.merge_info(el['merge'])

    providers[el['extension']] = log
