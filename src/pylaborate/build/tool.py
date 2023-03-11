## pylaborate.build.tool

from configparser import ConfigParser
from typing import Optional

from .program import Program


class Tool(Program):
    ## simple Program using an INI-type tool configuration file
    ##
    ## An early prototype - this class does not use modules outside of
    ## the Python standard library in Python 3.10, e.g TOML support

    def __init__(self, name: Optional[str] = None,
                 inifile: Optional[str] = None):
        super().__init__(name = name)
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
            ## FIXME handle the condition locally,
            ## when the configuration file does not exist
            ## - raise ...
            conf.read(ini)
            self._conf = conf
            return conf
        else:
            return self._conf
