#!/usr/bin/env python3
#
# setup.py - dynamic project configuration for pylaborate.spydy.qt5
#
# see also: ./project.py, ./Makefile
#

from setuptools import setup
import configparser, os, platform, re


def build_pyqt5_p(config):
    build_env = os.environ.get('BUILD_PYQT5', None)
    if build_env is not None:
        return False if len(build_env) == 0 else True
    elif re.match(r'.*[Bb][Ss][Dd].*', platform.system()) is not None:
        return True
    else:
        return False


def get_versions(dct):
    return ["%s>=%s" % (name, minv) for name, minv in dct.items()]


def read_deps(config):
    deps = get_versions(config['common_depends'])
    deps.extend(get_versions(config['dev_depends']))

    if build_pyqt5_p(config):
        deps.extend(get_versions(config['build_depends']))
    else:
        deps.extend(get_versions(config['run_depends']))
    return deps


def read_classifiers(config):
    return [txt for txt in config['project_classifiers'].values()]


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("project.ini")
    ## main project metadata is in project.ini
    setup(
        **config['project'],
        classifiers = read_classifiers(config),
        install_requires = read_deps(config),
        license_files = ("COPYING",),
        packages = ['pylaborate.spydy.qt5'],
        package_dir={'': 'src'}
    )
