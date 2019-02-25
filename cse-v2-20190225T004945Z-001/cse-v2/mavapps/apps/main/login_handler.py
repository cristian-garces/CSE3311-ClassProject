from shared.loggers import LoginLogger
from flask import request, flash, render_template, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from shared.constants import SETTINGS, is_safe_url, get_log_time
from mavapps.constants import remove_unused_uploads, APP_DIRECTORY, get_user_roles, login_daemon, app
from mavapps.apps.main.ldap_auth import LDAPAuth
from mavapps.apps.main.models import db, UserLoginModel


def logged_out(sender, user):
    remove_unused_uploads(APP_DIRECTORY, user.net_id)


@login_daemon.user_loader
def load_user(net_id):
    return UserLoginModel.query.get(net_id)


@app.route('/usurp/<net_id>')
def usurp_user(net_id=None):
    current_user_roles = get_user_roles(session["usurper_base_id"])

    if current_user.is_authenticated and (current_user_roles["DEV"] or current_user_roles["SADM"]):
        new_user = UserLoginModel.query.get(net_id)

        if new_user:
            user = current_user
            user.is_authenticated = False
            db.session.commit()
            logout_user()

            if login_user(new_user):
                user.is_authenticated = True
                db.session.commit()

                flash("Successfully usurped user {0}.".format(net_id), "success")
                return redirect(url_for('index'))

    flash("Attempt to usurp {0} failed. Check the NetID and try again.".format(net_id), "error")
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            return_url = request.json['next']
            username = request.json['netid'].strip()
            password = request.json['password']
            user = UserLoginModel.query.get(username)
            ldap_auth = LDAPAuth(SETTINGS.get("ldap_server"), SETTINGS.get("ldap_base_dn"),
                                 SETTINGS.get("ldap_user_dn"), username, password)

            if ldap_auth.authenticate() and is_safe_url(return_url) and user and user.is_active:
                if login_user(user):
                    session.permanent = True
                    time, zone = get_log_time()
                    LoginLogger("\nUser: {0}\n\tLogin Time:\t\t{1} (Time zone: {2})\n".format(username, time, zone),
                                "{0}/logs/".format(APP_DIRECTORY)).start()
                    remove_unused_uploads(APP_DIRECTORY, user.net_id)

                    current_user_roles = get_user_roles(user.net_id)
                    if current_user_roles["DEV"] or current_user_roles["SADM"]:
                        session["usurper_base_id"] = user.net_id

                    user.is_authenticated = True
                    db.session.commit()

                    flash("Logged in successfully.", "success")

                    return jsonify({"error": False, "return_url": return_url})
        except Exception as e:
            print(e)

        return jsonify({"error": True, "type": "error", "message": "Login failed, please try again."})

    return render_template("main/login.html")


@app.route('/logout', methods=["POST"])
@login_required
def logout():
    if request.json['logout']:
        session["usurper_base_id"] = None
        user = current_user
        time, zone = get_log_time()
        LoginLogger("\nUser: {0}\n\tLogout Time:\t{1} (Time zone: {2})\n".format(user.net_id, time, zone),
                    "{0}/logs/".format(APP_DIRECTORY)).start()
        user.is_authenticated = False
        db.session.commit()
        logout_user()

        flash("Logged out successfully.", "success")

        return jsonify({"success": True})


@app.route("/ping", methods=['POST'])
def ping():
    if current_user.is_authenticated:
        session.modified = True
        return "pong"
    return "logged_out"
