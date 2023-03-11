# pylaborate.build.program

import os, sys
from argparse import Action, ArgumentParser, Namespace
from typing import Optional


class Program:
    def __init__(self, name: Optional[str] = None):
        if name is None:
            name = os.path.basename(sys.argv[0])
        self._name = name

    @classmethod
    def commands(cls) -> Optional[list[str]]:
        ## default protocol method, defining no commands
        ##
        ## %% Main Documentation %%
        ##
        ## * Defining Program Commands:
        ##
        ## For each command `<name>` returned from `cls.commands()`,
        ## the following methods will be used, if defined:
        ##
        ## - `def set_<name>_opts(self, parser, subparser, root_parser)`
        ##
        ##   This method should configure any arguments and options for
        ##   the named command. (An illustration should be provided
        ##   here, in some later release of this library)
        ##
        ##   The `parser` object will provide an argument parser for the
        ##   named command.
        ##
        ##   The `subparser` will provide an Action object, such that
        ##   was created as with the following:
        ##
        ##   `root_parser.add_subparsers(** self.get_subparser_args()`
        ##
        ##   The `root_parser` will provide the main argument parser for
        ##   the implementing Program.
        ##
        ## - `def run_<name>(self, namespace: Namespace)`
        ##
        ##   This method will be run when the command is selected at the
        ##   command line.
        ##
        ##   The `namespace` object will provide values parsed from
        ##   the command line options for the implementing Program.
        ##
        ## * Configuring Program Arguments and Options:
        ##
        ## An implementing class may define a method `set_<name>_opts`
        ## as described above, to define the options for a named
        ## command.
        ##
        ## To add argument definitions to the main program, an
        ## implementing class may override the `setopts()` method.
        ## The overriding method may define any arguments and options,
        ## using the ArgumentParser returned from the superclass'
        ## `setopts()` method and should return the updated
        ## ArgumentParser.
        ##
        ## * Command semantics:
        ##
        ## If no `run_<name>` method is defined for a command
        ## specified in `commands()` then `run_command(name)` will be
        ## called as a default when the named command is specified at
        ## the shell command line.
        ##
        ## `run_command(None)` will be called when a Program is called
        ## without any commands.
        ##
        ## If `run_command` is not overridden in the implementing class, the
        ## default `run_command` method will raise a runtime error, for
        ## any command name either None or a command name string.
        ##
        ## * Parser Initialization
        ##
        ## When the main ArgumentParser is initialized for an
        ## implementing program, the program's `get_main_parser_args`
        ## method will be called to provide the set of keyword args for
        ## that ArgumentParser.
        ##
        ## When a subparser Action is added to the main ArgumentParser,
        ## such as for parsing any set of command options, the method
        ## `get_subparser_args` will be called to provide the set of
        ## keyword arguments, such as for the call
        ## `main_parser.add_subparsers(**kwargs)`
        ##
        ## When an ArgumentParser is initialized for parsing arguments
        ## to an individual command, the method `get_command_parser_args`
        ## will be called to provide initialization arguments to the
        ## command's ArgumentParser.
        ##
        ## When a  `set_<name>_opts` method is defined for a named
        ## command, then the command argument parser, subparser Action,
        ## and main program argument parser will each be provided to
        ## the method. This call will be dispatched from within the
        ## `define_command_opts` method.
        ##
        ## * Advanced Behaviors: Main Parser Defaults
        ##
        ## Defaults for the main parser can be configured by overriding
        ## the method `Program.set_main_parser_defaults()`. The
        ## behaviors of that method, as defined in the Program class,
        ## may be indicated as follows:
        ##
        ## If a program definines commands and is called without any
        ## commands in the program arguments, the default behavior
        ## provided in  `Program.set_main_parser_defaults()` will ensure
        ## that the help documentation for the program is written to the
        ## stdout stream.
        ##
        ## If a program defines no commands, the default behavior
        ## provided in `Program.set_main_parser_defaults()` will
        ## ensure that the function returned from
        ## `get_default_runner(None)` will be called when the Program is
        ## run. By default, that function will call `run_command(None)`
        ## for the implementing program.
        ##
        ## * Behaviors under --help
        ##
        ## By default, no command runner will be reached when a program
        ## or command is run as with `--help` or `-h`
        return None

    @property
    def name(self):
        return self._name

    def get_main_parser_args(self) -> dict:
        ## return a dictionary of keyword arguments to be used when
        ## initializing the main ArgumentParser for this program
        return dict(prog = self.name)

    def set_main_parser_defaults(self, parser: ArgumentParser):
        ## for any Program defining commands, if the Program is called
        ## without any commands, then print the help text to stdout
        cmds = self.commands()
        if (cmds is not None) or (len(cmds) == 0):
            ## set a default runner for a Program defining no commands
            parser.set_defaults(func = self.get_default_runner(None))
        elif not parser.get_default('func'):
            ## set a default runner to print help docs, when no command
            ## are provided to the Program
            fn = lambda ns: parser.print_help(file = sys.stdout)
            parser.set_defaults(func = fn)

    def get_default_runner(self, cmd_name: str):
        ## return a default command runner for dispatching to run_command(name)
        ## when a named command is activated. used in setopts()
        ##
        ## This indirection is used to ensure that the 'name' stays bound
        ## to its initially provided value, when the lambda is called
        return lambda ns: self.run_command(cmd_name, ns)

    def get_dispatch_runner(self, mtd: callable):
        ## return a dispatching self.<mtd> runner
        ##
        ## This function will be used to dispatch to any run_<cmd_name>
        ## method
        return lambda ns: mtd(self, ns)

    def define_command_opts(self, cmd_name: str, cmd_args_parser: ArgumentParser,
                           cmd_subparser: Action,
                           root_parser: ArgumentParser):
        ## dispatching caller for define_command
        setter = self.__class__.__dict__.get("set_" + cmd_name + "_opts", None)
        if setter is not None:
            setter(self, cmd_args_parser, cmd_subparser, root_parser)
            ## FIXME log for debug if no set_<cmd>_opts attr was defined
            ## log warning/critical if an attr was defined but is not callable

    def get_subparser_args(self) -> dict:
        ## return a dictionary of keyword arguments to be used for
        ## parser.add_subparsers(**kwargs) such as when initializing a
        ## subparser for command arguments
        return dict(title ="commands",
                    description = "Supported Commands",
                    help = "Action to run. See individual command help")

    def get_command_parser_args(self, cmd_name: str) -> dict:
        ## return a dictionary of keyword args, to be used when
        ## initializing the ArgumentParser for a named command
        return {}

    def make_command_lambda(self, cmd_name: str) -> callable:
        ## return a lambda function implementing a program command
        ##
        ## The function returned from here should accept a single arg,
        ## as the Namespace configured from parsed options for the command
        dct = self.__class__.__dict__
        mtd = dct.get("run_" + cmd_name, None)
        ##
        if mtd is None:
            ## the default runner function will dispatch to call
            ##     self.run_command(cmd_name, ns)
            ## there providing the parsed args Namespace received
            ## by the runner function as 'ns', after the cmd_name
            ## provdied here
            return self.get_default_runner(cmd_name)
        else:
            ## create a dispatching function for calling mtd
            ##
            ## the receiving method will be called with the parsed
            ## Namespace as an argument, after 'self'
            ##
            ## FIXME this does not verify that the named attr is callable
            return self.get_dispatch_runner(mtd)

    def define_command(self, cmd_name: str, subparser: Action,
                       root_parser: ArgumentParser) -> ArgumentParser:
        ## define options, args, and the run func for a named command
        parser_args = self.get_command_parser_args(cmd_name)
        cmd_args_parser = subparser.add_parser(cmd_name, **parser_args)
        self.define_command_opts(cmd_name, cmd_args_parser, subparser, root_parser)
        if not cmd_args_parser.get_default('func'):
            fn = self.make_command_lambda(cmd_name)
            cmd_args_parser.set_defaults(func = fn)
        return cmd_args_parser

    def run_command(self, cmd_name: Optional[str], namespace: Namespace):
        ## default command runner
        ##
        ## - If called from a subcommand func, as after setopts(),
        ##   cmd_name would be a string, the command name. This function
        ##   would not be reached if a run_<cmd_name> method was
        ##   defined.
        ##
        ## - If called as the func for a Program defininig no
        ##   subcommands, cmd_name will be None
        ##
        ## - namespace: the object returned from the arg parser in getopts()
        ##
        ## Additional caveats:
        ##
        ## * Any implementing class not defining subcommands _should_
        ##   override this method
        ##
        ## * Any implementing class defining subcommands _may_ override
        ##   this method. An overriding method should be implemented for
        ##   any one or more cases of `cmd_name`, i.e a string or None
        ##
        ## * For a class that defines commands, then when that class is
        ##   called in a shell script called without commands, the
        ##   default function added in setopts() will print help
        ##   documentation to the stdout stream
        ##
        msg = None
        if cmd_name is None:
            msg = "reached default run_command"
        else:
            msg = f"reached default run_command for {cmd_name!r}"
        raise RuntimeError(msg, self)

    def setopts(self, parser: ArgumentParser):
        ## configure any command options and runner functions for this Program
        cmds = self.commands()
        if (cmds is not None) and (len(cmds) 1= 0):
            subparser = parser.add_subparsers(**self.get_subparser_args())
            for cmd_name in cmds:
                self.define_command(cmd_name, subparser, parser)
        self.set_main_parser_defaults(parser)
        return parser

    def getopts(self, args: list[str] = sys.argv) -> Namespace:
        ## return a Namespace configured from parsed arguments
        ## for this Program
        ap = ArgumentParser(** self.get_main_parser_args())
        self.setopts(ap)
        return ap.parse_args(args)

    def run(self, args: list[str] = sys.argv):
        ## define program options, parse args, and run the primary func
        ## as selected for the parsed args
        ns = self.getopts(args = args)
        return ns.func(ns)
