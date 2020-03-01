#!/usr/bin/python3

import MySQLdb
import MySQLdb.cursors

class Database(object):
    def __init__(self, **kwargs):
        self.connection = MySQLdb.connect(
            host = kwargs.get('host', 'localhost'),
            user = kwargs.get('user', 'root'),
            db = kwargs.get('db', 'ksm'),
            passwd=kwargs.get('password', ''),
            ssl=kwargs.get('sslopts', {}),
            cursorclass= MySQLdb.cursors.DictCursor,
            )
        self.cursor = self.connection.cursor()

    def read(self, query, multiple = False):
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        if multiple:
            return result
        else:
            if len(result) != 1:
                return None
            else:
                return result[0]

    def write(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def getAllClients(self):
        query = "SELECT * from clients order by id DESC"
        return self.read(query, multiple=True)

    def getAllYubikeys(self):
        query = "SELECT * from yubikeys"
        return self.read(query, multiple=True)

    def getClientData(self, client):
        query = "SELECT id, secret FROM clients WHERE active='1' AND id='{}'".format(client)
        return self.read(query)

    def getClientDataBySecret(self, secret):
        query = "SELECT * FROM clients WHERE secret='{}'".format(secret)
        return self.read(query)

    def getKeyData(self, keyId):
        query = "SELECT aeskey, internalname FROM yubikeys WHERE publicname = '{}' AND active = 1" .format(keyId)
        return self.read(query)

    def getKeyParams(self, id):
        query = "SELECT * from yubikeys where yk_publicname = '{}'".format(id)
        data = self.read(query)
        if not data:
            createKeyQuery = """
            INSERT INTO
                yubikeys
            (
                active,
                created,
                modified,
                yk_publicname,
                yk_counter,
                yk_use,
                yk_low,
                yk_high,
                nonce,
                notes
            )
            VALUES
            (
                1,
                now(),
                -1,
                "{}",
                -1,
                -1,
                -1,
                -1,
                '0000000000000000',
                ''
            )""".format(id)
            self.write(createKeyQuery)
        return self.read(query)

    def updateDbCounters(self, data = {}):
        currentKeyValues = self.getKeyParams(data['yk_publicname'])
        if data['yk_counter'] > currentKeyValues['yk_counter'] or \
            (data['yk_counter'] == currentKeyValues['yk_counter'] and \
             data['yk_use'] > currentKeyValues['yk_use']):
            query = """
            UPDATE 
                yubikeys
            SET
                modified='{}',
                yk_counter={},
                yk_use={},
                yk_low={},
                yk_high={},
                nonce='{}'
            WHERE yk_publicname = '{}'
            """.format(
                data['modified'],
                data['yk_counter'],
                data['yk_use'],
                data['yk_low'],
                data['yk_high'],
                data['nonce'],
                data['yk_publicname'],
                )
            try:
                self.cursor.execute(query)
                self.connection.commit()
                return True, "Update successful"
            except Exception as e:
                return False, "Update error {}: {}".format(type(e).__name__, e.args)
        else:
            return False, "Comparison ERROR"

    def insertNewYubikey(self, serial = "", username = "", publicID = "", privateID = "", aesSecret = "", creator = ""):
        query = """
        INSERT INTO
            yubikeys
        SET
            serialnr = {},
            active = 1,
            hardware = 1,
            publicname = "{}",
            created = NOW(),
            internalname = "{}",
            aeskey = "{}",
            lockcode = "000000000000",
            creator = "{}",
            user = "{}"
        """.format(
            serial,
            publicID,
            privateID,
            aesSecret,
            creator,
            username
        )
        self.write(query)

    def insertNewClient(self, clientSecret = "", email = "", notes = "", otp = ""):
        query = """
        INSERT INTO 
            clients
        SET
            active = 1,
            created = NOW(),
            secret = "{}",
            email = "{}",
            notes = "{}",
            otp = "{}"
        """.format(
            clientSecret,
            email,
            notes,
            otp
        )
        self.write(query)

    def close(self):
        self.connection.close()