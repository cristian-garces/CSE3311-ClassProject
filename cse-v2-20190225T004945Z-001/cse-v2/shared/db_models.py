from sqlalchemy import ForeignKey, Column, Boolean, Integer, String, Date, DateTime, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    # messages_sent = relationship('Messages', foreign_keys='Messages.sender_net_id', backref='author', lazy=True)
    # messages_received = relationship('Messages', foreign_keys='Messages.recipient_net_id', backref='recipient', lazy=True)

    net_id = Column("NetId", String(30), unique=True, nullable=False, primary_key=True)
    uta_id = Column("UtaId", String(10), unique=True, nullable=True)
    first_name = Column("Fname", String(100), unique=False, nullable=True)
    middle_name = Column("Mname", String(100), unique=False, nullable=True)
    last_name = Column("Lname", String(100), unique=False, nullable=True)
    email = Column("UtaEmail", String(150), unique=False, nullable=True)
    phone_number = Column("Phone", String(20), unique=False, nullable=True)
    photo = Column("Photo", BLOB, unique=False, nullable=True)
    is_authenticated = Column("Authenticated", Boolean, default=False, unique=False, nullable=False)
    is_active = Column("IsActive", Integer, default=0, unique=False, nullable=False)
    is_temp = Column("IsTemp", Integer, default=0, unique=False, nullable=False)
    is_anonymous = False
    social_id = None

    # ################################################################################################################ #
    # ######################### Foreign Key Relationships & Columns Mapped From Other Tables ######################### #
    # ################################################################################################################ #
    employee_info = relationship('Employees', foreign_keys='Employees.net_id', backref='user', uselist=False, lazy=True)
    student_info = relationship('Students', foreign_keys='Students.net_id', backref='user', uselist=False, lazy=True)
    user_roles = relationship('UserRoles', foreign_keys='UserRoles.net_id', backref='user', lazy=True)
    pi_accounts = relationship('PIAccounts', foreign_keys='PIAccounts.net_id', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)

    # def new_messages(self):
        # return Messages.query.filter_by(recipient=self).filter(Messages.is_new is True).count()


"""
class Messages(Base):
    __tablename__ = 'messages'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column("ID", Integer, unique=True, nullable=False, primary_key=True)
    sender_net_id = Column("SenderNetID", String(30), ForeignKey("users.NetId"), unique=False, nullable=False)
    recipient_net_id = Column("RecipientNetID", String(30), ForeignKey("users.NetId"), unique=False, nullable=False)
    title = Column("Title", String(500), unique=False, nullable=False)
    body = Column("Body", String(500), unique=False, nullable=False)
    timestamp = Column("Timestamp", DateTime, unique=False, nullable=False, default=datetime.now())
    is_new = Column("IsNew", Boolean, unique=False, nullable=False)
    is_archived = Column("IsArchived", Boolean, unique=False, nullable=False)

    def __repr__(self):
        return "<id {0!r}, sender_net_id {1!r}>".format(self.id, self.sender_net_id)
"""


class Employees(Base):
    __tablename__ = 'employee'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    net_id = Column("EmNetId", String(30), ForeignKey("users.NetId"), unique=True, nullable=False, primary_key=True)
    name = Column("OfficialName", String(100), nullable=True)
    title = Column("Title", String(500), nullable=True)
    office = Column("Office", String(10), nullable=True)
    office_building = Column("OfficeBldg", String(30), nullable=True)


class Students(Base):
    __tablename__ = 'students'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    net_id = Column("StuNetId", String(30), ForeignKey("users.NetId"), unique=True, nullable=False, primary_key=True)
    program = Column("Program", String(50), unique=False, nullable=True)
    degree = Column("Degree", String(10), unique=False, nullable=True)
    plan = Column("Plan", String(20), unique=False, nullable=True)
    start_date = Column("StartDate", Date, unique=False, nullable=True)
    resume = Column("Resume", BLOB, unique=False, nullable=True)
    i_listen = Column("IListen", String(10), unique=False, nullable=True)
    i_writing = Column("IWriting", String(10), unique=False, nullable=True)
    i_read = Column("IRead", String(10), unique=False, nullable=True)
    i_overall = Column("IOverall", String(10), unique=False, nullable=True)
    t_listen = Column("TListen", String(10), unique=False, nullable=True)
    t_speaking = Column("TSpeaking", String(10), unique=False, nullable=True)
    t_writing = Column("TWriting", String(10), unique=False, nullable=True)
    t_reading = Column("TReading", String(10), unique=False, nullable=True)
    t_overall = Column("TOverall", String(10), unique=False, nullable=True)
    gre_verbal = Column("GREVerbal", String(10), unique=False, nullable=True)
    gre_quant = Column("GREQuant", String(10), unique=False, nullable=True)
    gre_writing = Column("GREWriting", String(10), unique=False, nullable=True)
    gre_total = Column("GRETotal", String(10), unique=False, nullable=True)
    website = Column("Website", String(50), unique=False, nullable=True)
    office = Column("Office", String(10), unique=False, nullable=True)
    lab = Column("Lab", Integer, unique=False, nullable=True)
    primary_research = Column("PrimaryResearch", Integer, unique=False, nullable=True)
    research_1 = Column("Research1", Integer, unique=False, nullable=True)
    research_2 = Column("Research2", Integer, unique=False, nullable=True)
    research_3 = Column("Research3", Integer, unique=False, nullable=True)
    research_int = Column("ResearchInt", String(200), unique=False, nullable=True)
    apply_gta = Column("ApplyGTA", Integer, unique=False, nullable=True)
    opt = Column("OPT", Integer, unique=False, nullable=True)
    time = Column("Time", String(20), unique=False, nullable=True)
    is_discontinued = Column("IsDiscontinued", Integer, unique=False, nullable=True)

    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)


