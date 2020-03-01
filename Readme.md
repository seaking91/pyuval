# pyuval
Pyuval is a replacement for the yubikey One Time Password (OTP) Validationserver written in python3 using flask.
It is bases on the original [PHP implementation](https://github.com/Yubico/yubikey-val) from [yubico](https://developers.yubico.com/yubikey-val/).

This implementation add the functionality to encrypt the AES Plaintext key with a GPG key and optionally write the passphrase direct to memory without having it anywhere on disk.

Installation and Setup instruction can de found in the docs/install.md file.