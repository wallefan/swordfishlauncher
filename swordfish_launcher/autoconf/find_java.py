
import os

def look_for_JAVA_HOME():
    return (os.environ.get('JAVA_HOME'), 0)

def look_for_java_in_windows_registry():
    try:
        import winreg
    except ImportError:
        print("we're not on windows")
        return
    if hasattr(winreg, 'WOW64_64KEY'):
        keytypes=(winreg.WOW64_64KEY, winreg.WOW64_32KEY)
    else:
        keytypes=(0,)
    for keytype in keytypes:
        for registry_key in (r'',):
            try:
                hkey=winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, registry_key, winreg.KEY_READ | keytype)
            except OSError:
                continue
            i=0
            try:
                recommended = winreg.QueryValueEx(hkey, 'CurrentVersion')
            except OSError:
                recommended = ''
            else:
                yield _read_java_regkey(hkey, recommended), recommended, 1
            while True:
                try:
                    subkey = winreg.EnumKey(hkey, i)
                except OSError:
                    break
                if subkey != recommended:
                    yield _read_java_regkey(hkey, subkey), subkey, 0


def _read_java_regkey(hkey, subkey):
    import winreg
    key = winreg.OpenKeyEx(hkey, subkey)
    result = winreg.QueryValueEx(key, 'JavaHome')
    key.Close()
    return result



def test_java(path):
    import subprocess
    return subprocess.Popen([path, '-version'], stderr=subprocess.PIPE).communicate()[1].decode('ascii').splitlines()
