# Prerequisites

## Database
Currently only MySQL/MariaDB is supported as the database backend.
It is recommended to have a central database / database cluster with central endpoint.

## Python
If you use Debian/Ubuntu you can install prebuild packages from the repository:

    sudo apt install python3-flask python3-crypto python3-gnupg python3-sysv-ipc python3-tabulate python3-mysqldb python3-gevent
    
otherwise run:

    pip install -r requirements.txt


# Mirgate from the [PHP implementation](https://github.com/Yubico/yubikey-val) from yubico

If you already have an working installation of the official yubikey validation server, you can only have to migrate the existing database:

    mysql> USE ykksm;
    mysql> ALTER TABLE yubikeys MODIFY aeskey TEXT;
    mysql> ALTER TABLE yubikeys ADD USER VARCHAR(32);
    mysql> USE ykval;
    mysql> ALTER TABLE clients MODIFY id INT(11) NOT NULL AUTO_INCREMENT;

# Database Setup

This step is only necessary if you create the database from scratch.

## Create two databases (ykval and ykksm):

    mysql> create database ykval;
    mysql> create database ykksm;

## Create two User for each database:

    mysql> GRANT USAGE ON *.* TO 'ykval'@'%';
    mysql> GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON `ykval`.* TO 'ykval'@'%';
    mysql> GRANT USAGE ON *.* TO 'ykksm'@'%';
    mysql> GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON `ykksm`.* TO 'ykksm'@'%';

## Create two Secure Passwords for each User:

    mysql > ALTER USER 'ykval'@'%' IDENTIFIED WITH mysql_native_password BY 'SECUREPASS_1' [REQUIRE SSL];
    mysql > ALTER USER 'ykksm'@'%' IDENTIFIED WITH mysql_native_password BY 'SECUREPASS_2' [REQUIRE SSL];

## Import Database Schemas:

    $ mysql -p -u ykval ykval < val.sql
    $ mysql -p -u ykksm ykksm < ksm.sql

## Create GPG Key [Optional]:

### install havegetd for entropy (if you going to generate the key on the server itself)
    $ sudo apt install havegetd
### create gpg home directory
    $ mkdir /var/www/yuval/gpg

### create gpg Key
    $ gpg --default-new-key-algo rsa4096 --gen-key --homedir /var/www/yuval/gpg

### add subkey for encryption
    $ gpg --homedir /var/www/yuval/gpg --edit-key <KEYID>
    gpg> addkey
    gpg> 6 # RSA (only enctrytion)
    gpg> 4096 # keysize
    gpg> 2y # valid for
    gpg> y
    gpg> y 
    gpg> safe

for key creation refer to https://help.github.com/en/github/authenticating-to-github/generating-a-new-gpg-key

#### add gpg support to pyuval.yaml

add the gpg section to the ksm key:
```
ksm:
  gpg:
    home: /var/www/html/pyuval/.gnupg/
    fingerprint: C59CD5BDC21F4E34710A6F0772ED3173C24747E5
    password: kFNFw4bPn5UfhTFvxQztkvlbr7vc9OVTykRVQ5
```

### Write Passphrase to Memory [OPTIONAL]

    $ python3 tools/writeToMemory.py

to verify the correct passwort you can show it via:

    $ python3 tools/readFromMemory.py

#### add gpg passphrase sahred memory to pyuval.yaml

add the shm section to the ksm > gpg key and remove the ksm>gpg>password key:
```
ksm:
  gpg:
#    password: kFNFw4bPn5UfhTFvxQr7vc9OVTykRVQ5
    shm:
      address: 3735935610 # Address as integer 0xdeadda7a = 3735935610 dec
``` 

# Adding a Yubikey

1. insert Yubikey
2. install and open Yubikey Personalization Tool 
    1. choose "Yubico OTP" in the most top menu
    2. klick the Advacned Button
    3. choose "Configuration Slot 1"
    4. Check "Public Identity" and klick "Generate"
    5. Check "Private Identity" and klick "Generate"
    6. klick "Generate" on the secret key line
    7. click "Write Configuration" and safe the log file
3. run `python3 tools/managePyuval.py -s yubikey -a` to add the newly created Yubikey
    1. **Serial** Serial Numer of your Yubikey (not used, for domumentation purposes only)
    2. **Username** The name of the user/owner of this specifiy Yubikey (not used, for domumentation purposes only)
    3. **Public ID** The public identity of your newly created Yubikey (4th Value in logfile)
    4. **Private ID** The public identity of your newly created Yubikey (5th Value in logfile)
    5. **AES Secret Key** The secret key of your newly created Yubikey (6th Value in logfile)

To verify the entry you can run `python3 tools/managePyuval.py -s yubikey -l` to list all yubikeys.

# Adding an application / a client

run `python3 tools/managePyuval.py -s client -a` to add an client which is allows to add to query OTP.
You need the **secret** and the **id** for the configuration of your application e.g. PAM module. You can use one ID-Secret pair for multiple applications but if you deactive it all your applications which share these token are not able to validate OTPs anymore.

To list all existing clients you can run `python3 tools/managePyuval.py -s client -l`.

# Example PAM configuration for SSHD (Debian/Ubuntu)

##### /etc/pam.d/yubikey-auth:

    apt install libpam-yubico

```
#Yubikey 2FA
auth required pam_yubico.so id=14 \
        key=ZldrCn5fMyE0PDMsVi90VDVUUU4= \
        urllist=https://pyval.mycomany.lan \
        authfile=/etc/yubikeyMappings \
        debug debug_file=/var/log/auth.log verbose_otp
```

##### /etc/pam.d/sshd:
```
# Remove common-auth
# @include common-auth
# 2FA Yubikey
@include yubikey-auth
```

##### /etc/yubikeyMappings
```
#Username:publicID1:publicID2
john.doe: cccccccccccc
will.smith: cbcbcbcbcb
```

##### /etc/ssh/sshd_config
```
[...]
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
UsePAM yes
[...]
```