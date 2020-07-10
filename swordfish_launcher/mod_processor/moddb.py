import csv
import socket
from collections import namedtuple

class ModDB:
    def __init__(self, file):
        self.file=file
        with open(file) as f:
            r=csv.reader(f)
            keys = next(r,())
            for line in f:
                meta=dict(zip(keys,line))
                rest=line[len(keys):]
                modids=rest[::2]
                versions=rest[1::2]
                
