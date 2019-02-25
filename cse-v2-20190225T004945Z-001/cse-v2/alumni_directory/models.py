from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
import shared.db_models as db_models


db = SQLAlchemy()


class Graduates(db.Model, db_models.Graduates):
    pass


class Alumni(db.Model, db_models.Alumni):
    pass


class GuestGraduateModel(object):
    id = None
    uta_id = ""
    net_id = "Guest"
    first_name = "Guest"
    middle_name = ""
    last_name = ""
    mavs_email = ""
    alt_email = ""
    phone = ""
    career = ""
    plan = ""
    degree = ""
    graduation_year = None
    graduation_semester = None

    def __repr__(self):
        return "<id {0!r}, Guest>".format(self.id)


class GuestUserLoginModel(AnonymousUserMixin):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    net_id = "Guest"
    social_email = ""
    photo = None
    country = ""
    company = ""
    state = ""
    title = ""
    biography = ""
    twitter = ""
    facebook = ""
    linkedin = ""
    public_area = ""
    ispublic = False
    google_id = ""
    facebk_id = ""
    linkedin_id = ""
    graduate_info = GuestGraduateModel()

    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)

    def get_id(self):
        return self.net_id


class UserLoginModel(Alumni, UserMixin):
    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)

    def get_id(self):
        return self.net_id
