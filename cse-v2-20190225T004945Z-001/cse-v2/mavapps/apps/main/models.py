from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
import shared.db_models as db_models


db = SQLAlchemy()


class Users(db.Model, db_models.Users):
    pass


class Students(db.Model, db_models.Students):
    pass


class Employees(db.Model, db_models.Employees):
    pass


class PIAccounts(db.Model, db_models.PIAccounts):
    pass


class Roles(db.Model, db_models.Roles):
    pass


class Invited_Talks(db.Model, db_models.Invited_Talks):
    pass


class UserRoles(db.Model, db_models.UserRoles):
    def __init__(self, net_id=None, role=None, **kwargs):
        super(UserRoles, self).__init__(**kwargs)
        self.net_id = net_id
        self.role = role


class Graduates(db.Model, db_models.Graduates):
    pass


class Alumni(db.Model, db_models.Alumni):
    pass


class GuestUserLoginModel(AnonymousUserMixin):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    messages_sent = None
    messages_received = None
    net_id = "Guest"
    uta_id = ""
    first_name = "Guest"
    middle_name = ""
    last_name = ""
    email = ""
    phone_number = ""
    photo = None
    is_authenticated = False
    is_active = 0
    is_temp = 0
    is_anonymous = True
    social_id = None

    user_roles = None
    employee = None
    student = None
    pi_accounts = None

    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)

    # def new_messages(self):
        # return None

    def get_id(self):
        return self.net_id


class UserLoginModel(Users, UserMixin):
    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)

    def get_id(self):
        return self.net_id
