#!/usr/bin/python3

import getpass
from pathlib import Path, PurePath
import sys
import os


libPath = os.path.join(Path(__file__).absolute().parent.parent, 'pyuval/')
sys.path.append(libPath)
from config import Config
from utils import Utility

util = Utility()
config = Config()

s = getpass.getpass("GPG Passphrase for Yubikey AES Secret Data Encryption Key: ")
util.writeDataToMemory(config.get('ksm:gpg:shm:address'), 0o0600, s)
