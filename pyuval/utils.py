#!/usr/bin/python
import sysv_ipc

class Utility(object):
    def __init__(self):
        pass
    
    @staticmethod
    def readDataFromMemoy(address):
        try:
            return sysv_ipc.SharedMemory(address).read().decode('UTF-8')
        except:
            raise Exception("ERROR reading from memory. Is segment populated?")

    @staticmethod
    def writeDataToMemory(address, mode, data):
        memory = sysv_ipc.SharedMemory(address, sysv_ipc.IPC_CREAT, mode, len(data.strip().encode('UTF-8')))
        return memory.write(data.strip())