import json.decoder
import zipfile
import pathlib
import time
from string import ascii_letters
ascii_letters+='_'

# So apparently Minecraft modders have no idea what the f*$& a JSON is.
# * ambientsounds's mcmod.info doesn't have a version key.
# * jecalculation's has the line
#       "dependencies": [jei],
# many, MANY mods list 'mod_MinecraftForge' as a dependency,

# So I had to get creative.

# This is a straight copy of json/scanner.py, except that I removed the StopIteration raise and instead implemented
# a bare string parser.


import re
NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))

def py_make_scanner(context):
    parse_object = context.parse_object
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    parse_constant = context.parse_constant
    object_hook = context.object_hook
    object_pairs_hook = context.object_pairs_hook
    memo = context.memo

    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration(idx)

        if nextchar == '"':
            return parse_string(string, idx + 1, strict)
        elif nextchar == '{':
            return parse_object((string, idx + 1), strict,
                _scan_once, object_hook, object_pairs_hook, memo)
        elif nextchar == '[':
            return parse_array((string, idx + 1), _scan_once)
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            return None, idx + 4
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            return True, idx + 4
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            return False, idx + 5

        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = parse_int(integer)
            return res, m.end()
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            return parse_constant('NaN'), idx + 3
        elif nextchar == 'I' and string[idx:idx + 8] == 'Infinity':
            return parse_constant('Infinity'), idx + 8
        elif nextchar == '-' and string[idx:idx + 9] == '-Infinity':
            return parse_constant('-Infinity'), idx + 9
        else:
            # it is a name, but those incompetent monkeys can't be bothered to make it a string
            stopidx=idx+1
            while string[stopidx] in ascii_letters:
                stopidx+=1
            return string[idx:stopidx], stopidx

    def scan_once(string, idx):
        try:
            return _scan_once(string, idx)
        finally:
            memo.clear()

    return scan_once


json_parser = json.decoder.JSONDecoder(strict=False)
json_parser.scan_once = py_make_scanner(json_parser)


def index_mods(path:pathlib.Path):
    times=[]
    index={}
    for jarfile in path.glob('*.jar'):
        t1=time.perf_counter()
        data = get_info(jarfile)
        if 'modList' in data:
            data = data['modList']
        if not data:
            print(jarfile.name, 'does not list ANY mods in its mcmod.info')
        elif len(data) > 1:
            print(jarfile.name, [mod['modid'] for mod in data])
        for mod in data:
            index.setdefault(mod['modid'], {})[mod.get('version', None)] = jarfile.name
        t2=time.perf_counter()
        times.append(t2-t1)
    print('Indexed', len(times), 'mods in', sum(times), 'seconds; avg', sum(times)/len(times) if times else 0, 'per mod')
    return index


def get_info(jarfile):
    with zipfile.ZipFile(jarfile) as zf:
        if 'mcmod.info' not in zf.namelist():
            print(jarfile.name, 'does not HAVE an mcmod.info')
            return None
        data = zf.read('mcmod.info').decode('utf8')
    return json_parser.decode(data)


if __name__=='__main__':
    p=pathlib.Path(r'/media/windows/Users/sawor.000/MultiMC/instances/Eternal-1.3.5.3/minecraft/mods')
    index = index_mods(p)
    index.update(index_mods(pathlib.Path(r'C:\Users\sawor.000\MultiMC\instances\Eternal-1.3.5.3\minecraft\coremods')))
    from swordfish_launcher.mod_processor.server_ping import server_list_ping
    server_ver, mods = server_list_ping('redbaron.local')
    jarfiles_required=set()
    missing_mods=[]
    misversioned_mods=[]
    for modid, ver in mods.items():
        available_versions = index.get(modid)
        if available_versions is None:
            print(f'no jarfiles at all found for {modid} (server needs version {ver})')
            if 'core' not in modid:
                missing_mods.append(modid)
            continue            
        if ver.upper() == 'ANY':
            ver = max(available_versions.keys()) # i do not think this is wise, as it will sort 0.9 before 0.10 but I have no other proposal.
        jarfile = available_versions.get(ver)
        if jarfile is None:
            if None in available_versions:
                jarfile = available_versions[None]
                print(f"{jarfile}'s mcmod.info does not list a version; assuming it matches {ver} specified by server")
            else:
                print(f'none of our versions of {modid} ({", ".join(available_versions)}) match the version on the server ({ver})')
                misversioned_mods.append(modid)
                continue
        jarfiles_required.add(jarfile)
    unused_mods=[]
    for jarfile in p.glob('*.jar'):
        if jarfile.name not in jarfiles_required:
            print('Did not use', jarfile.name)
            with zipfile.ZipFile(jarfile) as zf:
                if 'mcmod.info' not in zf.namelist():
                    print("no mcmod.info, so it's forgivable")
                else:
                    with zf.open('mcmod.info') as f:
                        data=json_parser.decode(f.read().decode('utf8'))
                        if 'modList' in data:
                            data=data['modList']
                        unused_mods.extend(mod['modid'] for mod in data if mod['modid'] not in misversioned_mods)
    for mod in missing_mods:
        print(mod, 'is only on the server')
    for mod in unused_mods:
        print(mod, 'is only on the client')

