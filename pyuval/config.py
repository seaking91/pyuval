#!/usr/bin/python3
import yaml
from pathlib import Path, PurePath
import sys

class Config(object):

    def __init__(self):
        with open(PurePath(Path(__file__).absolute().parent, 'pyuval.yaml'), 'r') as f:
            if sys.version_info.minor <= 7:
                self.config = yaml.load(f)
            else:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
    
    def get(self, keypath):
        if keypath:
            keypathList = keypath.split(':')
            returnValue = self.config
            for keypathItem in keypathList:
                if isinstance(returnValue, dict):
                    returnValue = returnValue.get(keypathItem, None)
                    if not returnValue:
                        raise Exception("Config key {} not found in config at the given position!".format(keypathItem))
                else:
                    raise Exception("{} is not a valid config key at this position!".format(keypathItem))
            return returnValue
        else:
            return ''

    @property
    def hasGnupgSupport(self):
        if 'gpg' in self.config['ksm']:
            return True
        return False

    @property
    def hasGnupgShmSupport(self):
        if 'shm' in self.config['ksm']['gpg']:
            return True
        return False