from datetime import datetime
from base64 import b64encode
from flask import render_template, session
from flask_login import current_user, user_logged_out
from shared.constants import SETTINGS, APP_HOST, APP_PORT, SRV, URL_PREFIX, NO_PHOTO
from mavapps.constants import GIT_HASH, APPS_LIST, APP_ACCESS_ROLES, version_files, AUTO_VERSION_APPS, get_user_roles, verify_roles
from mavapps.apps.main.login_handler import app, login_daemon, logged_out
from mavapps.apps.main.models import db
# ############################################################################################
# ############################## Import Sub Applications Here ################################
# ############################################################################################
from mavapps.apps.api import api_app
# from apps.messages import messages_app
from mavapps.apps.reimbursement import reimbursement_app
from mavapps.apps.role_management import role_management_app
from mavapps.apps.cse_talks import cse_talks_app
# ############################################################################################
# ############################### Register Applications Here #################################
# ############################################################################################
api_app.APIApp.register(app)
# messages_app.MessagesApp.register(app)
reimbursement_app.ReimbursementApp.register(app)
role_management_app.RoleManagementApp.register(app)
cse_talks_app.CseTalksApp.register(app)
# ############################################################################################
# ############################################################################################
# ############################################################################################


@app.before_first_request
def prep_work():
    if SRV == "localhost":
        version_files(AUTO_VERSION_APPS)


@app.context_processor
def inject_usurper_base_id():
    return dict(usurper_roles=get_user_roles(session.get("usurper_base_id")))


@app.context_processor
def inject_git_hash():
    return dict(git_hash=GIT_HASH)


@app.context_processor
def inject_now():
    return dict(current_date=datetime.now())


@app.context_processor
def inject_user_photo():
    if current_user and current_user.photo:
        return dict(user_photo=b64encode(current_user.photo).decode("utf-8"))

    return dict(user_photo=NO_PHOTO)


@app.context_processor
def inject_user_roles():
    return dict(user_roles=get_user_roles())


@app.context_processor
def inject_current_apps():
    vetted_apps_list = []

    for app_name in APPS_LIST:
        canonical_app_name = "_".join(word for word in app_name.split(" "))
        try:
            if "ANY" in APP_ACCESS_ROLES[canonical_app_name] or verify_roles(APP_ACCESS_ROLES[canonical_app_name]):
                vetted_apps_list.append(app_name)
        except KeyError:
            print("Application access roles have not been set for {0}, please set them in constants.py.".format(canonical_app_name))

    return dict(user_apps=vetted_apps_list)


@app.context_processor
def inject_root_path():
    return dict(root_path="{0}/mavapps/".format(URL_PREFIX))


@app.context_processor
def inject_server():
    return dict(server=SRV)


# Bad request (400) error
@app.errorhandler(400)
def page_not_found(e):
    return '<p>Login failed, please try again.</p>'


# Unauthorized (401) error
@app.errorhandler(401)
def page_not_found(e):
    return '<p>Login before trying to access this resource.</p>'


# Forbidden (401) error
@app.errorhandler(403)
def page_not_found(e):
    return '<p>You don\'t have access to this resource.</p>'


# Not found (404) error
@app.errorhandler(404)
def page_not_found(e):
    return '<p>The specified resource was not found.</p>'


@app.route('/')
def index():
    return render_template("main/index.html")


app.secret_key = SETTINGS.get("mavapps_secret")

with app.app_context():
    login_daemon.init_app(app)
    user_logged_out.connect(logged_out, app)
    db.init_app(app)
    db.create_all()


if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, threaded=True, debug=True)
