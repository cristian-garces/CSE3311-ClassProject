from datetime import datetime
from shared.constants import SETTINGS, APP_HOST, APP_PORT, SRV, URL_PREFIX
from alumni_directory.constants import app, GIT_HASH, version_files
from alumni_directory.models import db
# ############################################################################################
# ############################## Import Sub Applications Here ################################
# ############################################################################################
from alumni_directory import alumni_directory
# ############################################################################################
# ############################### Register Applications Here #################################
# ############################################################################################
alumni_directory.AlumniDirectoryApp.register(app)
# ############################################################################################
# ############################################################################################
# ############################################################################################


@app.before_first_request
def prep_work():
    if SRV == "localhost":
        pass
        # version_files()


@app.context_processor
def inject_git_hash():
    return dict(git_hash=GIT_HASH)


@app.context_processor
def inject_now():
    return dict(current_date=datetime.now())


@app.context_processor
def inject_root_path():
    return dict(root_path="{0}/alumni_directory/".format(URL_PREFIX))


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


app.secret_key = SETTINGS.get("alumni_directory_secret")

with app.app_context():
    db.init_app(app)
    db.create_all()


if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, threaded=True, debug=True)
