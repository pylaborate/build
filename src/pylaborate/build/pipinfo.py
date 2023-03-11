## pylaborate.build.pipinfo

import datetime
from collections import namedtuple, ChainMap
from packaging import version
from typing import Optional
import requests


## https://requests.readthedocs.io/en/latest/user/quickstart/
## https://requests.readthedocs.io/en/latest/user/advanced/


class JsonData():
    '''utility class for transformation of JSON data into a Pythonic
    object

    See also: The `pip_data` function, in this module'''

    def __init__(self, src: dict = {}):
        ## defining new classes that may not be GC's may cause a memory leak
        ## for long-running processes - needs further study ...
        data_name = "_%s_%s" % (self.__class__.__name__, hash(self))
        chain = ChainMap()
        keys = []
        for name, data in src.items():
            keys.append(name)
            if isinstance(data, dict):
                ## parsing only at the top level, assuming each key in the data
                ## can be used as an attribute name ...
                ## FIXME translate any unusable names
                value = data
            else:
                value = data
            chain = chain.new_child({name: value})
        ntpl = namedtuple(data_name, keys)
        self._data_class = ntpl
        self._data = ntpl(**chain)

    @property
    def data_class(self) -> type:
        '''convenience method, returning the class identity of the local
        class defined in the `data` property'''
        return self._data_class

    @property
    def data(self) -> namedtuple:
        '''local storage for data parsed from JSON'''
        return self._data


class PipData(JsonData):
    '''a generalized interface onto PyPI-style JSON data'''

    def __init__(self, src: dict = {}):
        super().__init__(src)
        self._cached_versions = None
        self._cached_latest = None
        self._cached_release = {}
        self._cached_srcinfo = {}

    @staticmethod
    def str_time(string: str, fmt: str = "%Y-%m-%dT%H:%M:%S.%f%z") -> datetime:
        '''return a datetime parsed from a timestamp string.

        The default format string is compatible with the ISO 8601
        timestatmp string format used within PyPI package information'''
        return datetime.datetime.strptime(string, fmt)

    @property
    def versions(self) -> list[str]:
        '''return a list of available release versions for this data
        structure

        The return value will be sorted such that each monotically higher
        version string will appear earlier in the list'''
        if self._cached_versions is None:
            ## sorting by semantic version parse, highest to lowest
            s = sorted([version.parse(v) for v in self.release_data.keys()],
                       reverse=True)
            versions = [str(v) for v in s]
            self._cached_versions = versions
            return versions
        else:
            return self._cached_versions

    @property
    def latest_version(self) -> str:
        if self._cached_latest is None:
            version = self.versions[0]
            self._cached_latest = version
            return version
        else:
            return self._cached_latest

    @property
    def release_data(self) -> dict:
        '''return a dictionary of release data for this data structure

        Each key in the return value will represent a release version,
        while each value will provide information about a pip wheel,
        sdist, or other file avaialble for that version.'''
        return self.data.releases

    def get_release(self, version: Optional[str] = None) -> list[dict]:
        '''return the release information for a single release in this
        data structure.

        If a version is not provided, the monotically highest release
        version will be used.

        If no release information is available for the specified
        version, raises a RuntimeError'''
        if version is None:
            version = self.versions[0]
        if version in self._cached_release:
            return self._cached_release[version]
        elif version in self.release_data:
            data = self.release_data[version]
            self._cached_release[version] = data
            return data
        else:
            raise RuntimeError(f"No release data found for version {version}", version)

    def release_source_data(self, version: Optional[str] = None) -> Optional[dict]:
        '''return the package index data for the sdist archive of a release
        version, if available.

        If a rlease version is not accompanied with an sdist archive, returns
        None for that version'''
        if version is None:
            version = self.latest_version
        if version in self._cached_srcinfo:
            return self._cached_srcinfo[version]
        else:
            reldata = self.get_release(version)
            srcinfo = None
            for info in reldata:
                if info['packagetype'] == 'sdist':
                    srcinfo = info
                    break
            self._cached_srcinfo[version] = srcinfo
            return srcinfo

def pip_data(pkgname: str):
    '''Initialize and return a PipData object, using the latest JSON data
    available from PyPI'''
    hdrs = {'accept': "application/json"}
    ## may throw "connection aborted" eg, or HTTP error under raise_for_status
    ## TBD handling requests.exception.ConnectionError
    r = requests.get("https://pypi.org/pypi/%s/json" % pkgname, headers = hdrs)
    r.raise_for_status()
    j = r.json()
    return PipData(j)