class Roles(Base):
    __tablename__ = 'roles'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    role = Column("RoleType", String(20), unique=True, nullable=False, primary_key=True)
    description = Column("Description", String(200), unique=False, nullable=False)

    def __repr__(self):
        return "<role {0!r}>".format(self.role)


class UserRoles(Base):
    __tablename__ = 'users_roles'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    net_id = Column("NetId", String(30), ForeignKey("users.NetId"), unique=True, nullable=False, primary_key=True)
    role = Column("RoleType", String(20), unique=False, nullable=False, primary_key=True)

    def __repr__(self):
        return "<net_id, role {0!r}, {1!r}>".format(self.net_id, self.role)


class PIAccounts(Base):
    __tablename__ = 'cost_center'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    account_number = Column("CCNumber", String(50), unique=True, nullable=False, primary_key=True)
    description = Column("Description", String(50), unique=False, nullable=False)
    net_id = Column("PINetId", String(50), ForeignKey("users.NetId"), unique=False, nullable=False)
    end_date = Column("EndDate", String(50), unique=False, nullable=False)

    def __repr__(self):
        return "<account {0!r}>".format(self.account_number)


class Graduates(Base):
    __tablename__ = 'graduates'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column("Idx", Integer, unique=True, nullable=False, primary_key=True)
    uta_id = Column("StuId", String(20), unique=False, nullable=False)
    net_id = Column("StuNetId", String(30), ForeignKey("alumni.NetId"), unique=False, nullable=False)
    first_name = Column("Fname", String(50), unique=False, nullable=False)
    middle_name = Column("Mname", String(50), unique=False, nullable=True)
    last_name = Column("Lname", String(50), unique=False, nullable=False)
    mavs_email = Column("MavsEmail", String(100), unique=False, nullable=False)
    alt_email = Column("AltEmail", String(100), unique=False, nullable=True)
    phone = Column("Phone", String(15), unique=False, nullable=True)
    career = Column("Career", String(50), unique=False, nullable=True)
    plan = Column("Plan", String(50), unique=False, nullable=True)
    degree = Column("Degree", String(10), unique=False, nullable=True)
    graduation_year = Column("GradYear", Integer, unique=False, nullable=False)
    graduation_semester = Column("GradSemester", Integer, unique=False, nullable=False)

    def __repr__(self):
        return "<id {0!r}>".format(self.id)


class Alumni(Base):
    __tablename__ = 'alumni'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    net_id = Column("NetId", String(30), unique=False, nullable=False, primary_key=True)
    social_email = Column("SocialEmail", String(100), unique=False, nullable=True)
    photo = Column("Photo", BLOB, unique=False, nullable=True)
    country = Column("Country", String(3), unique=False, nullable=True)
    company = Column("Company", String(50), unique=False, nullable=True)
    state = Column("State", String(2), unique=False, nullable=True)
    title = Column("Title", String(50), unique=False, nullable=True)
    biography = Column("Biography", String(500), unique=False, nullable=True)
    twitter = Column("Twitter", String(50), unique=False, nullable=True)
    facebook = Column("Facebook", String(50), unique=False, nullable=True)
    linkedin = Column("LinkedIn", String(50), unique=False, nullable=True)
    public_area = Column("PublicArea", String(25), unique=False, nullable=True)
    ispublic = Column("IsPublic", Boolean, unique=False, nullable=False)
    google_id = Column("GoogleID", String(100), unique=True, nullable=True)
    facebk_id = Column("FacebookID", String(100), unique=True, nullable=True)
    linkedin_id = Column("LinkedinID", String(100), unique=True, nullable=True)
    graduate_info = relationship('Graduates', foreign_keys='Graduates.net_id', uselist=False, lazy="joined")

    def __repr__(self):
        return "<net_id {0!r}>".format(self.net_id)


class Invited_Talks(Base):
    __tablename__ = "invited_talks"
    __table__table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    idx = Column("Idx", Integer, unique=True, nullable=False, primary_key=True)
    f_name = Column("FName", String(50), unique=False, nullable=False)
    l_name = Column("LName", String(50), unique=False, nullable=False)
    photo = Column("Photo", BLOB, unique=False, nullable=True)
    institution = Column("Institution", String(300), nullable=False)
    date = Column("Date", Date, unique=False, nullable=False)
    start_time = Column("StartTime", String(5), unique=False, nullable=False)
    end_time = Column("EndTime", String(5), unique=False, nullable=False)
    location = Column("Location", String(20), unique=False, nullable=False)
    title = Column("Title", String(500), unique=False, nullable=False)
    abstract = Column("Abstract", String(5000), unique=False, nullable=False)
    bio = Column("Biography", String(5000), unique=False, nullable=False)
    host = Column("Host", String(30), unique=False, nullable=False)
    number = Column("Number", Integer, unique=False, nullable=False)

    def __repr__(self):
        return "<idx {0!r}>".format(self.net_id)
