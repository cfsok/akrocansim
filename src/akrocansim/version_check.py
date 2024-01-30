from urllib.request import urlopen, Request
import json

from semver.version import Version

from .__init__ import __version__

def is_latest() -> str:
    http_request = Request("https://pypi.org/pypi/akrocansim/json", headers={"Accept": "application/json"})
    with urlopen(http_request) as response:
        if response.status == 200:
            latest_version = Version.parse(json.loads(response.read().decode())['info']['version'])
            current_version = Version.parse(__version__)
            if latest_version > current_version:
                return f'{latest_version} available for download'
            else:
                return 'latest'
        else:
            return 'unable to inquire latest version'
