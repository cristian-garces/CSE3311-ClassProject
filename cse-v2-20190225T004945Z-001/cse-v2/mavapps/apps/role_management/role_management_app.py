from os import path
from flask import render_template, request, jsonify
from flask_login import login_required
from flask_classful import FlaskView, route
from mavapps.constants import roles_required
from mavapps.apps.main.models import db, Users, Students, UserRoles, Roles


class RoleManagementApp(FlaskView):
    roles_list = [{"role": "DEV", "op": "or", "negated": False},
                  {"role": "SADM", "op": "or", "negated": False}]
    decorators = [login_required, roles_required(roles_list)]
    excluded_methods = ["filtered_query"]
    route_base = "/{0}/".format(path.dirname(path.realpath(__file__)).split("/")[-1])

    def __init__(self):
        """
        Initializes the app instance and sets the app path and app directory for later use.
        """
        self.__APP_PATH__ = path.dirname(path.realpath(__file__))
        self.__APP_DIR__ = self.__APP_PATH__.split("/")[-1]

    def index(self):
        """
        Renders the index page of the app.

        :return: Rendered index.html for the application
        """
        return render_template("{0}/index.html".format(self.__APP_DIR__))

    def post(self):
        """
        This method takes care of executing role changes and committing them to the database.

        :return: A JSON response specifying whether the action was successful or not
        """
        role_changes = request.json

        for k in role_changes:
            role_change = role_changes[k]

            if role_change["action"] == "add":
                db.session.add(UserRoles(role_change["net_id"], role_change["role"]))
                db.session.commit()
            elif role_change["action"] == "delete":
                UserRoles.query.filter((UserRoles.net_id == role_change["net_id"]) & (UserRoles.role == role_change["role"])).delete()
                db.session.commit()
            else:
                pass

        return jsonify({"type": "success", "message": "Role changes applied successfully."})

    @route('/get/data')
    @route('/get/data/<query_filter>', methods=["GET"])
    def get_user_data(self, query_filter=None):
        """
        This method takes care of providing all the data that the datatables instance uses to populate the table.
        It returns the name, NetID, and roles for a user with the roles being a list of all roles as a key and a value
        of True if the user has a particular role.

        :param query_filter: Filter to apply when retrieving users from the database
        :return: A JSON response of all users that matched the filter with their associated data
        """
        def get_user_dict(user):
            user_dict = {
                "name": "{0} {1}".format(user.first_name, user.last_name),
                "net_id": user.net_id
            }
            user_dict.update(dict(all_roles))

            for user_role in user.roles.split(","):
                user_dict[user_role] = True

            return user_dict

        users = self.filtered_query(query_filter)

        all_users = []
        all_roles = {row.role.strip(): False for row in Roles.query.all()}

        for u in users:
            all_users.append(get_user_dict(u))

        return jsonify(all_users)

    def filtered_query(self, query_filter=None):
        """
        This method takes care of returning the correct list of users based on what filter criteria was selected.

        :param query_filter: Filter criteria selected by the user in the front-end
        :return: List of users returned from the database matching the specified filter
        """
        if not query_filter or query_filter == "all users":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Users.is_active == 1)).group_by(Users.net_id)
        elif query_filter == "staff":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Users.is_active == 1)).group_by(Users.net_id).having(db.func.group_concat(UserRoles.role).like("%STF%"))
        elif query_filter == "faculty":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Users.is_active == 1)).group_by(Users.net_id).having(db.func.group_concat(UserRoles.role).like("%FAC%"))
        elif query_filter == "tenure track":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Users.is_active == 1)).group_by(Users.net_id).having(db.func.group_concat(UserRoles.role).like("%FTT%"))
        elif query_filter == "students":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Students.net_id == Users.net_id) & (Users.is_active == 1)).group_by(Users.net_id)
        elif query_filter == "undergrads":
            return db.session.query(Users.first_name, Users.last_name, Users.net_id, db.func.group_concat(UserRoles.role).label("roles")).filter((UserRoles.net_id == Users.net_id) & (Students.net_id == Users.net_id) & (Students.degree == "UGRD") & (Users.is_active == 1)).group_by(Users.net_id)
        else:
            return []
