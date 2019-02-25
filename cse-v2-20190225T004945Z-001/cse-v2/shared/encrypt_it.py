from simplecrypt import encrypt, decrypt
import sys
import json


class EncryptIt:
    def __init__(self):
        pass

    @staticmethod
    def encrypt_text(text=None, password=None):
        if text and password:
            return encrypt(password, text)
        else:
            print("Text encryption failed, make sure text and password are provided.", file=sys.stderr)
            return None

    @staticmethod
    def encrypt_file(file_name=None, password=None):
        try:
            with open(file_name, mode="r") as encrypt_in:
                with open("{0}.encrypted".format(file_name), mode="wb") as encrypt_out:
                    encrypt_out.write(encrypt(password, encrypt_in.read().encode('utf8')))
        except Exception as e:
            print("{0}\nFile encryption failed, make sure a file and password are provided.".format(e), file=sys.stderr)
            return None

    @staticmethod
    def decrypt_text(text=None, password=None):
        if text and password:
            return decrypt(password, text)
        else:
            print("Text decryption failed, make sure text and password are provided.", file=sys.stderr)
            return None

    @staticmethod
    def decrypt_file(file_name=None, password=None):
        try:
            with open(file_name, mode="rb") as encrypt_in:
                return decrypt(password, encrypt_in.read()).decode("utf-8")
        except Exception as e:
            print("{0}\nFile decryption failed, make sure a file and password are provided.".format(e), file=sys.stderr)
            return None


if __name__ == "__main__":
    # with open("./settings.json", mode="w") as settings_json:
        # with open(".settings_key", mode="r") as sk:
            # d_json = EncryptIt().decrypt_file("./settings.json.encrypted", sk.readline().strip())
            # json.dump(json.loads(d_json), settings_json)

    # with open(".settings_key", mode="r") as sk:
        # EncryptIt().encrypt_file("./settings.json", sk.readline().strip())

    pass
