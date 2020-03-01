#!/usr/bin/python3

import re
import os
import copy
import base64
from .config import Config
from .utils import Utility
from .config import Config
from datetime import datetime
from .database import Database
from .pyuvalLogging import PyuvalLogging
from .otpcrypto import OTPCrypto as otpcrypto

class OTPValidator(object):
    def __init__(self, source = None, **request):
        self.originalRequest = request
        self.log = PyuvalLogging()
        self.client = request.get('id', '0')
        self.nonce = request.get('nonce', '')
        self.otp = request.get('otp', '').lower()
        self.timestamp = int(request.get('timestamp', 0))
        self.h = request.get('h', '')
        self.sl = request.get('sl', 0) # sync level not further implemented
        self.timeout = request.get('timeout', '')
        self.S_OK = 'OK'
        self.S_BAD_OTP = 'BAD_OTP'
        self.S_REPLAYED_OTP = 'REPLAYED_OTP'
        self.S_DELAYED_OTP = 'DELAYED_OTP'
        self.S_BAD_SIGNATURE = 'BAD_SIGNATURE'
        self.S_MISSING_PARAMETER = 'MISSING_PARAMETER'
        self.S_NO_SUCH_CLIENT = 'NO_SUCH_CLIENT'
        self.S_OPERATION_NOT_ALLOWED = 'OPERATION_NOT_ALLOWED'
        self.S_BACKEND_ERROR = 'BACKEND_ERROR'
        self.S_NOT_ENOUGH_ANSWERS = 'NOT_ENOUGH_ANSWERS'
        self.S_REPLAYED_REQUEST = 'REPLAYED_REQUEST'
        self.S_KSM_ERROR = 'KSM_ERROR'
        self.S_KSM_ERROR_CRC = 'KSM_ERROR_CRC'
        self.tsSec = 1/8
        self.tsRelTolerance = 0.3
        self.tsAbsTolerance = 20
        self.tokenLength = 32
        self.otpMaxLenth = 48
        self.apiKey = b''
        self.util = Utility()
        self.time = "{}{}".format(
            datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%SZ0'),
            str(datetime.now().microsecond)[:3])
        self.config = Config()

        self.log.audit("Recived request from {} with otp {}".format(source, self.otp))
    
    def resonse(self, status, data = {}):
        data.update(dict(status=status))
        hmac = otpcrypto.signQuery(data, self.apiKey)
        data.update(dict(h=base64.b64encode(hmac).decode('UTF-8')))
        response = ""
        for key ,value in data.items():
            response += "{}={}\r\n".format(key, value)
        response += '\r\n' 
        self.log.info("Response: {}".format(response))
        return(response)

    def decryptOTP(self):
        keyid = self.otp[:12]
        modhexCiphertext = self.otp[12:]
        ksmDb = Database(**self.config.get('ksm:db'))
        keyData = ksmDb.getKeyData(keyid)
        ksmDb.close()
        if not keyData or not 'aeskey' in keyData:
            self.log.info("Yubikey unknown")
            return False, self.S_KSM_ERROR
        aesKey = base64.b64decode(keyData['aeskey']).decode('UTF-8')
        #aes key is gpg encrypted
        if self.config.hasGnupgSupport:
            from .otpcrypto import GnuPG
            #passphrase is in shared memory segment
            if self.config.hasGnupgShmSupport:
                password = self.util.readDataFromMemoy(self.config.get('ksm:gpg:shm:address'))
            #passphrase is in config
            else:
                password = self.config.get('ksm:gpg:password')
            #decrypt GPG key
            gpg = GnuPG(homedir=self.config.get('ksm:gpg:home'),
                        fingerprint=self.config.get('ksm:gpg:fingerprint'))
            plain_aesKey = gpg.decrypt(aesKey, password)
            
        else:
            plain_aesKey = aesKey

        ciphertext = otpcrypto.modhex2hex(modhexCiphertext)
        plaintext = otpcrypto.aes128ecb_decrypt(plain_aesKey, ciphertext)
        uid = plaintext[:12]
        if uid != keyData['internalname']:
            self.log.info("Corrupt OTP")
            return False, self.S_KSM_ERROR
        #Check CRC
        if otpcrypto.calculateCRC(plaintext) != int('0xf0b8', 16):
            self.log.info("CRC Failed Corrupt OTP")
            return False, self.S_KSM_ERROR_CRC

        self.log.info("Successfully decrypted OTP")
        return True, dict(
            sessionCounter = int("{}{}".format(plaintext[14:16], plaintext[12:14]), 16),
            low = int("{}{}".format(plaintext[18:20], plaintext[16:18]), 16),
            high = int(plaintext[20:22], 16),
            sessionUse = int(plaintext[22:24], 16),
        )

    @staticmethod
    def checkReplayed(probe1, probe2):
        return probe1['yk_counter'] == probe2['yk_counter'] and \
            probe1['yk_use'] == probe2['yk_use'] and \
            probe1['nonce'] == probe2['nonce']

    @staticmethod
    def countersHigherThanOrEqual(probe1, probe2):
        if (probe1['yk_counter'] > probe2['yk_counter']): return True
        if probe1['yk_counter'] == probe2['yk_counter'] and \
            probe1['yk_use'] >= probe2['yk_use']: return True
        return False

    def validateOTP(self):
        data = dict(
            otp = self.otp,
            nonce = self.nonce,
            t = self.time,
            sl = self.sl,
        )
        #check nonce
        if not self.nonce or self.nonce == "":
            self.log.error("Nonce is empty")
            return self.resonse(self.S_MISSING_PARAMETER, data=data)
        if not re.match(r'^[A-Za-z0-9]+$', self.nonce):
            self.log.error("Nonce is in invalid format")
            return self.resonse(self.S_MISSING_PARAMETER, data=data)
        if not 16 <= len(self.nonce) <= 40:
            self.log.error("Nonce is out of lenth bounderies: {}".format(str(len(self.nonce))))
            return self.resonse(self.S_MISSING_PARAMETER, data=data)
        self.log.audit("Provided nonce is a valid nonce.")
        #check OTP
        if re.match(r'^[jxe\.uidchtnbpygk]+$', self.otp):
            self.otp = self.otp.replace('jxe.uidchtnbpygk', 'cbdefghijklnrtuv')
            self.log.error("Dvorak OTP converted")
        if not self.otp or self.otp == "":
            self.log.error("OTP is missing")
            return self.resonse(self.S_MISSING_PARAMETER, data=data)
        if len(self.otp) < self.tokenLength or len(self.otp) > self.otpMaxLenth:
            self.log.error("Incorrect OTP length: {}".format(self.otp))
            return self.resonse(self.S_BAD_OTP, data=data)
        if not re.match(r'^([cbdefghijklnrtuv]{0,16})([cbdefghijklnrtuv]{32})$', self.otp):
            self.log.error("Incorrect OTP format: {}".format(self.otp))
            return self.resonse(self.S_BAD_OTP, data=data)
        #check Client
        if not re.match(r"^[0-9]+$", self.client) or self.client == "0":
            self.log.error("Client ID is not valid: {}".format(self.client))
            return self.resonse(self.S_MISSING_PARAMETER, data=data)
        #check HMAC
        valDb = Database(**self.config.get('val:db'))
        client = valDb.getClientData(self.client)
        if not client:
            self.log.error("Client with ID {} not found in database.".format(self.client))
            return self.resonse(self.S_NO_SUCH_CLIENT)
        self.apiKey =  base64.b64decode(client['secret'])
        requestDatatoSign = copy.deepcopy(self.originalRequest)
        del requestDatatoSign['h']
        hmac = otpcrypto.signQuery(requestDatatoSign, self.apiKey)
        if not hmac == base64.b64decode(self.h):
            self.log.error("HMAC missmatch! client hmac: {}, server hmac: {}.".format(hmac.decode('UTF-8'), base64.b64decode(self.h).decode('UTF-8')))
            return self.resonse(self.S_BAD_SIGNATURE, data=data)
        ksmSuccess, ksmData = self.decryptOTP()
        if not ksmSuccess:
            self.log.error("OTP decryption faild for OTP {}".format(self.otp))
            return self.resonse(self.S_KSM_ERROR, data=data)
        publicId = self.otp[0:len(self.otp) - self.tokenLength]
        keyParams = valDb.getKeyParams(publicId)
        if not keyParams:
            self.log.info("Key with public ID {} not found".format(publicId))
            return self.resonse(self.S_NO_SUCH_CLIENT, data=data)
        
        otpData = dict(
              modified = self.timestamp,
              otp = self.otp,
              nonce = self.nonce,
              yk_publicname = publicId,
              yk_counter = ksmData['sessionCounter'],
              yk_use = ksmData['sessionUse'],
              yk_high = ksmData['high'],
              yk_low = ksmData['low']
            )

        if self.checkReplayed(keyParams, otpData):
            self.log.error("Replayed Request")
            return self.resonse(self.S_REPLAYED_REQUEST, data=data)
        if self.countersHigherThanOrEqual(keyParams, otpData):
            self.log.error("Replayed OTP Counter Missmatch")
            return self.resonse(self.S_REPLAYED_OTP, data=data)
        updateSuccess, updateData = valDb.updateDbCounters(otpData)
        if not updateSuccess:
            self.log.error("Update Error, {}".format(updateData))
            return self.resonse(self.S_BACKEND_ERROR)
        
        #END
        valDb.close()
        if self.timestamp == 1:
            data.update(dict(
                timestamp = ( ksmData['high'] << 16 ) + ksmData['low'],
                sessioncounter = ksmData['sessionCounter'],
                sessionuse = ksmData['sessionUse'],
            ))
        self.log.info("Valid OTP {} provided sending success response.".format(self.otp))
        return self.resonse(self.S_OK, data=data)
