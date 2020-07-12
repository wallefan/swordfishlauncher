from ..modpack import AbstractModpack
import zipfile
from ..http_api import API
import urllib.parse
import json

CURSEFORGE_API = API('https://addons-ecs.forgesvc.net/api/v2', {'User-Agent': 'SwordfishLauncher 0.1'})


class CurseModpack(AbstractModpack):
    def __init__(self, info):
        super().__init__(info['name'], info['summary'], None)
        if info['attachments']:
            self._icon_url = info['attachments'][0]['url']
            self._background_image_url = info['attachments'][1]['url'] if len(info['attachments']) > 1 else None

    @classmethod
    def from_project_id(cls, project_id):
        return cls(CURSEFORGE_API.get_json('/addon/%d'%project_id))

    @classmethod
    def search(cls, searchQuery, gameVersion=None, index=0, count=25):
        path = ('/addon/search?gameId=432&'  # 432 = Minecraft
                'sectionId=4471&'  # 4471 = Minecraft modpacks
                'index=%d&count=%d&searchFilter=%s'
                )%(index, count, urllib.parse.quote(searchQuery))
        if gameVersion:
            path += '&gameVersion='+gameVersion
        # For whatever reason, the Curseforge API straight up ignores all but the first word of the search query.
        searchQuery=searchQuery.casefold()
        return [cls(info) for info in CURSEFORGE_API.get_json(path) if searchQuery in info['name'].casefold()]

    def _get_image_bytes(self, image_type):
        if image_type == 'icon':
            with urllib.request.urlopen(self._icon_url) as req:
                return (req.read(), req.headers.get_content_subtype())
        elif image_type == 'background':
            with urllib.request.urlopen(self._icon_url) as req:
                return (req.read(), req.headers.get_content_subtype)
        else:
            return None

    def download(self, version:str=None):
        pass