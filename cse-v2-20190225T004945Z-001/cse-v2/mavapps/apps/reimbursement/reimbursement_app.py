import json
import mavapps.apps.reimbursement.app_constants as app_constants
from fuzzywuzzy import fuzz
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
from os import path, remove, scandir, listdir
from shutil import rmtree
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, flash, send_from_directory, abort
from flask_classful import FlaskView, route
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from shared.constants import allowed_file, str_2_bool, pikaday_to_datetime, paginate_it, URL_FULL_PATH, SRV
from mavapps.constants import get_user_roles, roles_required
from mavapps.apps.main.models import Users, UserRoles, PIAccounts
from shared.mailer import Mailer
from shared.pdf_maker import PDFMaker


class ReimbursementApp(FlaskView):
    roles_list = [{"role": "DEV", "op": "or", "negated": False},
                  {"role": "SADM", "op": "or", "negated": False},
                  {"role": "FAC", "op": "or", "negated": False},
                  {"role": "FINANCE", "op": "or", "negated": False}]
    default_methods = ['GET', 'POST', 'PUT', 'DELETE']
    decorators = [login_required, roles_required(roles_list)]
    excluded_methods = ["get_uploads", "make_pdf"]
    route_base = "/{0}/".format(path.dirname(path.realpath(__file__)).split("/")[-1])

    def __init__(self):
        """
        Initializes the app instance and sets the app path, app directory, allowed extensions, as well as some e-mail
        lists to be used in different development environments for later use. The mailer is also initialized here and
        reused throughout the app when e-mails need to be sent.
        """
        self.__ALLOWED_EXTENSIONS__ = {"txt", "doc", "docx", "xls", "xlsx", "pdf", "png", "jpg", "jpeg", "gif", "zip"}
        self.__APP_PATH__ = path.dirname(path.realpath(__file__))
        self.__APP_DIR__ = self.__APP_PATH__.split("/")[-1]
        self.__SPECIAL_FILES__ = ["request.saved", "request.submitted", "request.processed", "request.returned", "request.voided", "submission.json"]
        self.__TEST_EMAILS__ = [["Damian Jimenez", "jimenez.dmn@gmail.com"]]
        self.__PROD_EMAILS__ = [["CSE Webmaster", "webmaster-cse@uta.edu"], ["Chengkai Li", "cli@uta.edu"]]
        self.mailer = Mailer()

    def index(self):
        """
        Renders the index page of the app.

        :return: Rendered index.html for the application
        """
        return render_template("{0}/index.html".format(self.__APP_DIR__))

    @route('/new/request/')
    def new(self):
        """
        Renders the new requests page for the app. The template gets passed a list of accounts that are at least within
        two years of the end-date listed in the database or accounts with no end-date.

        :return: Rendered new_request.html for the application
        """
        valid_accounts = [acc for acc in PIAccounts.query.filter((PIAccounts.net_id == current_user.net_id) & (((datetime.now() - timedelta(days=2*365)) < PIAccounts.end_date) | (PIAccounts.end_date.is_(None)))).with_entities(PIAccounts.end_date, PIAccounts.account_number, PIAccounts.description)]

        return render_template("{0}/new_request.html".format(self.__APP_DIR__), user_accounts=valid_accounts)

    @route("/edit/request/")
    def edit(self):
        """
        Renders the edit requests page for the app. The template gets passed a list of accounts that are at least within
        two years of the end-date listed in the database or accounts with no end-date, the request details which is
        loaded from the submission.json of the request, whether the request has been saved, and whether the request
        has been returned. The last two help determine if the edit request is a valid one, as only saved or returned
        requests can be edited.

        :return: Rendered edit_request.html for the application
        """
        current_user_roles = get_user_roles()

        if current_user_roles["STFADM"] or request.args.get("user_id", None) == current_user.net_id:
            folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, request.args.get("user_id", None), request.args.get("request_id", None))

            with open("{0}submission.json".format(folder_path), mode="r") as request_json:
                request_details = json.load(request_json)

            request_saved = path.exists("{0}/request.saved".format(folder_path))
            request_returned = path.exists("{0}/request.returned".format(folder_path))

            if request_saved or request_returned:
                valid_accounts = [acc for acc in PIAccounts.query.filter((PIAccounts.net_id == current_user.net_id) & (((datetime.now() - timedelta(days=2*365)) < PIAccounts.end_date) | (PIAccounts.end_date.is_(None)))).with_entities(PIAccounts.end_date, PIAccounts.account_number, PIAccounts.description)]

                return render_template("{0}/edit_request.html".format(self.__APP_DIR__), user_accounts=valid_accounts, request_details=request_details, request_saved=request_saved, request_returned=request_returned)
        return abort(403)

    @route('/view/requests/')
    @route('/view/<int:index>/')
    def view_requests(self, index=0):
        """
        Renders the view requests page for the app. The function takes a parameter, index, which specifies the current
        index for the list of requests that is used in paginating requests. The template gets passed all uploads that
        are relevant for the current user, and pagination details.

        :param index: The current index to use as an offset for the list of uploads returned
        :return: Rendered view_requests.html for the app
        """
        all_uploads = self.get_uploads()
        num_to_display = 10

        return render_template("{0}/view_requests.html".format(self.__APP_DIR__),
                               uploads=all_uploads[index: num_to_display + index],
                               pagination=paginate_it(current_index=index, num_to_display=num_to_display, num_items=len(all_uploads)))

    @route('/view/requests/search')
    def search_requests(self):
        """
        Renders the search page for requests for the app. The template gets passed all the uploads that matched the
        applied filters and whether uploads were available to display had no filters been applied. The latter is used
        to help determine whether to display search controls, if no requests are present then there is no point in
        displaying the search controls at all.

        :return: Rendered view_requests_search.html for the app
        """
        query = request.args.get("query", None) if request.args.get("query", None) != "" else None
        sort_by = request.args.get("sort-by", None) if request.args.get("sort-by", None) else "date"
        sort_direction = True if request.args.get("sort-direction", None) == "descending" else False

        all_uploads = self.get_uploads(
            query, sort_by, sort_direction,
            request.args.get("request-type-list", "").split(",") if request.args.get("request-type-list", "") else None,
            request.args.get("status-filter-list", "").split(",") if request.args.get("status-filter-list", "") else None,
            pikaday_to_datetime(request.args.get("after-date-filter", None)),
            pikaday_to_datetime(request.args.get("before-date-filter", None)),
            float(request.args.get("ge-amount-filter", None)) if request.args.get("ge-amount-filter", None) else None,
            float(request.args.get("le-amount-filter", None)) if request.args.get("le-amount-filter", None) else None
        )

        return render_template("{0}/view_requests_search.html".format(self.__APP_DIR__), uploads=all_uploads, uploads_available=self.uploads_present())

    @route('/download/<net_id>/<request_id>/<request_date>')
    def download(self, net_id, request_id, request_date):
        """
        Returns a request zip containing the submission files and PDf summary of the request.

        :param net_id: The NetID of the user the request belongs to
        :param request_id: The request id to help identify which request should be sent back
        :param request_date: The request date to include in the zip name
        :return: The zipped request including the request files and a PDF summary as a blob
        """
        current_user_roles = get_user_roles()

        if current_user_roles["STFADM"] or net_id == current_user.net_id:
            if self.make_pdf(net_id, request_id, request_date):
                try:
                    with ZipFile("{0}/user_uploads/{1}/{2}/[{1}-{3}]_request.zip".format(self.__APP_PATH__, net_id, request_id, request_date), mode="w") as zip_archive:
                        for user_file in scandir("{0}/user_uploads/{1}/{2}".format(self.__APP_PATH__, net_id, request_id)):
                            if "_request.zip" not in user_file.name and user_file.name not in self.__SPECIAL_FILES__:
                                zip_archive.write(user_file.path, user_file.name, ZIP_DEFLATED)

                    return send_from_directory("{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, net_id, request_id),
                                               "[{0}-{1}]_request.zip".format(net_id, request_date), mimetype="blob")
                except Exception as e:
                    print(e)
            return abort(404)
        return abort(403)

    @route("/download/pdf/<net_id>/<request_id>/<request_date>")
    def download_pdf(self, net_id, request_id, request_date):
        """
        Returns a the PDF summary of the request.

        :param net_id: The NetID of the user the request belongs to
        :param request_id: The request id to help identify which request the PDf should be generated for
        :param request_date: The request date to include in the PDF name
        :return: The PDF summary of the request as a blob
        """
        current_user_roles = get_user_roles()
        if current_user_roles["STFADM"] or net_id == current_user.net_id:
            if self.make_pdf(net_id, request_id, request_date):
                return send_from_directory("{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, net_id, request_id),
                                           "[{0}-{1}]_report.pdf".format(net_id, request_date), mimetype="blob")

            return abort(404)
        return abort(403)

    @route("/download/file/<net_id>/<request_id>/<file_name>")
    def download_file(self, net_id, request_id, file_name):
        """
        Returns a specific file from a request.

        :param net_id: The NetID of the user the request belongs to
        :param request_id: The request id to help identify which request the file is found in
        :param file_name: The file name of the desired file
        :return: The requested file as a blob
        """
        current_user_roles = get_user_roles()
        if current_user_roles["STFADM"] or net_id == current_user.net_id:
            try:
                return send_from_directory("{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, net_id, request_id),
                                           "{0}".format(secure_filename(file_name)), mimetype="blob")
            except Exception as e:
                print(e)
                return abort(404)
        return abort(403)

    @route('/process/<net_id>/<request_id>/<processed>', methods=["POST"])
    def process_request(self, net_id, request_id, processed):
        """
        Marks a request as processed/unprocessed by adding/removing a file named "request.processed" in the request
        directory. Apart from this the request history is updated to reflect who processed/unprocessed the request.
        This only occurs if no other request markers are present in the request directory. If successful an e-mail is
        sent out to all party's associated with the request as well as the CSE Webmaster.

        :param net_id: The NetID of the user the request belongs to
        :param request_id: The request id to help identify which request is being processed
        :param processed: Whether the request is being processed (true) or unprocessed (false)
        :return: A JSON response specifying whether the action was successful or not
        """
        folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, net_id, request_id)
        request_submitted_marker = "{0}request.submitted".format(folder_path)
        request_processed_marker = "{0}request.processed".format(folder_path)
        request_returned_marker = "{0}request.returned".format(folder_path)
        request_voided_marker = "{0}request.voided".format(folder_path)
        request_submitted = path.exists(request_submitted_marker)

        if get_user_roles(current_user.net_id)["STFADM"] and ((request_submitted and str_2_bool(processed)) or (not request_submitted and not str_2_bool(processed))):
            date_time = "{0}".format(datetime.now()).split()

            if path.exists(request_voided_marker):
                return jsonify({"success": False, "type": "error", "message": "This request has been voided. Please refresh the page."})
            elif path.exists(request_returned_marker):
                return jsonify({"success": False, "type": "error", "message": "This request has been returned. Please refresh the page."})
            elif path.exists(request_processed_marker) and str_2_bool(processed):
                return jsonify({"success": False, "type": "error", "message": "This request has already been processed. Please refresh the page."})
            elif not path.exists(request_processed_marker) and not str_2_bool(processed):
                return jsonify({"success": False, "type": "error", "message": "This request has already been unprocessed. Please refresh the page."})

            with open("{0}submission.json".format(folder_path), mode="r") as request_details_json:
                request_details = json.load(request_details_json)

            try:
                request_date = "{0:02d}/{1:02d}/{2:04d}".format(request_details["request_date"]["month"],
                                                                request_details["request_date"]["day"],
                                                                request_details["request_date"]["year"])

                history_update = {
                    "date": date_time[0],
                    "time": date_time[1],
                    "action": None,
                    "actor": {
                        "first_name": current_user.first_name,
                        "last_name": current_user.last_name,
                        "email": current_user.email,
                        "uta_id": current_user.uta_id
                    },
                    "metadata": None
                }

                processed = str_2_bool(processed)
                if processed:
                    remove(request_submitted_marker)
                    optional_message = request.json.get("message", "").strip()
                    history_update["action"] = "Processed"
                    history_update["metadata"] = {
                        "transaction_number": request.json["transaction_number"],
                        "message": optional_message
                    }

                    with open(request_processed_marker, mode="w") as processed_marker:
                        processed_marker.write("/n")

                    if optional_message:
                        optional_message_html = "<br><br>Please see the attached message from {0} below:" \
                                                "<br><blockquote style='border-left: 3px solid rgb(200, 200, 200); " \
                                                "border-top-color: rgb(200, 200, 200); border-right-color: " \
                                                "rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); " \
                                                "padding-left: 1ex; margin-left: 0.8ex; color: rgb(102, 102, 102);'>" \
                                                "<div style='color: rgb(0, 0, 0);'>{1}</div>" \
                                                "</blockquote>".format(current_user.first_name, optional_message)
                        optional_message = "\n\nPlease see the attached message from {0} below:" \
                                           "\n{1}".format(current_user.first_name, optional_message)
                    else:
                        optional_message_html = ""

                    email_subject = "Reimbursement Request Processed"
                    requester_payto_equal = request_details["requester"]["email"].lower().strip() == request_details["pay_to"]["email"].lower().strip()

                    if requester_payto_equal:
                        email_body = app_constants.EMAILS["process_request"]["text"][processed][requester_payto_equal].format(
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            request_date, request_details["total_amount"],
                            current_user.first_name, current_user.email,
                            request.json["transaction_number"],
                            optional_message, request_details["short_description"],
                            request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                        email_body_html = app_constants.EMAILS["process_request"]["html"][processed][requester_payto_equal].format(
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            request_date, request_details["total_amount"],
                            current_user.first_name, current_user.email,
                            request.json["transaction_number"],
                            optional_message_html, request_details["short_description"],
                            request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                    else:
                        email_body = app_constants.EMAILS["process_request"]["text"][processed][requester_payto_equal].format(
                            request_details["pay_to"]["name"],
                            request_date, request_details["total_amount"],
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            current_user.first_name, current_user.email,
                            request.json["transaction_number"],
                            optional_message, request_details["short_description"],
                            request_details["requester"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                        email_body_html = app_constants.EMAILS["process_request"]["html"][processed][requester_payto_equal].format(
                            request_details["pay_to"]["name"],
                            request_date, request_details["total_amount"],
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            current_user.first_name, current_user.email,
                            request.json["transaction_number"],
                            optional_message_html, request_details["short_description"],
                            request_details["requester"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))

                    return_payload = {"success": True, "type": "success", "message": "File marked as processed."}
                else:
                    with open(request_submitted_marker, mode="w") as submitted_marker:
                        submitted_marker.write("/n")

                    user_message = request.json["message"]
                    history_update["action"] = "Unprocessed"
                    history_update["metadata"] = {
                        "message": user_message
                    }

                    email_subject = "Reimbursement Request Unprocessed"
                    requester_payto_equal = request_details["requester"]["email"].lower().strip() == request_details["pay_to"]["email"].lower().strip()

                    if requester_payto_equal:
                        email_body = app_constants.EMAILS["process_request"]["text"][processed][requester_payto_equal].format(
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            request_date, request_details["total_amount"],
                            current_user.first_name, current_user.email,
                            user_message, request_details["short_description"],
                            request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                        email_body_html = app_constants.EMAILS["process_request"]["html"][processed][requester_payto_equal].format(
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            request_date, request_details["total_amount"],
                            current_user.first_name, current_user.email,
                            user_message, request_details["short_description"],
                            request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                    else:
                        email_body = app_constants.EMAILS["process_request"]["text"][processed][requester_payto_equal].format(
                            request_details["pay_to"]["name"],
                            request_date, request_details["total_amount"],
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            current_user.first_name, current_user.email,
                            user_message, request_details["short_description"],
                            request_details["requester"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))
                        email_body_html = app_constants.EMAILS["process_request"]["html"][processed][requester_payto_equal].format(
                            request_details["pay_to"]["name"],
                            request_date, request_details["total_amount"],
                            request_details["requester"]["first_name"],
                            request_details["requester"]["last_name"],
                            current_user.first_name, current_user.email,
                            user_message, request_details["short_description"],
                            request_details["requester"]["email"],
                            "{0}mavapps/".format(URL_FULL_PATH))

                    if path.exists(request_processed_marker):
                        remove(request_processed_marker)

                    return_payload = {"success": True, "type": "success", "message": "File marked as unprocessed."}

                with open("{0}submission.json".format(folder_path), mode="w") as request_details_json:
                    request_details["history"].append(history_update)
                    json.dump(request_details, request_details_json)

                if SRV != "prod":
                    emails = self.__TEST_EMAILS__
                else:
                    emails = [["{0} {1}".format(current_user.first_name, current_user.last_name), current_user.email],
                              ["{0} {1}".format(request_details["requester"]["first_name"], request_details["requester"]["last_name"]), request_details["requester"]["email"]]] \
                             + self.__PROD_EMAILS__
                    if not requester_payto_equal:
                        emails.append(["{0}".format(request_details["pay_to"]["name"]), request_details["pay_to"]["email"]])

                self.mailer.send_mail(emails, email_subject, email_body, email_body_html, from_name="CSE Reimbursement App")

                return jsonify(return_payload)

            except Exception as e:
                print(e)

            return jsonify({"success": False, "type": "error", "message": "Oops! Something went wrong, contact the "
                                                                          "administrator if the problem persists."})
        return abort(403)

    @route('/void/request/', methods=["POST"])
    def void_request(self):
        """
        Marks a request as voided by adding a file named "request.voided" in the request
        directory. Apart from this the request history is updated to reflect who voided the request.
        This only occurs if the request is currently unprocessed. If successful an e-mail is sent out
        to all party's associated with the request as well as the CSE Webmaster.

        :return: A JSON response specifying whether the action was successful or not
        """
        try:
            accountant_emails = [["{0} {1}".format(accountant[0], accountant[1]), accountant[2]] for accountant in Users.query.with_entities(Users.first_name, Users.last_name, Users.email).join(Users.user_roles).filter((UserRoles.role == "STFADM") & (Users.net_id == "sherrift")).all()]
            folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, request.json["net_id"], request.json["request_id"])
            request_submitted_marker = "{0}request.submitted".format(folder_path)
            request_processed_marker = "{0}request.processed".format(folder_path)
            request_returned_marker = "{0}request.returned".format(folder_path)
            request_voided_marker = "{0}request.voided".format(folder_path)

            void_message = request.json["return_message"].strip()

            if path.exists(request_voided_marker):
                return jsonify({"success": False, "type": "error", "message": "This request has already been voided. Please refresh the page."})

            if path.exists(request_processed_marker):
                if not get_user_roles(current_user.net_id)["STFADM"]:
                    return jsonify({"success": False, "type": "error", "message": "Processed requests cannot be voided by the requester."})
                else:
                    remove(request_processed_marker)

            if path.exists(request_submitted_marker):
                if not get_user_roles(current_user.net_id)["STFADM"]:
                    return jsonify({"success": False, "type": "error", "message": "Submitted requests cannot be voided by the requester."})
                else:
                    remove(request_submitted_marker)

            if path.exists(request_returned_marker):
                remove(request_returned_marker)

            with open("{0}submission.json".format(folder_path), mode="r") as request_details_json:
                request_details = json.load(request_details_json)

            with open("{0}submission.json".format(folder_path), mode="w") as request_details_json:
                date_time = "{0}".format(datetime.now()).split()

                request_details["history"].append({"date": date_time[0],
                                                   "time": date_time[1],
                                                   "action": "Voided",
                                                   "actor": {
                                                       "first_name": current_user.first_name,
                                                       "last_name": current_user.last_name,
                                                       "email": current_user.email,
                                                       "uta_id": current_user.uta_id
                                                   },
                                                   "metadata": {
                                                       "message": void_message
                                                   }})
                json.dump(request_details, request_details_json)

            with open(request_voided_marker, mode="w") as voided_marker:
                voided_marker.write("/n")

            if void_message:
                void_message_html = "<br><br>Message from {0}:<br>" \
                                    "<blockquote style='border-left: 3px solid rgb(200, 200, 200); " \
                                    "border-top-color: rgb(200, 200, 200); border-right-color: " \
                                    "rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); padding-left: 1ex; " \
                                    "margin-left: 0.8ex; color: rgb(102, 102, 102);'>" \
                                    "<div style='color: rgb(0, 0, 0);'>{1}</div>" \
                                    "</blockquote>".format(current_user.first_name, void_message)
                void_message = "\n\nMessage from {0}:\n{1}".format(current_user.first_name, void_message)
            else:
                void_message_html = ""

            request_date = "{0:02d}/{1:02d}/{2:04d}".format(request_details["request_date"]["month"],
                                                            request_details["request_date"]["day"],
                                                            request_details["request_date"]["year"])

            email_subject = "Reimbursement Request Voided"
            email_body = app_constants.EMAILS["void_request"]["text"].format(
                request_date,
                request_details["requester"]["first_name"],
                request_details["requester"]["last_name"],
                void_message, request_details["short_description"],
                request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                request_details["total_amount"], "{0}mavapps/".format(URL_FULL_PATH))
            email_body_html = app_constants.EMAILS["void_request"]["html"].format(
                request_date,
                request_details["requester"]["first_name"],
                request_details["requester"]["last_name"],
                void_message_html, request_details["short_description"],
                request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                request_details["total_amount"], "{0}mavapps/".format(URL_FULL_PATH))

            if SRV != "prod":
                emails = self.__TEST_EMAILS__
            else:
                emails = [["{0} {1}".format(request_details["requester"]["first_name"], request_details["requester"]["last_name"]), request_details["requester"]["email"]]] \
                         + accountant_emails + self.__PROD_EMAILS__

            self.mailer.send_mail(emails, email_subject, email_body, email_body_html, from_name="CSE Reimbursement App")

            return jsonify({"success": True, "type": "success", "message": "Request voided successfully."})
        except Exception as e:
            print(e)
            return abort(400)

    @route('/return/request/', methods=["POST"])
    def return_request(self):
        """
        Marks a request as returned by adding a file named "request.returned" in the request
        directory. Apart from this the request history is updated to reflect who returned the request.
        This only occurs if the request has not been voided. If successful an e-mail is sent out
        to all party's associated with the request as well as the CSE Webmaster.

        :return: A JSON response specifying whether the action was successful or not
        """
        folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, request.json["net_id"], request.json["request_id"])
        request_submitted_marker = "{0}request.submitted".format(folder_path)
        request_processed_marker = "{0}request.processed".format(folder_path)
        request_returned_marker = "{0}request.returned".format(folder_path)
        request_voided_marker = "{0}request.voided".format(folder_path)

        if get_user_roles(current_user.net_id)["STFADM"] and path.exists(request_submitted_marker):
            try:
                return_message = request.json["return_message"].strip()

                if path.exists(request_processed_marker):
                    return jsonify({"success": False, "type": "error", "message": "You must unprocess a request before returning it."})
                elif path.exists(request_voided_marker):
                    return jsonify({"success": False, "type": "error", "message": "This request has already been voided. Please refresh the page."})
                elif path.exists(request_returned_marker):
                    return jsonify({"success": False, "type": "error", "message": "This request has already been returned. Please refresh the page."})

                with open("{0}submission.json".format(folder_path), mode="r") as request_details_json:
                    request_details = json.load(request_details_json)

                with open("{0}submission.json".format(folder_path), mode="w") as request_details_json:
                    date_time = "{0}".format(datetime.now()).split()

                    request_details["history"].append({"date": date_time[0],
                                                       "time": date_time[1],
                                                       "action": "Returned",
                                                       "actor": {
                                                           "first_name": current_user.first_name,
                                                           "last_name": current_user.last_name,
                                                           "email": current_user.email,
                                                           "uta_id": current_user.uta_id
                                                       },
                                                       "metadata": {
                                                           "message": return_message
                                                       }})
                    json.dump(request_details, request_details_json)

                with open(request_returned_marker, mode="w") as returned_marker:
                    returned_marker.write("/n")

                if return_message:
                    return_message_html = "<br><br>Message from {0}:<br>" \
                                          "<blockquote style='border-left: 3px solid rgb(200, 200, 200); " \
                                          "border-top-color: rgb(200, 200, 200); border-right-color: " \
                                          "rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); " \
                                          "padding-left: 1ex; margin-left: 0.8ex; color: rgb(102, 102, 102);'>" \
                                          "<div style='color: rgb(0, 0, 0);'>{1}</div>" \
                                          "</blockquote>".format(current_user.first_name, return_message)
                    return_message = "\n\nMessage from {0}:\n{1}".format(current_user.first_name, return_message)
                else:
                    return_message_html = ""

                request_date = "{0:02d}/{1:02d}/{2:04d}".format(request_details["request_date"]["month"],
                                                                request_details["request_date"]["day"],
                                                                request_details["request_date"]["year"])
                email_subject = "Reimbursement Request Returned"
                email_body = app_constants.EMAILS["return_request"]["text"].format(
                    request_details["requester"]["first_name"],
                    request_details["requester"]["last_name"],
                    request_date, request_details["total_amount"],
                    "{0}mavapps/".format(URL_FULL_PATH), request_details["requester"]["net_id"],
                    request_details["folder_name"], return_message,
                    request_details["short_description"],
                    request_details["pay_to"]["name"], request_details["pay_to"]["email"])
                email_body_html = app_constants.EMAILS["return_request"]["html"].format(
                    request_details["requester"]["first_name"],
                    request_details["requester"]["last_name"],
                    request_date, request_details["total_amount"],
                    "{0}mavapps/".format(URL_FULL_PATH), request_details["requester"]["net_id"],
                    request_details["folder_name"], return_message_html,
                    request_details["short_description"],
                    request_details["pay_to"]["name"], request_details["pay_to"]["email"])

                if SRV != "prod":
                    emails = self.__TEST_EMAILS__
                else:
                    emails = [["{0} {1}".format(current_user.first_name, current_user.last_name), current_user.email],
                              ["{0} {1}".format(request_details["requester"]["first_name"], request_details["requester"]["last_name"]), request_details["requester"]["email"]]] \
                             + self.__PROD_EMAILS__

                self.mailer.send_mail(emails, email_subject, email_body, email_body_html, from_name="CSE Reimbursement App")

                remove(request_submitted_marker)

                return jsonify({"success": True, "type": "success", "message": "Request returned to the user successfully."})
            except Exception as e:
                print(e)
                return abort(400)
        return abort(403)

    def post(self):
        """
        This method takes care of accepting files uploaded to a request through the new/request/ or edit/request/
        pages. It makes sure the file names are secure then returns a response with the secure file name to store in
        the submission.json. Only files with an extension that matches one in __ALLOWED_EXTENSIONS__ is able to be
        uploaded.

        :return: A JSON response specifying whether the action was successful or not, if it was this response includes
        the secure file name version of the original file name.
        """
        folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, current_user.net_id, request.headers["folder_name"])

        request_submitted = path.exists("{0}request.submitted".format(folder_path))
        request_processed = path.exists("{0}request.processed".format(folder_path))
        request_voided = path.exists("{0}request.voided".format(folder_path))

        if not request_submitted and not request_processed and not request_voided:
            if 'file' not in request.files or "folder_name" not in request.headers:
                return jsonify({"success": False, "type": "error", "message": "Invalid request format."})

            file = request.files['file']

            if file and allowed_file(file.filename, self.__ALLOWED_EXTENSIONS__):
                try:
                    Path(folder_path).mkdir(parents=True, exist_ok=True)
                    filename = secure_filename(file.filename)
                    file.save(path.join(folder_path, filename))

                    return jsonify({"success": True, "type": "success", "message": "File successfully uploaded.", "filename": filename})
                except Exception as e:
                    print(e)

                    return jsonify({"success": False, "type": "error", "message": "An error occurred while saving the file."})

            return jsonify({"success": False, "type": "error", "message": "Invalid file or file extension."})
        return jsonify({"success": False, "type": "error", "message": "Status of the request has changed."})

    def delete(self):
        """
        This method takes care of deleting a file or request based on the delete_request argument passed in the JSON.

        :return: A JSON response specifying whether the action was successful or not
        """
        try:
            flash_message = request.json["flash_message"]
            folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, current_user.net_id, request.json["folder_name"])
            request_submitted = path.exists("{0}request.submitted".format(folder_path))
            request_processed = path.exists("{0}request.processed".format(folder_path))
            request_returned = path.exists("{0}request.returned".format(folder_path))
            request_voided = path.exists("{0}request.voided".format(folder_path))
            filename = "{0}{1}".format(folder_path, request.json.get("file", None))

            if request.json['delete_request'] and not request_submitted and not request_processed and not request_returned and not request_voided:
                rmtree(folder_path, True)

                if flash_message:
                    flash("Request deleted successfully.", "success")

                return jsonify({"success": True, "type": "success", "message": "Request deleted successfully."})
            elif request.json['delete_request']:
                if flash_message:
                    flash("This request can no longer be deleted.", "error")

                return jsonify({"success": False, "type": "error", "message": "This request can no longer be deleted."})

            if filename and path.exists(filename):
                remove(filename)

            return jsonify({"type": "success", "message": "File successfully deleted."})
        except Exception as e:
            print(e)
            pass

        return jsonify({"type": "error", "message": "Invalid request format or origin."})

    def put(self):
        """
        This method takes care of request submissions (i.e., when a request goes from a draft/returned state into a
        submitted state) and saving requests for drafts. First a sanity check ensures that all listed files in the
        request are present in the request directory, if they are not an exception is raised. Then a check determines
        if this is just a draft save or a submission. After, if it is a submission the history is updated to reflect
        this and and e-mail is sent out to all party's associated with the request as well as the CSE Webmaster.
        Finally, a message is queued to flash when the page redirects to the app index page.

        :return: A JSON response specifying whether the action was successful or not
        """
        folder_path = "{0}/user_uploads/{1}/{2}/".format(self.__APP_PATH__, current_user.net_id, request.json["folder_name"])
        request_submitted_marker = "{0}request.submitted".format(folder_path)
        request_processed_marker = "{0}request.processed".format(folder_path)
        request_voided_marker = "{0}request.voided".format(folder_path)

        if not path.exists(request_submitted_marker) and not path.exists(request_processed_marker) and not path.exists(request_voided_marker):
            try:
                accountant_emails = [["{0} {1}".format(accountant[0], accountant[1]), accountant[2]] for accountant in Users.query.with_entities(Users.first_name, Users.last_name, Users.email).join(Users.user_roles).filter((UserRoles.role == "STFADM") & (Users.net_id == "sherrift")).all()]
                Path(folder_path).mkdir(parents=True, exist_ok=True)

                request_resubmission = path.exists("{0}request.returned".format(folder_path))
                request_details = request.json["request_details"]
                optional_message = request.json.get("user_message", "").strip()
                user_message = optional_message
                all_files = [path.join(folder_path, f) for f in listdir(folder_path) if path.isfile(path.join(folder_path, f))]

                request_files = ["{0}{1}".format(folder_path, request_file["upload"]["filename"].replace(" ", "_"))
                                 for request_file in request_details["files"]]

                for file in request_files:
                    if file not in all_files:
                        raise Exception("File in submission details was not found on the server.\nFile: {0}".format(file))

                request_returned_marker = "{0}request.returned".format(folder_path)
                request_saved_marker = "{0}request.saved".format(folder_path)

                if request.json["save_for_later"]:
                    if path.exists("{0}submission.json".format(folder_path)):
                        with open("{0}submission.json".format(folder_path), mode="r") as request_details_json:
                            request_details["history"] = json.load(request_details_json)["history"]

                    with open(request_saved_marker, mode="w") as saved_marker:
                        saved_marker.write("/n")

                    with open("{0}submission.json".format(folder_path), mode="w") as request_details_json:
                        json.dump(request_details, request_details_json)

                    return jsonify({"status": True})

                with open(request_submitted_marker, mode="w") as submitted_marker:
                    submitted_marker.write("/n")

                if path.exists(request_saved_marker):
                    remove(request_saved_marker)

                if path.exists(request_returned_marker):
                    remove(request_returned_marker)

                if optional_message:
                    optional_message_html = "<br><br>Please see the attached message from {0} below:" \
                                            "<br><blockquote style='border-left: 3px solid rgb(200, 200, 200); " \
                                            "border-top-color: rgb(200, 200, 200); border-right-color: " \
                                            "rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); " \
                                            "padding-left: 1ex; margin-left: 0.8ex; color: rgb(102, 102, 102);'>" \
                                            "<div style='color: rgb(0, 0, 0);'>{1}</div>" \
                                            "</blockquote>".format(current_user.first_name, optional_message)
                    optional_message = "\n\nPlease see the attached message from {0} below:" \
                                       "\n{1}".format(current_user.first_name, optional_message)
                else:
                    optional_message_html = ""

                date_time = "{0}".format(datetime.now()).split()
                history_update = {
                    "date": date_time[0],
                    "time": date_time[1],
                    "action": None,
                    "actor": {
                        "first_name": current_user.first_name,
                        "last_name": current_user.last_name,
                        "email": current_user.email,
                        "uta_id": current_user.uta_id
                    },
                    "metadata": {
                        "message": user_message
                    }
                }

                if request_resubmission:
                    with open("{0}submission.json".format(folder_path), mode="r") as request_details_json:
                        request_details["history"] = json.load(request_details_json)["history"]

                    history_update["action"] = "Resubmitted"
                    email_subject = "Reimbursement Request Resubmitted"
                    email_body = app_constants.EMAILS["submit_request"]["text"][request_resubmission].format(
                        "Sherri",
                        request_details["requester"]["first_name"],
                        request_details["requester"]["last_name"],
                        "{0}mavapps/".format(URL_FULL_PATH),
                        request_details["short_description"],
                        request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                        request_details["total_amount"], optional_message)
                    email_body_html = app_constants.EMAILS["submit_request"]["html"][request_resubmission].format(
                        "Sherri",
                        request_details["requester"]["first_name"],
                        request_details["requester"]["last_name"],
                        "{0}mavapps/".format(URL_FULL_PATH),
                        request_details["short_description"],
                        request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                        request_details["total_amount"], optional_message_html)
                else:
                    history_update["action"] = "Submitted"
                    email_subject = "Reimbursement Request Opened"
                    email_body = app_constants.EMAILS["submit_request"]["text"][request_resubmission].format(
                        "Sherri",
                        request_details["requester"]["first_name"],
                        request_details["requester"]["last_name"],
                        "{0}mavapps/".format(URL_FULL_PATH),
                        request_details["short_description"],
                        request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                        request_details["total_amount"], optional_message)
                    email_body_html = app_constants.EMAILS["submit_request"]["html"][request_resubmission].format(
                        "Sherri",
                        request_details["requester"]["first_name"],
                        request_details["requester"]["last_name"],
                        "{0}mavapps/".format(URL_FULL_PATH),
                        request_details["short_description"],
                        request_details["pay_to"]["name"], request_details["pay_to"]["email"],
                        request_details["total_amount"], optional_message_html)

                with open("{0}submission.json".format(folder_path), mode="w") as request_details_json:
                    request_details["history"].append(history_update)
                    json.dump(request_details, request_details_json)

                if SRV != "prod":
                    emails = self.__TEST_EMAILS__
                else:
                    emails = [["{0} {1}".format(request_details["requester"]["first_name"], request_details["requester"]["last_name"]), request_details["requester"]["email"]]] \
                             + accountant_emails + self.__PROD_EMAILS__

                self.mailer.send_mail(emails, email_subject, email_body, email_body_html, from_name="CSE Reimbursement App")

                flash("Your request was submitted successfully.", "success")

                return jsonify({"status": True})
            except Exception as e:
                print(e)

        flash("Oops! It seems the status of the request has changed. Please verify it still exists and is editable.", "error")

        return jsonify({"status": False})

    def uploads_present(self):
        """
        This function determines whether any uploads are present to be displayed to the current user.

        :return: Boolean specifying whether uploads were found
        """
        is_stfadm = get_user_roles(current_user.net_id)["STFADM"]

        try:
            if is_stfadm:
                if len([f.path for f in scandir("{0}/user_uploads/".format(self.__APP_PATH__)) if f.is_dir()]) > 0:
                    return True
            elif len([f.path for f in scandir("{0}/user_uploads/".format(self.__APP_PATH__)) if f.is_dir() and current_user.net_id in f.name]) > 0:
                    return True
        except FileNotFoundError:
            pass
        return False

    def get_uploads(self, query=None, sort_func="date", sort_descending=True, request_type_list=None, filter_status_list=None,
                    filter_date1=None, filter_date2=None, filter_amount1=None, filter_amount2=None):
        """
        This method takes care of sorting and filtering out requests for the view/requests/ and view/requests/search/
        pages. A user can filter requests with a query, by type, by status, by date, or by requested amount. The
        filtered requests can then be sorted by submission date, latest activity, or request amount. Latest activity
        is similar to submission date except that, for example, if a request was submitted a while a ago and just
        recently got returned/processed it will then appear near the top of the results. The sorting can also be
        done in ascending or descending order. Note that true must be returned for all filters applied for a request
        to get added to the final results.

        :param query: String specifying the user query
        :param sort_func: String specifying sorting function to be used
        :param sort_descending: Boolean specifying whether to sort descending (default) or ascending
        :param request_type_list: A list of the request types to use in filtering requests
        :param filter_status_list: A list of the request statuses to use in filtering requests
        :param filter_date1: Datetime date which the request should be on or after
        :param filter_date2: Datetime date which the request should be on or before
        :param filter_amount1: Float amount which the request should be greater than or equal to
        :param filter_amount2: Float amount which the request should be less than or equal to
        :return:
        """
        def filter_by_query(x, _query=None):
            """
            This helper method filters request using a user query. A partial match ratio is used and a threshold of 60
            determines whether this method returns true or not.

            :param x: A request dictionary object containing all the request details
            :param _query: String specifying the user query to use in filtering
            :return: Boolean specifying whether to add the request or not
            """
            if _query:
                scores = [fuzz.partial_ratio(_query, "{0} {1}".format(x["requester"]["first_name"], x["requester"]["last_name"])),
                          fuzz.partial_ratio(_query, x["requester"]["email"]),
                          fuzz.partial_ratio(_query, x["requester"]["net_id"]),
                          fuzz.partial_ratio(_query, x["pay_to"]["name"]),
                          fuzz.partial_ratio(_query, x["pay_to"]["email"]),
                          fuzz.partial_ratio(_query, x["pay_to"]["id"] or ""),
                          fuzz.partial_ratio(_query, x["short_description"]),
                          fuzz.partial_ratio(_query, x["notes"])]

                if max(scores) > 60:
                    return True
                return False
            return True

        def filter_by_type(x, _request_type_list=None):
            """
            This helper method filters requests based on the types that were selected. If a request matches any type
            then this method returns true.

            :param x: A request dictionary object containing all the request details
            :param _request_type_list: A list of the request types to use in filtering
            :return: Boolean specifying whether to add the request or not
            """
            if _request_type_list:
                for request_type in _request_type_list:
                    if x["request_type"] == request_type:
                        return True
                return False
            return True

        def filter_by_status(x, _filter_status_list=None):
            """
            This helper method filters requests based on the statuses that were selected. If a request matches any of
            the statuses specified then this method returns true.

            :param x: A request dictionary object containing all the request details
            :param _filter_status_list: A list of the request statuses to use in filtering
            :return: Boolean specifying whether to add the request or not
            """
            if _filter_status_list:
                for filter_status in _filter_status_list:
                    if x.get(filter_status, False):
                        return True
                return False
            return True

        def filter_by_date(x, _filter_date1=None, _filter_date2=None):
            """
            This helper method filters requests based on the date they were submitted. If a request matches the date or
            date range then true is returned.

            :param x: A request dictionary object containing all the request details
            :param _filter_date1: Datetime date which the request should be on or after
            :param _filter_date2: Datetime date which the request should be on or before
            :return: Boolean specifying whether to add the request or not
            """
            if _filter_date1 or _filter_date2:
                request_date = datetime(x["request_date"]["year"], x["request_date"]["month"], x["request_date"]["day"], 0, 0)

                if _filter_date1 and _filter_date2:
                    return _filter_date1 <= request_date <= _filter_date2
                return _filter_date1 <= request_date if _filter_date1 else request_date <= _filter_date2
            return True

        def filter_by_request_amount(x, _filter_amount1=None, _filter_amount2=None):
            """
            This helper method filters requests based on the amount requested. If a request matches the amount or
            range of amounts then true is returned.

            :param x: A request dictionary object containing all the request details
            :param _filter_amount1: Float amount which the request should be greater than or equal to
            :param _filter_amount2: Float amount which the request should be less than or equal to
            :return: Boolean specifying whether to add the request or not
            """
            if _filter_amount1 or _filter_amount2:
                request_total = x["total_amount"]

                if _filter_amount1 and _filter_amount2:
                    return _filter_amount1 <= request_total <= _filter_amount2
                return _filter_amount1 <= request_total if _filter_amount1 else request_total <= _filter_amount2
            return True

        def sort_by_submission_date(x):
            """
            Sorts requests by submission date. Datetime dates are used for sorting.

            :param x: A request dictionary object containing all the request details
            :return: Datetime date to use as a key to sort by
            """
            return datetime.strptime("{0}-{1}-{2}".format(x["request_date"]["year"], x["request_date"]["month"], x["request_date"]["day"]), '%Y-%m-%d')

        def sort_by_latest_activity(x):
            """
            Sorts requests by latest activity date. Datetime dates are used for sorting.

            :param x: A request dictionary object containing all the request details
            :return: Datetime date to use as a key to sort by
            """
            if len(x["history"]) > 0:
                return datetime.strptime(x["history"][-1]["date"], '%Y-%m-%d')
            return datetime.strptime("{0}-{1}-{2}".format(x["request_date"]["year"], x["request_date"]["month"], x["request_date"]["day"]), '%Y-%m-%d')

        def sort_by_request_amount(x):
            """
            Sorts requests by amount requested.

            :param x: A request dictionary object containing all the request details
            :return: Float value of the amount requested to use a key to sort by
            """
            return float(x["total_amount"])

        sorting_functions_map = {
            "date": sort_by_submission_date,
            "activity": sort_by_latest_activity,
            "amount": sort_by_request_amount
        }

        all_uploads = []
        is_stfadm = get_user_roles(current_user.net_id)["STFADM"]

        try:
            if is_stfadm:
                user_folders = [f.path for f in scandir("{0}/user_uploads/".format(self.__APP_PATH__)) if f.is_dir()]
            else:
                user_folders = [f.path for f in scandir("{0}/user_uploads/".format(self.__APP_PATH__))
                                if f.is_dir() and current_user.net_id in f.name]
        except FileNotFoundError:
            return all_uploads

        for folder in user_folders:
            user_uploads = [f.path for f in scandir(folder) if f.is_dir()]

            for upload in user_uploads:
                try:
                    with open("{0}/submission.json".format(upload)) as submission_json:
                        upload_dict = json.load(submission_json)

                    upload_dict["request_saved"] = path.exists("{0}/request.saved".format(upload))
                    upload_dict["request_submitted"] = path.exists("{0}/request.submitted".format(upload))
                    upload_dict["request_processed"] = path.exists("{0}/request.processed".format(upload))
                    upload_dict["request_returned"] = path.exists("{0}/request.returned".format(upload))
                    upload_dict["request_voided"] = path.exists("{0}/request.voided".format(upload))
                    upload_dict["request_draft"] = upload_dict["request_saved"] and not upload_dict["request_returned"]

                    if not is_stfadm or (is_stfadm and not upload_dict["request_saved"] and not upload_dict["request_returned"]):
                        if (
                                filter_by_query(upload_dict, query) and
                                filter_by_status(upload_dict, filter_status_list) and
                                filter_by_date(upload_dict, filter_date1, filter_date2) and
                                filter_by_request_amount(upload_dict, filter_amount1, filter_amount2) and
                                filter_by_type(upload_dict, request_type_list)
                        ):
                            all_uploads.append(upload_dict)
                except FileNotFoundError:
                    pass

        all_uploads.sort(key=sorting_functions_map[sort_func], reverse=sort_descending)

        return all_uploads

    def make_pdf(self, net_id, request_id, request_date):
        """
        This method takes care of generating the PDF summary for a request. A logo is appended to the top of the page
        and the formatting is done with simple characters as unicode characters don't seem to play well with the
        underlying library this uses.

        :param net_id: The NetID of the user the request belongs to
        :param request_id: The request id to help identify which request is being processed
        :param request_date: The request date
        :return: Boolean specifying whether the PDF was able to be generated
        """
        with open("{0}/user_uploads/{1}/{2}/submission.json".format(self.__APP_PATH__, net_id, request_id), mode="r") as json_file:
            request_details = json.load(json_file)

        files_text = ""
        travel_text = None

        if request_details["request_type"] == "travel":
            travel_text = "\n\nTravel Details:\n" \
                          "\t\t\t\tTravel from: {0} ({1})\n" \
                          "\t\t\t\tTravel to: {2} ({3})\n" \
                          "\t\t\t\tTravel Number: {4}\n" \
                          "\t\t\t\tEvent Website: {5}".format(request_details["travel_from"],
                                                              request_details["travel_from_date"],
                                                              request_details["travel_to"],
                                                              request_details["travel_to_date"],
                                                              request_details["travel_number"],
                                                              request_details.get("event_website", "N/A"))
        for file in request_details["files"]:
            amount_text = "${0}".format(file["dollar_amount"]) if file["dollar_amount"] > 0.0 else "Auxiliary File"
            files_text += "\t\t\t\t{0} ({1})\n\t\t\t\t\t\t\t\t" \
                          "{2}\n\t\t\t\t\t\t\t\t{3}\n\n".format(file["label"], amount_text,
                                                                file["name"], file["description"])

        if request_details["notes"].strip():
            request_notes = "\nNotes:\n{0}".format(request_details["notes"].strip())
        else:
            request_notes = ""

        pdf_title = "({0}) {1:02d}/{2:02d}/{3:04d} - {4:02d}:{5:02d}:{6:02d}, Amount: ${7}".format(
            request_details["request_date"]["weekday"], request_details["request_date"]["month"],
            request_details["request_date"]["day"], request_details["request_date"]["year"],
            request_details["request_date"]["hours"], request_details["request_date"]["minutes"],
            request_details["request_date"]["seconds"], request_details["total_amount"])

        if request_details["pay_to"]["id"]:
            pay_to_details = "{0} ({1}, {2})".format(request_details["pay_to"]["name"], request_details["pay_to"]["id"],
                                                     request_details["pay_to"]["email"])
        else:
            pay_to_details = "{0} ({1})".format(request_details["pay_to"]["name"], request_details["pay_to"]["email"])

        pdf_body = "{0}{1}\n\nRequestee: \n\t\t\t\tAccount:{2}\n\t\t\t\tName: {3} {4} ({5})\n\t\t\t\t" \
                   "Phone: {6}\t|\tNet ID: {7}\t\n\nPay To:\n\t\t\t\tName: {8}{9}\n\n" \
                   "Files:\n{10}".format(request_details["short_description"], request_notes,
                                         request_details["account_number"],
                                         request_details["requester"]["first_name"],
                                         request_details["requester"]["last_name"],
                                         request_details["requester"]["email"],
                                         request_details["requester"]["phone_number"],
                                         request_details["requester"]["net_id"],
                                         pay_to_details,
                                         travel_text,
                                         files_text)
        try:
            logo_path = "{0}/static/assets/main/uta_logo.png".format(self.__APP_PATH__.split("/apps/")[0])
            pdf = PDFMaker(**{"title": "Reimbursement Request Report"})

            pdf.set_margins(left=19.05, top=19.05, right=19.05)
            pdf.set_auto_page_break(auto=True, margin=19.05)
            pdf.set_author("MavApps - Reimbursement App")
            pdf.print_page(pdf_title, pdf_body)
            pdf.image(logo_path, x=53, y=11, w=107, h=10, type="PNG", link="https://uta.edu")
            pdf.output("{0}/user_uploads/{1}/{2}/[{1}-{3}]_report.pdf".format(self.__APP_PATH__, net_id, request_id, request_date), "F")
        except Exception as e:
            print(e)
            return False
        return True
