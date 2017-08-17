from subprocess import Popen, PIPE, DEVNULL

c
lass GeneratorError(Exception):

    def __init__(self, message):
        super(GeneratorError, self).__init(message)


class Generator:

    def __init__(self, name, message, flags = []):
        self.name = name
        self.message = message
        self.flags = flags
        self.callList = [self.name]
        self.callList.extend(self.flags)

    def generate(self, outFile):

        try:
            proc = Popen(self.callList, stdin=PIPE, stdout = open(outFile, "w"), stderr = DEVNULL)
            proc.communicate(input = self.message.encode())
            proc.wait()

            if proc.returncode != 0:
                raise GeneratorError()
        except KeyboardInterrupt:
            raise KeyboardInterrupt
