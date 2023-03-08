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

import os, shlex, sys
from tempfile import TemporaryDirectory
from configparser import ConfigParser
from argparse import ArgumentParser, Namespace
from typing import Any, Union
from venv import main as venvmain
from subprocess import Popen


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


def with_main(ns, sub_main, args, failmsg = "Main call failed: %s"):
    rc = 1
    orig_argv = sys.argv
    try:
        sys.argv = [ns.__this__, *args]
        sub_main()
        rc = 0
    except Exception as e:
        notify(failmsg, e)
        sys.exit(rc)
    finally:
        sys.argv = orig_argv
    return rc


def ensure_env(ns: Namespace):
    ## ensure that a virtualenv virtual environment exists at a path provided
    ## under the configuration namespace 'ns'
    ##
    ## For purposes of project bootstrapping, this workflow proceeds as follows:
    ## 1) Creates a bootstrap pip environment using venv in this Python process
    ## 2) Installs the virtualenv package with pip, in that environment
    ## 3) Creates the primary virtual environment using virtualenv from within
    ##    the bootstrap pip environment
    ##
    ## By default, the primary virtual environment would use the same Python
    ## implementation as that running this project.py script. This behavior
    ## may be modified by providing --python "<path>" within the
    ## --virtualenv-opts option to this project.py script.
    ##
    ## If a virtual environment exists at the provided envdir:
    ## - Exits non-zero if it does not appear to comprise a virtualenv virtual
    ##   environment, i.e if no bin/activate_this.py exists within envdir
    ## - Else, exits zero for the existing environment
    ##
    ## On success, a virtualenv virtual environment will have been installed
    ## at the envdir provided in 'ns'.
    envdir = ns.envdir
    env_cfg = os.path.join(envdir, "pyvenv.cfg")
    if os.path.exists(env_cfg):
        py_activate = os.path.join(envdir, "bin", "activate_this.py")
        if os.path.exists(py_activate):
            notify("Virtual environment already created: %s", envdir)
            sys.exit(0)
        else:
            notify("Virtual environment exists but bin/activate_this.py not found: %s",
                   envdir)
            sys.exit(7)
    else:
        with TemporaryDirectory(prefix = ns.__this__ + ".", dir = ns.tmpdir) as tmp:
            venv_args = ['--upgrade-deps', tmp]
            notify("Creating bootstrap venv environment %s", tmp)
            with_main(
                ns, venvmain, venv_args,
                "bootstrap venv creation failed: %s"
            )
            notify("Installing virtualenv in bootstrap environment %s", tmp)
            pip_opts = shlex.split(ns.pip_opts)
            pip_cmd = os.path.join(tmp, "bin", "pip")
            pip_install_argv = [pip_cmd, "install", * pip_opts, "virtualenv"]
            rc = 11
            try:
                proc = Popen(pip_install_argv,
                             stdin = sys.stdin, stdout = sys.stdout,
                             stderr = sys.stderr)
                proc.wait()
                rc = proc.returncode
            except Exception as e:
                notify("Failed to create primary virtual environment: %s", e)
                sys.exit(23)
            if (rc != 0):
                notify("Failed to install virtualenv, pip install exited %d", rc)
                sys.exit(rc)
            ## now run vitualenv to create the actual virtualenv
            envdir = ns.envdir
            notify("Creating primary virtual environment in %s", envdir)
            virtualenv_cmd = os.path.join(tmp, "bin", "virtualenv")
            virtualenv_opts = shlex.split(ns.virtualenv_opts)
            virtualenv_argv = [virtualenv_cmd, *virtualenv_opts, envdir]
            try:
                ## final subprocess call - this could be managed via exec
                proc = Popen(virtualenv_argv,
                             stdin = sys.stdin, stdout = sys.stdout,
                             stderr = sys.stderr)
                proc.wait()
                rc = proc.returncode
                if (rc != 0):
                    notify("virtualenv command exited non-zero: %d", rc)
                else:
                    notify("Created virtualenv environment in %s", envdir)
                notify("Removing bootstrap venv environment %s", tmp)
                sys.exit(rc)
            except Exception as e:
                notify("Failed to create primary virtual environment: %s", e)
                sys.exit(31)

if __name__ == "__main__":
    this = os.path.basename(__file__)
    mainparser = ArgumentParser(prog = this)
    show_help = lambda ns: mainparser.print_help(file = sys.stdout)
    tmpdir = os.environ.get("TMPDIR", None)
    mainparser.set_defaults(
        __this__ = this,
        tmpdir = tmpdir,
        func = show_help,
    )
    mainparser.add_argument(
        "--tmpdir", "-t",
        help=f'''Temporary directory for commands.
        If None, use system default. default: {tmpdir!r}''',
        default = tmpdir
    )
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
        "--envdir", "-e",
        help=f'''Directory path for virtual environment.
        default: {envdir_dflt}''',
        default = envdir_dflt
    )
    mkenv_parser.add_argument(
        "--pip-opts", "-i",
        help="Options to pass to pip install",
        default=''
    )
    mkenv_parser.add_argument(
        "--virtualenv-opts", "-o",
        help="Options to pass to virutalenv",
        default=''
    )

    ## the following section should be moved to a modular build lib
    ## then available post-boostrap with a 'build' command passing all
    ## other args to a build.py script, or using pavement.py
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
    tmpdir = ns.tmpdir
    if tmpdir is not None:
        orig_umask = os.umask(0o077)
        try:
            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
        finally:
            os.umask(orig_umask)
        os.environ["TMPDIR"] = tmpdir
    ns.func(ns)
