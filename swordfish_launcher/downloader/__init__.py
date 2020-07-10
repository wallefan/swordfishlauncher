import http.client
from tkinter import ttk
import threading
import urllib.request
import tempfile
import zipfile
import io
import os


def download(fin:http.client.HTTPResponse, fout, progressbar:ttk.Progressbar):
    if progressbar:
        filesize=fin.getheader('Content-Length')
        if filesize:
            progressbar.configure(value=0, mode='determinate', max=filesize)
        else:
            progressbar.configure(value=0, mode='indeterminate', max=1024*1024)
    with memoryview(bytearray(1024*1024)) as buffer:
        count=fin.readinto1(buffer)
        while count:
            if progressbar:
                progressbar.step(count)
            if count == 1024*1024:
                fout.write(buffer)
            else:
                fout.write(buffer[:count])
            count = fin.readinto1(buffer)

# NOTE: The original SwordfishPDS had a much better thread system.
# Downloader objects were simply frontends to a queue and contained multiple threads which would work on the same
# instance.  I ditched this for Swordfish Launcher because having multiple simultaneous download threads pointing at the
# same server will at best go slower than a single thread and at worst get you an IP ban.

# I also ditched the functionality it had where it started downloading the first mod before it had received the URL
# of the last one from the server.

# It kind of hurt to omit these features from the new version because I was kind of proud of them when I first came
# up with them.


class Downloader(threading.Thread):
    def __init__(self, server, queue, urlformat, outputdir, overall_progressbar, download_progressbar):
        self.client=http.client.HTTPSConnection(server)
        self.queue=queue
        self.urlformat=urlformat
        self.outputdir=outputdir
        self.overall_progressbar = overall_progressbar
        self.download_progressbar = download_progressbar
        self.failed_downloads = {}

    def run(self):
        self.overall_progressbar.config(mode='determinate', max=len(self.queue), value=0)
        while self.queue:
            outfile, *fmt = self.queue.pop()
            outpath = os.path.join(self.outputdir, outfile)
            with open(outpath+'.part', 'ab') as fout:
                headers = {'User-Agent': 'Swordfish-Launcher 1.0'}
                if fout.tell() != 0:
                    headers['Range'] = 'bytes=%d-' % fout.tell()
                    expected_code = 206
                else:
                    expected_code = 200
                self.client.request('GET', self.urlformat.format(*fmt, filename=outfile.replace(os.sep, '/')),
                                    headers=headers)
                with self.client.getresponse() as resp:
                    if resp.code != expected_code:
                        self.failed_downloads[outfile] = resp.code
                        continue
                    download(resp, fout, self.download_progressbar)
            os.rename(outpath+'.part', outpath)
            self.overall_progressbar.step()

    def join(self):
        super().join()
        return self.failed_downloads

class ZipDownloader(Downloader):
    def run(self):
        while True:
            url=self.queue.get()
            if url is None:
                return
            with urllib.request.urlopen(url) as fin:
                size=fin.getheader('Content-Length', 0)
                if size > 25*1024*1024:
                    ftmp=tempfile.TemporaryFile()
                else:
                    ftmp=io.BytesIO(size)
                download(fin, ftmp, self.progressbar)
            ftmp.seek(0)
            with zipfile.ZipFile(ftmp) as zf:
                # I would just use zf.extractall() but I wanted the progress bar.
                zf.extractall()
                files=[]
                for name in zf.namelist():
                    if name.endswith('/'):
                        os.makedirs(os.path.join(self.destpath, file), exist_ok=True)
                    else:
                        files.append(zf.getinfo(name))

                self.progressbar.config(mode='determinate', value=0, max=sum(zi.file_size for zi in files))
                for member in files:

                    ### THIS PORTION COPY PASTED FROM zipfile.py ###

                    # build the destination pathname, replacing
                    # forward slashes to platform specific separators.
                    arcname = member.filename.replace('/', os.path.sep)

                    if os.path.altsep:
                        arcname = arcname.replace(os.path.altsep, os.path.sep)
                    # interpret absolute pathname as relative, remove drive letter or
                    # UNC path, redundant separators, "." and ".." components.
                    arcname = os.path.splitdrive(arcname)[1]
                    invalid_path_parts = ('', os.path.curdir, os.path.pardir)
                    arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                               if x not in invalid_path_parts)
                    if os.path.sep == '\\':
                        # filter illegal characters on Windows
                        arcname = zf._sanitize_windows_name(arcname, os.path.sep)

                    targetpath = os.path.join(targetpath, arcname)
                    targetpath = os.path.normpath(targetpath)

                    ### END COPY PASTE FROM zipfile.py ###

                    os.makedirs(os.path.dirname(targetpath), exist_ok=True)
                    if not member.isdir():
                        with open(targetpath, 'wb') as fout, zf.open(member) as fin:
                            data = fin.read(1024*1024)
                            self.progressbar.step(len(data))
                            fout.write(data)

