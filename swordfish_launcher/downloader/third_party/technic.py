import urllib.request
import urllib.parse
import json

def download_technicpack(slug):
    with urllib.request.urlopen('https://api.technicpack.net/modpack/%s?build=999'%urllib.parse.quote(slug)) as resp:
        data=json.load(resp)
    with urllib.request.urlopen(data['solder']+'modpack/'+slug) as resp:
        version_list = json.load(resp)
    with urllib.request.urlopen(data['solder']+'modpack/'+slug+'/'+version_list['recommended']) as resp:
        pack = json.load(resp)
    return pack
