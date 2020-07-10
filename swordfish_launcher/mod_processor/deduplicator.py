__package__='swordfish_launcher.mod_processor'

import pathlib
import zipfile

if __name__=='__main__':
    path = pathlib.Path(r'/media/windows/Users/sawor.000/MultiMC/instances')
    mods_we_know_about = dict()
    total_mods = 0
    for inst in path.iterdir():
        for jar_path in inst.rglob('*.jar'):
            try:
                zf=zipfile.ZipFile(jar_path)
            except zipfile.BadZipFile:
                print(jar_path.relative_to(path), "isn't a valid zip file!?")
                continue
            with zf:
                manifest=frozenset((x.filename, x.file_size, x.CRC) for x in zf.infolist())
            total_mods += 1
            if manifest in mods_we_know_about:
                mods_we_know_about[manifest].add(jar_path)
            else:
                mods_we_know_about[manifest] = {jar_path}

    for duplicate_set in mods_we_know_about.values():
        best_one = min(duplicate_set, key=lambda path:path.stat().st_size)
        if len(duplicate_set) == 1:
            print("Somehow, miraculously, we only have one copy of", best_one.name)
            continue
        for dup in duplicate_set:
            if dup.samefile(best_one):
                continue
            try:
                dedup_temp=pathlib.Path(str(dup.absolute())+'.dedup_tmp')
                best_one.link_to(dedup_temp)
            except OSError:
                print("Unable to deduplicate", best_one, 'to', dup)
                continue
            dup.unlink()
            dedup_temp.rename(dup)
            print('successfully deduplicated', dup, '->', best_one)


    print('Scanned', total_mods, 'JAR files')
    print(len(mods_we_know_about), 'were unique')