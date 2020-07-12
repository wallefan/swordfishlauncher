import urllib.request
import urllib.parse
import json
from ..modpack import AbstractModpack


def download_technicpack(slug):
    with urllib.request.urlopen('https://api.technicpack.net/modpack/%s?build=999' % urllib.parse.quote(slug)) as resp:
        data = json.load(resp)
    with urllib.request.urlopen(data['solder'] + 'modpack/' + slug) as resp:
        version_list = json.load(resp)
    with urllib.request.urlopen(data['solder'] + 'modpack/' + slug + '/' + version_list['recommended']) as resp:
        pack = json.load(resp)
    return pack


class TechnicModpack(AbstractModpack):
    def __init__(self, slug):
        with urllib.request.urlopen(
                'https://api.technicpack.net/modpack/%s?build=999' % urllib.parse.quote(slug)) as resp:
            data = json.load(resp)
        self.solder=data['solder']
        self.url = data['url']
        self.advertised_version = data['version'] # only valid if solder is absent.
        self.icon = data['icon']['url']
        self.bg = data['background']['url']

    def download(self, version: str = None):
        if self.solder is None:
            assert version == self.

    def getVersions(self):
        if self.solder is None:
            return [self.only_version]
