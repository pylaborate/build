#!/usr/bin/env python3

## project.py for pylaborate.spydy.qt5
##
## Usage
## - used for general shell command tooling via the project Makefile
## - for command usage, run as e.g 'python3 project.py --help'
##
## Limitations
## - For purposes of project boostrapping, this code must use classes
##   and methods only from stdlib

import os, sys
from configparser import ConfigParser
from argparse import ArgumentParser, Namespace
from typing import Any, Union


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


def notify(fmt: str, *args: list[Any]):
    ## utility method for user notification during cmd exec
    print("#-- " + fmt % args, file = sys.stderr)


def ensure_env(ns: Namespace):
    prompt = ns.prompt
    envdir = ns.envdir
    env_cfg = os.path.join(envdir, "pyvenv.cfg")
    if os.path.exists(env_cfg):
        ## not an error, process will exit 0, thus not breaking any Makefile
        ## calling this project.py
        notify("Virtual environment already created: %s", envdir)
    else:
        notify("Creating virtual environment %r in %s", prompt, envdir)
        import venv
        args = ['--prompt', prompt, '--upgrade-deps', envdir]
        venv.main(args)


if __name__ == "__main__":
    this = os.path.basename(__file__)
    mainparser = ArgumentParser(prog = this)
    show_help = lambda ns: mainparser.print_help(file = sys.stdout)
    mainparser.set_defaults(func = show_help)
    subparser = mainparser.add_subparsers(
        title = "commands",
        help = "Single action to run (see command help)",
    )

    mkenv_parser = subparser.add_parser(
        "ensure_env",
        help = "Ensure a virtual environment is created",
        description = "Ensure a virtual environment is created"
    )
    mkenv_parser.set_defaults(func = ensure_env)
    envdir_dflt = os.path.join(os.getcwd(), "env")
    mkenv_parser.add_argument(
        "--envdir", '-e',
        help=f'''Directory path for virtual environment.
        default: {envdir_dflt}''',
        default = envdir_dflt
    )
    prompt_dflt = "env"
    mkenv_parser.add_argument(
        "--prompt", "-p",
        help=f'''Virtual Environment prompt string.
        default: {prompt_dflt!r}''',
        default = prompt_dflt
    )

    ## the following section should be moved to a modular build lib
    ## then available post-boostrap with a 'build' command passing all
    ## other args to a build.py script
    conf = ConfigParser()
    conf.read("project.ini")
    bld_parser = subparser.add_parser(
        "build",
        help = "(unimplemented)"
    )
    pyqt5_dflt = conf['run_depends']['PyQt5']
    bld_parser.add_argument(
        "--pyqt5-version",
        help=f'''PyQt5 version for build.
        default: {pyqt5_dflt}''',
        default = pyqt5_dflt)
    pyqt_bld_dflt = conf['build_depends']['PyQt-builder']
    bld_parser.add_argument(
        "--pyqt-builder-version",
        help=f'''PyQt-builder version for build.
        default: {pyqt_bld_dflt}''',
        default = pyqt_bld_dflt)
    ## qmake availability by platform:
    ##
    ## - openSUSE: via libqt5-qtbase-common-devel
    ##   typically as /usr/bin/qt5-qmake (symlink)
    ##   and e.g /usr/lib64/qt5/bin/qmake (binary file)
    ##   see also: python<pyversion>-qt5-devel, patterns-kde-devel_qt5
    ##   /usr/lib64/qt5/mkspecs
    ##
    ## - Fedora: via qt5-qtbase-devel
    ##   typically as /usr/bin/qmake-qt5 ...
    ##   see also: https://src.fedoraproject.org/rpms/python-qt5
    ##   https://src.fedoraproject.org/rpms/python-qt5/blob/rawhide/f/python-qt5.spec
    ##   NB --qmake-setting 'QMAKE_CXXFLAGS_RELEASE="%{optflags} `pkg-config --cflags dbus-python`"'
    ##   dbus-python n/a via pip
    ##
    ## - Debian and Debian-based distros: via qt5-qmake, qt5-qmake-bin
    ##   typically as ... and /usr/lib/qt5/bin/qmake
    ##   see also: qtbase5-dev,
    ##   https://tracker.debian.org/pkg/qtbase-opensource-src
    ##
    ## - NetBSD, pkgsrc: via pkgsrc x11/qt5-qtbase,
    ##   typically as /usr/pkg/qt5/bin/qmake
    ##   see also: /usr/pkg/qt5/mkspecs/
    ##
    ## - FreeBSD ports: via port devel/qt5-qmake,
    ##   typically as /usr/local/bin/qt5-qmake (symlink)
    ##   and /usr/local/lib/qt5/bin/qmake (binary file)
    ##   see also: /usr/local/lib/qt5/mkspecs/
    ##
    ## - mingw/msys2: (untested)
    ##   via mingw-<platform>-qt5-base, e.g mingw-w64-x86_64-qt5-base
    ##   as e.g /mingw64/bin/qmake.exe
    ##   see also: https://wiki.qt.io/MinGW
    ##   (may not be as easily detected here)
    ##
    qmake_dflt = os.getenv("QMAKE", None)
    if qmake_dflt is None:
        basedirs_try = ["/usr/pkg/", "/usr/local/lib", "/usr/lib64", "/usr/lib"]
        for d in basedirs_try:
            pfx = os.path.join(d, "qt5")
            if os.path.exists(pfx):
                qmk = os.path.join(pfx, "bin", "qmake")
                if os.path.exists(qmk):
                    qt5_prefix = pfx
                    qmake_dflt = qmk
                    break
    ## usage: --qmake path for sip-build under the pyqt5 sources
    bld_parser.add_argument(
        "--qmake",
        help=f'''path to qmake for this build.
        default on this host: {qmake_dflt}''',
        default = qmake_dflt)
    ## add'l opts to do :
    ##
    ## --qmake-spec : optional. --spec path for sip-build under pyqt5
    ## e.g --qmake-spec /usr/local/lib/qt5/mkspecs/freebsd-clang
    ## default: TBD (might be removed from tool)
    ##
    ## --qml => if false, add --no-qml-plugin to sip-build
    ##
    ## --designer-plugin => if false, add --no-designer-plugin
    ##
    ## --dbus => if false, add --no-dbus-python to sip-build
    ##
    ## --dbus-incdir => for --dbus incpath for sip-build
    ## e.g $(pkg-config --variable=includedir dbus-python)
    ## && pydbus-common @ FreeBSD
    ##
    ## --jobs / -j => sip-build --jobs arg (not clear if this has any effect...)
    ##
    ## --cc, --cxx
    ##
    ## ...

    ## run with argparser
    cmd_args = args_after(lambda a: os.path.basename(a) == this)
    ns = mainparser.parse_args(cmd_args)
    ns.func(ns)
