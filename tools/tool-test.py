#!/usr/bin/env python3

## trivial test script for the Tool API
##
## see also: ./piptool, providing a working
## test case for the underlying Program API
##
## Notes:
## - this file was refactored from an earlier prototype for a project.py
##
## - this uses python -m venv, whereas the top-level project.py
##   installs a virtualenv environment from a boostrap tmpdir

import os, sys
from argparse import Action, ArgumentParser
from typing import Any

PROJECT_DIR = os.environ.get("PROJECT_DIR", None)
if PROJECT_DIR is None:
    PROJECT_DIR = os.getcwd()

if os.environ.get("VIRTUAL_ENV", None) is None:
    ## activate a virtual environment in this Python
    envdir = os.environ.get("ENV_DIR", None)
    if envdir is None:
        envdir = os.path.join(PROJECT_DIR, "env")
    activate_py = os.path.join(envdir, "bin", "activate_this.py")
    if os.path.exists(activate_py):
        exec(open(activate_py).read(), {'__file__': activate_py})

from pylaborate.build import Tool

class ProjectTool(Tool):

    @classmethod
    def commands(cls):
        ## be sure to test without defining commands()
        ## in a subclass of each of Program, Tool
        return ("ensure_env", "build", "test")

    def set_ensure_env_opts(self, parser: ArgumentParser, subparser: Action,
                            root_parser: ArgumentParser):
        envdir_dflt = os.path.join(os.getcwd(), "env")
        ## optional positional args not supported here
        parser.add_argument("--envdir", '-e',
                            help=f'''Directory path for virtual environment.
                            default: {envdir_dflt}''',
                            default = envdir_dflt)

        prompt_dflt = os.getenv("VENV_PROMPT", "env")
        parser.add_argument("--prompt", "-p",
                            help=f'''Virtual Environment prompt string. \
                            overrides VENV_PROMPT, if provided.
                            default: {prompt_dflt!r}''',
                            default = prompt_dflt)

    def notify(self, fmt: str, *args: list[Any]):
        ## utility method for user notification during cmd exec
        print("#-- " + fmt % args, file = sys.stderr)

    def run_ensure_env(self, ns):
        prompt = ns.prompt
        envdir = ns.envdir
        env_cfg = os.path.join(envdir, "pyvenv.cfg")
        if os.path.exists(env_cfg):
            ## not an error, process will exit 0, thus not breaking any Makefile
            ## calling this project.py
            self.notify("Virtual environment already created: %s", envdir)
        else:
            self.notify("Creating virtual environment %r in %s", prompt, envdir)
            import venv
            args = ['--prompt', prompt, '--upgrade-deps', envdir]
            venv.main(args)

    def run_build(self, ns):
        print("not implemented (build)")


if __name__ == "__main__":
    t = ProjectTool(inifile = os.path.join(PROJECT_DIR, "project.ini"))
    t.run(sys.argv[1:])
