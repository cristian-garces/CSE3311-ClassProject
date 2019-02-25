from os import path
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from flask_classful import FlaskView, route
from mavapps.constants import roles_required
# from apps.main.models import Messages


class MessagesApp(FlaskView):
    roles_list = [{"role": "DEV", "op": "or", "negated": False},
                  {"role": "SADM", "op": "or", "negated": False}]
    decorators = [login_required, roles_required(roles_list)]
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

    @route("/received/")
    def received_messages(self):
        per_page = request.args.get("per_page", 20, type=int)
        page = request.args.get("page", 0, type=int)

        user_messages = self.get_all_messages(True, False, page, per_page)

        return render_template("{0}/messages.html".format(self.__APP_DIR__), data=user_messages, endpoint="MessagesApp:received_messages")

    @route("/sent/")
    def sent_messages(self):
        per_page = request.args.get("per_page", 20, type=int)
        page = request.args.get("page", 0, type=int)

        user_messages = self.get_all_messages(False, True, page, per_page)

        return render_template("{0}/messages.html".format(self.__APP_DIR__), data=user_messages, endpoint="MessagesApp:sent_messages")

    @route("/send/", methods=["POST"])
    def send_messages(self):
        return render_template("{0}/index.html".format(self.__APP_DIR__), user_messages=self.get_all_messages())

    @route("/mark/read/", methods=["POST"])
    def read_message(self):
        return render_template("{0}/index.html".format(self.__APP_DIR__), user_messages=self.get_all_messages())

    @route("/mark/archived/", methods=["POST"])
    def archive_message(self):
        return render_template("{0}/index.html".format(self.__APP_DIR__), user_messages=self.get_all_messages())

    @route("/get/", methods=["GET"])
    def get_messages(self):
        return jsonify(self.serialize(self.get_all_messages()["messages"]))

    @route("/get/received/", methods=["GET"])
    def get_messages_received(self):
        return jsonify(self.serialize(self.get_all_messages(True, False)["messages"]))

    @route("/get/sent/", methods=["GET"])
    def get_messages_sent(self):
        return jsonify(self.serialize(self.get_all_messages(False, True)["messages"]))

    def get_all_messages(self, received=True, sent=True, page=0, per_page=20):
        if received and sent:
            messages = Messages.query.filter((current_user.net_id == Messages.recipient_net_id) | (current_user.net_id == Messages.sender_net_id)).order_by(Messages.timestamp.desc()).paginate(page, per_page, False)
        elif received and not sent:
            messages = Messages.query.filter(current_user.net_id == Messages.recipient_net_id).order_by(Messages.timestamp.desc()).paginate(page, per_page, False)
        elif not received and sent:
            messages = Messages.query.filter(current_user.net_id == Messages.sender_net_id).order_by(Messages.timestamp.desc()).paginate(page, per_page, False)
        else:
            raise ValueError("Invalid message retrieval request, please see function definition in MessagesApp.get_all_messages().")

        return {"messages": messages.items, "pagination": messages}

    def serialize(self, messages):
        return [{"message_id": message.id,
                 "sender_net_id": message.sender_net_id,
                 "recipient_net_id": message.recipient_net_id,
                 "title": message.title,
                 "body": message.body,
                 "timestamp": message.timestamp,
                 "is_new": message.is_new,
                 "is_archived": message.is_archived} for message in messages]

