from . import (
    live,
    init,
    run,
    test,
    compile,
    generate,
    merge)


def useAllModules(parser):
    subParser = parser.add_subparsers()
    compile.createSubParser(subParser)
    run.createSubParser(subParser)
    test.createSubParser(subParser)
    init.createSubParser(subParser)
    live.createSubParser(subParser)
    merge.createSubParser(subParser)
    generate.createSubParser(subParser)
