## pylaborate.build.tool

import os, sys
from configparser import ConfigParser
from argparse import Action, ArgumentParser, Namespace
from typing import Any, Optional, Union

from .program import Program


def args_after(selector: Union[str, callable], args = sys.argv) -> list[str]:
    ## utility method for dispatch in running with argparse
    ##
    ## return all args in 'args' after some provided selector
    ##
    ## selector as a string: matching arg must be == to the selector
    ##
    ## selector as callable: callable must accept one arg,
    ##     i.e each successive element in args,
    ##     then returning a truthy value for the first matching arg
    ##
    ## example:
    ##
    ## ```python
    ## # test.py
    ##
    ## import os, sys
    ## from argparse import ArgumentParser
    ##
    ## this = os.path.basename(__file__)
    ## parser = ArgumentParser(prog = this)
    ## func_dflt = lambda ns: print(f"{this} running with verbosity {ns.verbose}")
    ## parser.set_defaults(func = func_dflt)
    ## parser.add_argument("--verbose", "-v", action="count", default=0)
    ##
    ## cmd_args = args_after(lambda arg: os.path.basename(arg) == this)
    ## ns = parser.parse_args(cmd_args)
    ## ns.func(ns)
    ## ```
    ##
    ## ```sh
    ## $ python3 -X importtime test.py -vv
    ## ```
    ##
    test = None
    if callable(selector):
        test = selector
    else:
        test = lambda a: a == selector
    n = 1
    matched = False
    for idx in range(len(args)):
        arg = args[idx]
        if matched:
            n = idx
            break
        else:
            matched = test(arg)
    return args[n:]


class Tool(Program):
    def __init__(self, inifile: Optional[str] = None):
        super().__init__()
        self._inifile = inifile
        self._conf = None

    @property
    def inifile(self) -> Optional[str]:
        return self._inifile

    @property
    def conf(self) -> Optional[dict]:
        ini = self.inifile
        if self._conf is None and ini is not None:
            conf = ConfigParser()
            conf.read(ini)
            self._conf = conf
            return conf
        else:
            return self._conf


## test in ../../../tools/tool-test.py
