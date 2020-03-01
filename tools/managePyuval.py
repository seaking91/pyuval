#!/usr/bin/python3

import sys
import os
import pwd
import base64
import argparse
import random
import string
from pathlib import Path
from tabulate import tabulate
from collections import OrderedDict

libPath = os.path.join(Path(__file__).absolute().parent.parent, 'pyuval/')

sys.path.append(libPath)

from config import Config
from utils import Utility
from database import Database
from pyuvalLogging import PyuvalLogging

def prettyTable(data):
    blacklist = ['internalname', 'aeskey']
    thead = list()
    tbody = list()
    if data:
        for item in data:
            if not thead:
                thead = [x for x in OrderedDict(sorted(item.items())).keys() if x not in blacklist]
            row = []
            for key, value in OrderedDict(sorted(item.items())).items():
                if key not in blacklist:
                    row.append(value)
            tbody.append(row)
        print()
        print(tabulate(tbody, thead))
        print()
    else:
        print("No data found!")

def randomString(length=20):
    return ''.join(random.choice(string.printable) for i in range(length))

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--add", help="Add new Yubikey(s) to database",
                    action="store_true", default=False, dest="add")

parser.add_argument("-l", "--list", help="list all yubikeys in database",
                    action="store_true", default=False, dest="list")

parser.add_argument("-s", "--subsystem", help="Subsystem to apply action [client, yubikey]",
                    default=None, type=str, dest="subsystem")
args = parser.parse_args()

util = Utility()
config = Config()
log = PyuvalLogging(ModuleName="ManagePyuval")

if 'SUDO_USER' in os.environ:
    user = os.environ['SUDO_USER']
else:
    user = os.environ['USER']

ksmDb = Database(**config.get('ksm:db'))

if args.subsystem == "yubikey":
    if args.add:
        serial = input('Serial: ').strip()
        username = input('Username: ').strip()
        pubID = input('Public ID: ').strip()
        privID = input('Private ID: ').strip()
        aesKey = input('AES Secret Key: ').strip()

        if config.hasGnupgSupport:
            from otpcrypto import GnuPG
            gpg = GnuPG(homedir=config.get('ksm:gpg:home'), 
                        fingerprint=config.get('ksm:gpg:fingerprint'))
            if config.hasGnupgShmSupport: 
                password = config.get('ksm:gpg:shm:address')
            else:
                password = config.get('ksm:gpg:password')
            aesKey = base64.b64encode(gpg.encrypt(aesKey).encode('UTF-8')).decode('UTF-8')


        keyData = ksmDb.insertNewYubikey(
            serial=serial,
            username=username,
            publicID=pubID,
            privateID=privID,
            aesSecret=aesKey,
            creator=user)
        
        log.audit("{} added yubikey with public ID {}".format(user, pubID))

    elif args.list:

        yubikeys = ksmDb.getAllYubikeys()
        prettyTable(yubikeys)

        log.audit("{} listed all yubikeys".format(user))

    ksmDb.close()



elif args.subsystem == "client":
    
    valDB = Database(**config.get('val:db'))

    if args.add:

        count = int(input('Number of Clients to create: ').strip())

        for i in range(0, count):
            clientSecret = randomString()
            clientSecretBase64 = base64.b64encode(clientSecret.encode('UTF-8')).decode('UTF-8')
            email = input('contact EMail [optional]: ').strip()
            notes = input('Notes [optional]: ').strip()
            if not notes or notes == "":
                notes = "Client added by {}".format(user)
            addData = valDB.insertNewClient(clientSecret=clientSecretBase64, email=email, notes=notes)
            verifyData = valDB.getClientDataBySecret(clientSecretBase64)
            print("\nClient added:")
            for column, data in verifyData.items():
                print("{}: {}" .format(column, data))
            print("\n")

            log.audit("{} added new client with id {}".format(user, verifyData['id']))
    
    elif args.list:
        clients = valDB.getAllClients()
        prettyTable(clients)

        log.audit("{} listed all clients".format(user))

    else:
        print("No Action specified!")
    valDB.close()
else:
    print("Subsystem not know!")