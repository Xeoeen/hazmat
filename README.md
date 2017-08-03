# hazmat
`hazmat` is a Python shell script used to test your solution for contests like IOI or OI.

## Instalation
```sh
    # clone the repository
    git clone https://github.com/Xeoeen/hazmat.git

    # enter repository
    cd hazmat

    # use pip to install
    pip3 install -e .

    # or run make to create single-file application
    make

    # place hazmat_merged under $PATH
    mv hazmat_merged ~/.local/.bin/
    # for example

```

## Configuration
`hazmat` keeps its connfiguration file under `~/.config/hazmat.conf`.

### Example:
```json
{
    "languages" : [
        {
            "name": "C++",
            "extension": ".cpp",
            "compile": {
                "compiler": "clang++-4.0",
                "default-flags": ["-O2", "-std=c++11"],
                "format": "{} {} {} -o {}"
            },
            "merge": "mergeCompile {} {}",
            "init":{
                "default": {
                    "dirs": [ "Tests" ],
                    "files": [
                        { "src": "/home/user/template.cpp", "dest": "{}.cpp"}
                    ]
                },
                "testing" :{
                    "dirs": [ "Gen", "Valid", "Math"],
                    "files": [
                        { "src": "/home/user/math.cpp", "dest": "Math/{}-math.cpp"}
                    ]
                }
            }

        },
        {
            "name": "Haskell",
            "extension": ".hs",
            "compile":{
                "compiler": "ghc",
                "default-flags": ["-fno-code -O3"],
                "format": "{} {} {} -o {}"
            }
        },
        {
            "name": "Python",
            "extension": ".py"
        }


    ]
}

```
###### **This file should be json formatted.**

## Bugs
Feel free to create an issue.
