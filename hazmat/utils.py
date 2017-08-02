import os


def normalize_dir(path):
    if not path.endswith("/"):
        path += "/"

    if not os.path.isdir(path):
        raise Exception("Directory does not exist")
    return path


def printFile(path):
    with open(path, 'r') as file:
        print((file.read()).strip("\n"))


def subtree_dirs(rootDir):
    list = []
    for dirName, subdirList, fileList in os.walk(rootDir):
        list.append(normalize_dir(dirName))
    return list


def get_parrarel_tests(inTestDir, outTestDir):
    list = []
    for test in os.listdir(inTestDir):
        if os.path.isfile(inTestDir + test):
            if test.endswith(".in"):
                inTest = inTestDir + test
                outTest = outTestDir + os.path.splitext(os.path.basename(test))[0] + ".out"
                if os.path.isfile(outTest):
                    list.append((inTest, outTest))

    return list
