ColorSuccess = "1;37;42"
ColorWarning = "0;37;43"
ColorError = "1;37;41"
ColorInfo = "1;37;44"
ColorTime = "1;31;47"


def printSuccess(message, end = "\n"):
    print(strSuccess(message), end = end)


def strSuccess(message):
    return "\x1b[{0}m {1} \x1b[0m".format(ColorSuccess, message)


def printWarning(message, end = "\n"):
    print(strWarning(message), end = end)


def strWarning(message):
    return "\x1b[{0}m {1} \x1b[0m".format(ColorWarning, message,)


def printInfo(message, end = "\n"):
    print(strInfo(message), end = end)


def strInfo(message):
    return "\x1b[{0}m {1} \x1b[0m".format(ColorInfo, message)


def printError(message, end = "\n"):
    print(strError(message), end = end)


def strError(message):
    return "\x1b[{0}m {1} \x1b[0m".format(ColorError, message)


def printTime(message, end = "\n"):
    print(strTime(message), end = end)


def strTime(message):
    return "\x1b[{0}m {1:.2f} \x1b[0m".format(ColorTime, message)


def printArrow(message, end = "\n"):
    print(strArrow(message), end = end)


def strArrow(message):
    return "\x1b[{0}m {1} \x1b[0m".format(ColorTime, message)


def printCustom(message, style, fg, bg, end = "\n"):
    form = ';'.join([str(style), str(fg), str(bg)])
    print("\x1b[{}m {} \x1b[0m".format(form, message))


def printWA(testName, durationTime):
    print(strWA(testName, durationTime))


def strWA(testName, durationTime):
    return strError("WA {}".format(testName)) + strTime(durationTime)


def printAC(testName, durationTime):
    print(strAC(testName, durationTime))


def strAC(testName, durationTime):
    return strSuccess("AC {}".format(testName)) + strTime(durationTime)


def printTLE(testName):
    print(strTLE(testName))


def strTLE(testName):
    return strWarning("TLE  ") + strArrow(testName)


def printExc(status, testName):
    print(strExc(status, testName))


def strExc(status, testName):
    return strError(status.name) + strArrow(testName)
