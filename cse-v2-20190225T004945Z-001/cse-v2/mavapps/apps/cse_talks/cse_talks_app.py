from os import path
from flask import render_template, request, jsonify
from flask_login import login_required
from flask_classful import FlaskView, route
from mavapps.constants import roles_required
from mavapps.apps.main.models import db, Users, Students, UserRoles, Roles, Invited_Talks


class CseTalksApp(FlaskView):
    decorators = [login_required]
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

    @route('/get/data/')
    @route('/get/data/<query_filter>', methods=["GET"])
    def get_invited_talks_data(self, query_filter=None):
        """
        This method takes care of providing all the data that the datatables instance uses to populate the table.
        It returns the name of guests invited to give a talk

        :param query_filter: Filter to apply when retrieving talks from the database
        :return: A JSON response of all users that matched the filter with their associated data
        """
        def get_invited_talks_dict(talk):
            invited_talks_dict = {
                "f_name": talk.f_name,
                "l_name": talk.l_name
            }
            return invited_talks_dict

        invited_talks = self.filtered_query(query_filter)

        all_talks = []

        for i in invited_talks:
            all_talks.append(get_invited_talks_dict(i))
        return jsonify(all_talks)
    
    def filtered_query(self, query_filter=None):
        """
        This method takes care of returning the correct list of users based on what filter criteria was selected.

        :param query_filter: Filter criteria selected by the user in the front-end
        :return: List of users returned from the database matching the specified filter
        """
        if not query_filter or query_filter == "all talks":
            return db.session.query(Invited_Talks.f_name, Invited_Talks.l_name)
        
        #else:
            #return []

        
