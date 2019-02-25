from re import match, compile, IGNORECASE
from datetime import timedelta
from os import scandir, path, rename
from flask import Flask
from flask_login import login_manager
from alumni_directory.models import GuestUserLoginModel
from shared.constants import SETTINGS, SRV, CA_FILE, generate_version_file

APP_DIRECTORY = path.dirname(path.realpath(__file__))
GIT_HASH = generate_version_file(APP_DIRECTORY)

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
