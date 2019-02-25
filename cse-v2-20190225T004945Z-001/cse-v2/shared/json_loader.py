import json
import sys
from shared.encrypt_it import EncryptIt


class JSONLoader:
    def __init__(self, file_name, encrypted=False, encryption_pass=None):
        try:
            if encrypted:
                self.json = json.loads(EncryptIt().decrypt_file(file_name, encryption_pass))
            else:
                with open(file_name, mode="r") as json_file:
                    self.json = json.load(json_file)
        except Exception as e:
            exit("{0}\nPlease make sure the specified file exists and is readable. Exiting...".format(e))

    def get(self, key):
        try:
            return self.json[key]
        except KeyError as e:
            print("Specified key ({0}) does not exist in the JSON file.".format(e), file=sys.stderr)
            return None
