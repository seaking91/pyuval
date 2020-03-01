#!/usr/bin/python3

from pathlib import Path
import os
import sys

libPath = os.path.join(Path(__file__).absolute().parent.parent, 'pyuval/')

sys.path.append(libPath)
from config import Config
from utils import Utility

util = Utility()
config = Config()

memoryData =  util.readDataFromMemoy(config.get('ksm:gpg:shm:address'))
print(memoryData)

