## pylaborate.build.program

import sys

from argparse import Action, ArgumentParser, Namespace
from typing import Optional

class Program:

    @classmethod
    def commands(cls) -> Optional[list[str]]:
        ## default protocol method (no subcommands)
        ##
        ## for each subcommand <name> returned from here, the following  methods
        ## will be used if defined - initialized via setopts():
        ## - set_<name>_opts - configure cmd options.
        ##   Must return the ArgumentParser used for the subcommand (FIXME)
        ## - run_<name>
        ##   Function to run when the command is active (and not --help)
        ##   If not defined, then for any active subcommand, the method
        ##   run_command(name) will be called (by default: raises error)
        return None

    def add_cmd(self, name: str, subparser: Action, *args) -> ArgumentParser:
        ## convenience method for set_<cmd>_opts methods
        return subparser.add_parser(name, *args)

    def default_runner(self, name: str):
        ## return a default command runner for dispatching to run_command
        ## when a named command is activated. used in setopts()
        ##
        ## this indirection is used to ensure that the 'name' stays bound
        ## to its initially provided value, when the lambda is called
        return lambda ns: self.run_command(name, ns)

    def dispatch_runner(self, mtd: callable):
        ## return a dispatching self.<mtd> runner
        ## used for command wrapping onto self.run_<cmd> via setopts()
        return lambda ns: mtd(self, ns)

    def run_command(self, name: Optional[str], namespace: Namespace):
        ## default command runner
        ## - name would be a string, the command name, if called from
        ##   a default subcommand func after setopts()
        ## - if reached as the default top-level command, name will be None
        ##
        ## - namespace: the object returned from the arg parser in getopts(),
        ##   available to methods overriding this fallback
        raise RuntimeError(f"reached default run_command for {name!r}", self, name)

    def setopts(self, parser: ArgumentParser):
        cmds = self.commands()
        if cmds is not None:
            ## FIXME parameterize the subparsers call
            ## e.g setting non-default command-section args for --help text
            subp = parser.add_subparsers(title ="commands",
                                         description = "Supported Commands",
                                         help = "Action to run. See individual command help")
            dct = self.__class__.__dict__
            for cmd in cmds:
                ## dispatch to each defined set_<cmd>_opts method,
                ## by default calling add_cmd(cmd)
                setter = dct.get("set_" + cmd + "_opts", None)
                if setter is None:
                    ## ensure the cmd is added to the arg parser,
                    ## whether to be run via self.run_<cmd>()
                    ## or via self.run_command(<cmd>)
                    cmd_parser = self.add_cmd(cmd, subp)
                else:
                    ## call method - it must return an ArgumentParser
                    ## (FIXME) such that can be used for further configuration here
                    cmd_parser = setter(self, parser, subp)
                if isinstance(cmd_parser, ArgumentParser):
                    ## configure a default func to run for the command,
                    ## if none was defined under set_<cmd>_opts
                    fn = cmd_parser.get_default('func')
                    if fn is None:
                        runner = dct.get("run_" + cmd, None)
                        if runner is None:
                            ## DEBUG
                            # print("Configuring runner {runner} for {cmd}")
                            ## calls self.run_command(<cmd>)
                            fn = self.default_runner(cmd)
                        else:
                            ## DEBUG
                            # print("Configuring default runner for {cmd}")
                            ## calls the method self.run_<cmd>()
                            fn = self.dispatch_runner(runner)
                            cmd_parser.set_defaults(func = fn)
        return parser

    ## FIXME it uses __file__ for this file
    def getopts(self, prog: str = __file__, args=sys.argv):
        ap = ArgumentParser(prog = prog)
        self.setopts(ap)
        fn = ap.get_default('func')
        if fn is None:
            cmds = self.commands()
            if cmds is None or len(cmds) != 0:
                ## for a command-less implementation,
                ## dispatch to the default runner
                fn = self.default_runner(None)
            else:
                ## set a default top-level func to print help docs,
                ## if commands are defined but no subcommand was provided
                fn = lambda ns: ap.print_help(file = sys.stdout)
            ap.set_defaults(func = fn)
        ## this exits when --help:
        return ap.parse_args(args)

    def run(self, args=sys.argv):
        ns = self.getopts(args = args)
        ## not reached under --help
        ns.func(ns)
