from subprocess import Popen, PIPE, DEVNULL


class Generator:

    def __init__(self, name, message, flags = []):
        self.name = name
        self.message = message
        self.flags = flags

    def generate(self, outFile):
        callList = [self.name]
        callList.extend(self.flags)
        try:
            proc = Popen(callList, stdin=PIPE, stdout = open(outFile, "w"), stderr = DEVNULL)
            proc.communicate(input = self.message.encode())
            proc.wait()

            if proc.returncode != 0:
                print("Generator crashed on message {}".format(self.message))
                raise Exception("GeneratorError")
        except KeyboardInterrupt:
            raise KeyboardInterrupt
