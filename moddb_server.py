import csv
import urllib
import zipfile
import tempfile
import json
import hashlib


class ModDB:
    def __init__(self):
        self.files_to_download_locations={}
        self.forge_mods_to_files={}

    def (self):

    def download_mod(self, url, destpath=None):
        h = hashlib.sha1()
        with (open(destpath, 'x+b') if destpath else tempfile.TemporaryFile()) as fout:
            with urllib.request.urlopen(url) as fin:
                with memoryview(bytearray(1024*1024)) as buf:
                    while True:
                        count = fin.readinto1(buf)
                        if not count:
                            break
                        h.update(buf[:count])
                        fout.write(buf[:count])
            fout.seek(0)
            with zipfile.ZipFile(fout) as zf:
                with zf.open('mcmod.info') as fin:
                    info = json.load(fin)
        self.update_index(info)

    def load(self, csvfile):
        with open(csvfile) as f:
            self._parsecsv(csv.reader(f))

    def _parsecsv(self, r):
        header_row = next(r)
        assert header_row == ('Filename', 'DownloadType', 'DownloadLocation', 'SHA1', 'Disposition', 'Mod','Version'), header_row
        for filename, dltype, dlloc, sha1, disp, *mods in r:
            self.
