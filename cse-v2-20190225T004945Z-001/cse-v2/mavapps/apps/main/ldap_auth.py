import ldap
import re


class LDAPAuth:
    def __init__(self, server=None, base_dn=None, user_dn=None, username=None, password=None):
        self.server = server
        self.base_dn = base_dn
        self.user_dn = user_dn
        self.username = username
        self.password = password
        self.username_re = re.compile("(?<=uid=)([a-zA-Z0-9]{2,})(?=,)")

    def authenticate(self):
        try:
            if self.server and self.user_dn and self.base_dn and self.username and self.password:
                connect = ldap.initialize(self.server)
                connect.bind_s("uid={0},{1}".format(self.username, self.user_dn), self.password)
                result = connect.search_s(self.base_dn, 3, "uid={0}".format(self.username))
                connect.unbind_s()
                result_username = re.search(self.username_re, result[0][0])
                result_username = result_username.group(0)

                return result_username == self.username
        except Exception as e:
            print(e)
            return False
