#!/usr/bin/python

import hmac
import gnupg
import base64
import hashlib
from Crypto.Cipher import AES
from collections import OrderedDict
from urllib.parse import urlencode, unquote

class OTPCrypto(object):
    def __init__(self):
        pass

    @staticmethod
    def signQuery(queryValues, apiKey):
        orderedQueryValues = OrderedDict(sorted(queryValues.items()))
        queryString = unquote(urlencode(orderedQueryValues, encoding='utf-8'))
        hmacSHA1 = hmac.new(
            apiKey,
            queryString.encode('UTF-8'),
            hashlib.sha1
            ).digest()
        return hmacSHA1

    @staticmethod
    def modhex2hex(text):
        plainhex = "0123456789abcdef"
        modhex = "cbdefghijklnrtuv"
        for search, replace in zip(modhex, plainhex):
            text = text.replace(search, replace)
        return text

    @staticmethod
    def hex2byte(xx):
        pos = 0
        byte = bytearray()
        while pos < len(xx):
                x = '{}{}'.format(xx[pos],xx[pos+1])
                byte.append(int(x, 16))
                pos += 2
        return bytes(byte)

    @staticmethod
    def aes128ecb_decrypt(aeskey, encdata):
        return AES.new(OTPCrypto.hex2byte(aeskey), AES.MODE_ECB).decrypt(OTPCrypto.hex2byte(encdata)).hex()

    @staticmethod
    def calculateCRC(plain):
        crc = 0xffff
        for i in range(0, 16):
            b = int(plain[i*2] + plain[(i*2)+1], 16)
            crc = crc ^ ( b & 0xff)
            for _ in range(0, 8):
                n = crc & 1
                crc = crc >> 1
                if n != 0:
                    crc = crc ^ 0x8408
        return crc

class GnuPG(object):
    def __init__(self, homedir=None, fingerprint=None):
        self.fingerprint = None
        if not homedir or not fingerprint:
            raise Exception("GPG homedir or fingerprint missing!")
        self.gpg = gnupg.GPG(gnupghome=homedir)
        for key in self.gpg.list_keys():
            if key['fingerprint'] == fingerprint:
                self.fingerprint = fingerprint
        if not self.fingerprint:
            raise Exception("No GPG key with fingerprint {} found in GPG homedir {}!".format(fingerprint, homedir))
    
    def encrypt(self, data):
        return str(self.gpg.encrypt(data, self.fingerprint))

    def decrypt(self, data, password):
        return str(self.gpg.decrypt(data, passphrase=password))