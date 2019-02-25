from re import match, compile, IGNORECASE
from datetime import timedelta
from os import scandir, path, rename
from shutil import rmtree
from functools import wraps
from flask import Flask, request, abort
from flask_login import login_manager, current_user
from mavapps.apps.main.models import GuestUserLoginModel, Roles, UserRoles
from shared.constants import SETTINGS, SRV, CA_FILE, generate_version_file

APPS_LIST = []
APP_ACCESS_ROLES = {
    "reimbursement": ["DEV", "FAC", "FINANCE", "SADM"],
    "role_management": ["DEV", "SADM"],
    "messages": ["DEV", "SADM"],
    "cse_talks": ["DEV", "SADM"]
}
APP_DIRECTORY = path.dirname(path.realpath(__file__))
GIT_HASH = generate_version_file(APP_DIRECTORY)
REQUEST_REF_RE = compile("^(http[s]?://((127|0).0.0.[10]|localhost):[0-9]{4}|(https://(cse(-sandbox|-dev|-test)?.uta.edu/)))")

EXCLUDED_APPS = ["/apps/main", "/apps/api", "/apps/messages", "/apps/alumni_directory", "pycache"]
AUTO_VERSION_APPS = ["main", "reimbursement", "role_management", "messages", "cse_talks"]

app = Flask(__name__)
login_daemon = login_manager.LoginManager()
login_daemon.anonymous_user = GuestUserLoginModel
login_daemon.login_view = "login"
login_daemon.login_message = "Please login to access the applications."
login_daemon.login_message_category = "error"

if SRV != "localhost":
    app.config["SESSION_COOKIE_SECURE"] = True
app.config["PREFERRED_URL_SCHEME"] = "https"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=31)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SQLALCHEMY_POOL_RECYCLE"] = 120
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8mb4{5}'.format(
    SETTINGS.get("{0}_server_user".format(SRV)),
    SETTINGS.get("{0}_server_password".format(SRV)),
    SETTINGS.get("{0}_server_url".format(SRV)),
    SETTINGS.get("{0}_server_port".format(SRV)),
    SETTINGS.get("{0}_server_name".format(SRV)),
    CA_FILE)


class UnknownOperatorError(Exception):
    def __init__(self):
        default_message = "Unknown operator used, please make sure only or's and and's are used when assigning app roles."
        super().__init__(default_message)


def get_user_roles(net_id=None):
    net_id = net_id or current_user.net_id
    user_roles = {row.role: False for row in Roles.query.all()}

    for r in UserRoles.query.filter_by(net_id=net_id).all():
        user_roles[r.role] = True

    return user_roles


def verify_roles(roles_list, user_roles=None):
    current_user_roles = user_roles or get_user_roles()
    for role in roles_list:
        if current_user_roles[role]:
            return True
    return False


def verify_app_roles(roles=None, user_roles=None):
    user_roles = user_roles or get_user_roles()

    if roles and user_roles:
        role_dict = roles[0]

        if role_dict["negated"]:
            truth_value = not user_roles[role_dict["role"]]
        else:
            truth_value = user_roles[role_dict["role"]]
        try:
            if role_dict["op"] == "or":
                return truth_value or verify_app_roles(roles[1:], user_roles)
            elif role_dict["op"] == "and":
                return truth_value and verify_app_roles(roles[1:], user_roles)
            else:
                raise UnknownOperatorError
        except IndexError:
            return truth_value
    return False


def cse_referrer_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.referrer and match(REQUEST_REF_RE, request.referrer):
                return f(*args, **kwargs)
            return abort(401)
        return decorated_function
    return decorator


def roles_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_roles = get_user_roles()
            sorted_roles = sorted(roles, key=lambda k: k["op"], reverse=True)

            if verify_app_roles(sorted_roles, user_roles):
                return f(*args, **kwargs)
            return abort(401)
        return decorated_function
    return decorator


def get_app_paths(base_dir):
    app_sub_directories = [f.path for f in scandir("{0}/apps".format(base_dir)) if f.is_dir()]

    for e in EXCLUDED_APPS:
        for i, sub_directory in enumerate(app_sub_directories):
            if e in sub_directory:
                app_sub_directories.pop(i)
                break

    return app_sub_directories


def remove_unused_uploads(base_dir, user_id):
    for app_path in get_app_paths(base_dir):
        user_upload_folder = "{0}/user_uploads/{1}".format(app_path, user_id)

        if path.isdir(user_upload_folder):
            user_uploads = [f.path for f in scandir(user_upload_folder) if f.is_dir()]

            for upload in user_uploads:
                if "submission.json" in [uploaded_file.name.strip() for uploaded_file in scandir(upload)]:
                    continue

                rmtree(upload, True)


def version_files(app_name_list=()):
    version_string_re = compile("[a-f0-9]{8}", IGNORECASE)

    for _app_name in app_name_list:
        css_files = [f.path for f in scandir("{0}/static/css/{1}/".format(APP_DIRECTORY, _app_name)) if f.is_file()]
        js_files = [f.path for f in scandir("{0}/static/js/{1}/".format(APP_DIRECTORY, _app_name)) if f.is_file()]

        for f in css_files + js_files:
            f_path_parts = f.split("/")
            f_parts = f_path_parts[-1].split(".")
            version_string_match = match(version_string_re, f_parts[-2])

            if len(f_parts) > 2 and not version_string_match:
                f_path_parts[-1] = "{0}.{1}.{2}".format(".".join(f_parts[:-1]), GIT_HASH, f_parts[-1])
            elif len(f_parts) > 2 and version_string_match:
                f_path_parts[-1] = "{0}.{1}.{2}".format(".".join(f_parts[:-2]), GIT_HASH, f_parts[-1])
            elif len(f_parts) == 2:
                f_path_parts[-1] = "{0}.{1}.{2}".format(f_parts[0], GIT_HASH, f_parts[1])
            else:
                postfix = "css" if "/static/css/" in f else "js"
                f_path_parts[-1] = "{0}.{1}.{2}".format(f_parts[0], GIT_HASH, postfix)

            try:
                rename(f, "/".join(f_path_parts))
            except OSError as e:
                pass


for app_name in [sub_dir.split("/")[-1] for sub_dir in get_app_paths(APP_DIRECTORY)]:
    APPS_LIST.append(" ".join(word for word in app_name.split("_")))
