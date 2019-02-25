import os
from base64 import b64encode
from math import ceil
from os import path
from flask import (
    render_template, request, jsonify, flash, session, send_file
)
from flask import url_for, abort, redirect
from flask_classful import FlaskView, route
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import or_
from alumni_directory.models import Graduates, Alumni, db
from shared.mailer import Mailer
from shared.constants import NO_PHOTO
from .oauth import OAuthSignIn
from pathlib import Path
from werkzeug.utils import secure_filename
from sqlalchemy import exc

ts = URLSafeTimedSerializer(os.environ.get('APP_SECRET_KEY', default="thisisasecret"))


class AlumniDirectoryApp(FlaskView):
    route_base = "/"

    def __init__(self):
        self.__APP_PATH__ = path.dirname(path.realpath(__file__))

    @route('/', methods=['POST', 'GET'])
    def index(self):
        print("============ON INDEX PAGE===========")
        per_page = 20
        page = 0

        if request.form.get("page-number") is not None and len(request.form.get("page-number")) != 0:
            page = int(float(request.form.get("page-number")))
 
        max_pages = ceil(db.session.query(db.func.count(Alumni.net_id).label("count")).first().count / (per_page * 1.0))

        if page > max_pages:
            page = max_pages

        year = Graduates.query.with_entities(Graduates.graduation_year.distinct()).order_by(Graduates.graduation_year.asc()).all()
        years = ';'.join([str(y[0]) for y in year])
        alumni = []

        query_results = Alumni.query.join(Alumni.graduate_info).order_by(Graduates.first_name)

        if request.form.get("gradyear") is not None:
            filter_year = request.form.get("gradyear").split(',')
            query_results = query_results.filter((filter_year[0] <= Graduates.graduation_year) & (filter_year[1] >= Graduates.graduation_year))
            grad_year_filter = ';'.join(filter_year)
        else:
            grad_year_filter = str(year[0][0]) + ";" + str(year[-1][0])

        countries = []

        if request.form.get("old_country") is not None and request.form.get("old_country").strip():
            countries = request.form.get("old_country").strip(';').split(';')

        if request.form.get("new_country") is not None  and request.form.get("new_country").strip():
            countries.append(request.form.get("new_country"))

        states = []

        if request.form.get("old_state") is not None and request.form.get("old_state").strip():
            states = request.form.get("old_state").strip(';').split(';')

        if request.form.get("new_state") is not None and request.form.get("new_state").strip():
            states.append(request.form.get("new_state"))

        if len(countries) != 0 and len(states) != 0:
            query_results = query_results.filter(or_(Alumni.country.in_(countries), Alumni.state.in_(states)))
        elif len(countries) != 0:
            query_results = query_results.filter(Alumni.country.in_(countries))
        elif len(states) != 0:
            query_results = query_results.filter(Alumni.state.in_(states))

        if len(request.form.getlist("degree")) != 0:
            degree = []

            if "BS" in request.form.getlist("degree"):
                degree.append("UNGRAD")

            if "MS" in request.form.getlist("degree"):
                degree.append("MSNT")
                degree.append("MSTH")

            if "PHD" in request.form.getlist("degree"):
                degree.append("PhD")

            query_results = query_results.filter(Alumni.graduate_info.has(Graduates.degree.in_(degree)))

        names = ""

        if request.form.get("names") is not None:
            names = request.form.get("names")
            name = "%{0}%".format(' '.join(names.split(' ')))
            query_results = query_results.filter(
                or_(Graduates.first_name.like(name), Graduates.middle_name.like(name), Graduates.last_name.like(name), 
                    (Graduates.first_name + " " + Graduates.last_name).like(name),
                    (Graduates.first_name + " " + Graduates.middle_name + " " + Graduates.last_name).like(name)))

        query_results = query_results.filter(Alumni.ispublic).paginate(page, per_page, False)

        for i, alumnus in enumerate(query_results.items):
            if alumnus.photo:
                alumni_photo = b64encode(alumnus.photo).decode("utf-8")
            else:
                alumni_photo = NO_PHOTO

            degree_name = ""

            if alumnus.graduate_info.degree == "UNGRAD":
                degree_name = "Bachelor’s Degree"
            elif alumnus.graduate_info.degree == "MSNT" or alumnus.graduate_info.degree == "MSTH":
                degree_name = "Master’s Degree"
            elif alumnus.graduate_info.degree == "PhD":
                degree_name = "Ph.D."

            if alumnus.public_area is None:
                alumnus.public_area = ""

            alumni.append({"id": alumnus.net_id,
                           "first_name": alumnus.graduate_info.first_name,
                           "last_name": alumnus.graduate_info.last_name,
                           "company": alumnus.company,
                           "title": alumnus.title,
                           "photo": alumni_photo,
                           "graduation_year": alumnus.graduate_info.graduation_year,
                           "email": alumnus.social_email,
                           "degree": degree_name,
                           "public_area": alumnus.public_area})

        form_data = {"years": years,
                     "gradyear": grad_year_filter,
                     "countries": ';'.join(countries),
                     "usstates": ';'.join(states),
                     "degree": request.form.getlist("degree"),
                     "names": names,
                     "alumni": alumni}

        return render_template("view.html", pagination=query_results, form_data=form_data,
                               endpoint="AlumniDirectoryApp:index")


    @route('/view/user/<user_id>')
    def view_user(self, user_id=None):
        if user_id:
            alumnus = Alumni.query.join(Alumni.graduate_info).filter(Alumni.net_id == user_id).first()

            name = ""

            if alumnus.graduate_info.first_name is not None:
                name += alumnus.graduate_info.first_name + " "
            if alumnus.graduate_info.middle_name is not None:
                name += alumnus.graduate_info.middle_name + " "
            if alumnus.graduate_info.last_name is not None:
                name += alumnus.graduate_info.last_name

            if alumnus.public_area is None:
                alumnus.public_area = ""

            if alumnus.photo:
                alumnus_photo = b64encode(alumnus.photo).decode("utf-8")
            else:
                alumnus_photo = NO_PHOTO

            if alumnus.public_area is None:
                alumnus.public_area = ""

            alumnus = {"id": alumnus.net_id,
                       "name": name,
                       "email": alumnus.social_email,
                       "photo": alumnus_photo,
                       "country": alumnus.country,
                       "state": alumnus.state,
                       "company": alumnus.company,
                       "title": alumnus.title,
                       "biography": alumnus.biography,
                       "twitter": alumnus.twitter,
                       "facebook": alumnus.facebook,
                       "linkedin": alumnus.linkedin,
                       "public_area": alumnus.public_area}

            return render_template("profile.html", alumnus=alumnus)
        return "User not found."


    @route('/view/user/edit/<user_id>')
    def edit_user(self, user_id=None):
        try:
            if (session['edit_permission_for'] == user_id) and (session['logged_in'] == True) and (session['edit_target'] == user_id):
                if user_id:
                    query_result = db.session.query(Alumni, Graduates).outerjoin((Graduates, Alumni.net_id == Graduates.net_id)).filter(Alumni.net_id == user_id).first()

                    if query_result.Alumni.photo:
                        alumnus_photo = b64encode(query_result.Alumni.photo).decode("utf-8")
                    else:
                        alumnus_photo = NO_PHOTO

                    if query_result.Alumni.company is None:
                        query_result.Alumni.company = ""

                    if query_result.Alumni.title is None:
                        query_result.Alumni.title = ""

                    if query_result.Alumni.biography is None:
                        query_result.Alumni.biography = ""

                    if query_result.Alumni.twitter is None:
                        query_result.Alumni.twitter = ""

                    if query_result.Alumni.facebook is None:
                        query_result.Alumni.facebook = ""

                    if query_result.Alumni.linkedin is None:
                        query_result.Alumni.linkedin = ""

                    alumnus = {"id": query_result.Alumni.net_id,
                            "photo": alumnus_photo,
                            "email": query_result.Alumni.social_email,
                            "country": query_result.Alumni.country,
                            "state": query_result.Alumni.state,
                            "company": query_result.Alumni.company,
                            "title": query_result.Alumni.title,
                            "biography": query_result.Alumni.biography,
                            "twitter": query_result.Alumni.twitter,
                            "facebook": query_result.Alumni.facebook,
                            "linkedin": query_result.Alumni.linkedin,
                            "public_area": query_result.Alumni.public_area,
                            "ispublic": query_result.Alumni.ispublic}

                    return render_template("edit.html", alumnus=alumnus)
                return "User not found."
            else:
                message = """
                You do not have the permission to view or edit this page. Please login to this user's
                profile to access the page.
                """
                return self.info_message(message)
        except KeyError as err:
            message = """
            You do not have the permission to view or edit this page. Please login to this user's
            profile to access the page.
            """
            return self.info_message(message)

    @route('/view/user/update/', methods=['POST'])
    def update_user(self):
        if 'alumnus-photo' in request.files:
            db.session.query(Alumni).filter(Alumni.net_id == request.form.get('alumnus-id')).update({"photo": request.files['alumnus-photo'].read()})

        country = request.form.get("alumnus-country")
        state = request.form.get("alumnus-state")

        if country != "USA":
            state = None

        company = None

        if len(request.form.get('alumnus-company')) > 0:
            company = request.form.get('alumnus-company')

        title = None

        if len(request.form.get('alumnus-title')) > 0:
            title = request.form.get('alumnus-title')

        biography = None

        if len(request.form.get('alumnus-biography')) > 0:
            biography = request.form.get('alumnus-biography')

        twitter = None

        if len(request.form.get('alumnus-twitter')) > 0:
            twitter = request.form.get('alumnus-twitter')

        facebook = None

        if len(request.form.get('alumnus-facebook')) > 0:
            facebook = request.form.get('alumnus-facebook')

        linkedin = None

        if len(request.form.get('alumnus-linkedin')) > 0:
            linkedin = request.form.get('alumnus-linkedin')

        ispublic = False

        if request.form.get('alumnus-ispublic') is not None:
            ispublic = True

        public_area = '#'.join(request.form.getlist("public_area"))

        if len(public_area) == 0:
            public_area = None

        db.session.query(Alumni).filter(Alumni.net_id == request.form.get('alumnus-id')).update({
            "social_email": request.form.get('alumnus-email'),
            "country": country,
            "state": state,
            "company": company,
            "title": title,
            "biography": biography,
            "twitter": twitter,
            "facebook": facebook,
            "linkedin": linkedin,
            "public_area": public_area,
            "ispublic": ispublic})

        db.session.commit()

        flash("Profile updated successfully.", "success")

        self.oauth_logout()

        return redirect(url_for("AlumniDirectoryApp:view_user", user_id=request.form.get('alumnus-id')))

    @route('/view/user/edit_request/login/<alumnus_id>')
    def edit_request_login(self, alumnus_id=None):
        """
        Queries the alumni, and either:
        a) Returns the editing page if the user is already logged in.
        b) Calls the function that sends out the authentiation token.

        :param alumnus_id: The NetID of the user requsting app access.
        """
        if alumnus_id:
            alumnus = Alumni.query.join(
                Alumni.graduate_info
            ).filter(Alumni.net_id == alumnus_id).first()
            
            if not alumnus:
                message = """
                Sorry, it appears the NetID {net_id} is invalid. 
                """.format(net_id=alumnus_id)
                return self.info_message(message)
            else:
                alumnus_details = {
                    "first_name": alumnus.graduate_info.first_name,
                    "last_name" : alumnus.graduate_info.last_name,
                    "email"     : alumnus.social_email,
                    "title"     : alumnus.title,
                    "netid_token" : ts.dumps(
                        alumnus.net_id, salt="netid-confirm-key"
                    )
                }
                
                session['edit_target'] = alumnus_id
                if ("logged_in" in session) and (session["logged_in"] == True):
                    return redirect(
                        url_for("AlumniDirectoryApp:edit_request", user_id=alumnus_id)
                    )
                else:
                    try:
                        notify = self.email_token(alumnus_details)
                    except Exception as e:
                        print("Exception: ", e)
                        print("Email: \n", notify) 
                    return redirect(url_for('AlumniDirectoryApp:inform_email'))
        else:
            message = """
            Sorry, please specify the profile you wish to edit.
            """
            return self.info_message(message)



    def email_token(self, request_details):
        """
        Sends an email containing an authentication to the users whose information
        is encapsulated in request_details.

        :param request_details: dictionary object containing details about user
                                attempting to log in.
        """

        email_title = "Alumni Directory: Login Token"
        from_name = "CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>Dear {username},<br></p>

                    <p>
                        We have you received your request to log into your profile on CSE Alumni Directory. If you still wish to login, please access your profile by clicking <a href="{login_link}">here</a>.
                    <br> 
                    </p>
                    <p>
                        Also, kindly note that this link will only be valid for 24 hrs. You can, however, click on the "Edit profile" button on your public page to have another link sent to you.
                        <br>
                    </p>
                    <p>
                        Best regards, <br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>
                </body>
            </html>
        """.format(
            username = request_details["first_name"] + " " + request_details["last_name"],
            login_link = url_for('AlumniDirectoryApp:alumni_login_confirm', token=request_details["netid_token"], _external=True) 
        )
        email_body_html = email_body
        try:
            Mailer().send_mail(
               ["webmaster-cse1@uta.edu", request_details['email']],
               email_title, email_body, email_body_html, from_name=from_name)
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))


    @route('/alumnidirectory/login/confirm/<token>')
    def alumni_login_confirm(self, token=None):
        """
        Logs user in using tokenized user netid.

        :param token: tokenized user netid
        """        
        if token:
            alumnus_id = ts.loads(token, salt="netid-confirm-key", max_age=86400)
            alumnus = Alumni.query.join(
                Alumni.graduate_info
            ).filter(Alumni.net_id == alumnus_id).first()
            if alumnus:
                session['edit_target'] = alumnus.net_id
                session['edit_permission_for'] = alumnus.net_id
                return redirect(url_for("AlumniDirectoryApp:edit_request", user_id=alumnus.net_id))
        else:
            message = """
            It appears the URL you are using is faulty. Please make sure 
            you copied it correctly, or click directly on the link you 
            received in the email.
            """
            return self.info_message(message)
        
   
    @route('/view/update_email', methods=['POST'])
    def initiate_email_update(self):
        """
        Receives and tokenizes email from user and sends 
        confirmation link to user's current email address
        to confirm the request
        """

        net_id = session['edit_target']
        alumnus = Alumni.query.join(
            Alumni.graduate_info
        ).filter(Alumni.net_id == net_id).first()
        new_email = request.json['alumnus']

        if new_email:
            alumnus_details = {
                    "first_name"  : alumnus.graduate_info.first_name,
                    "last_name"   : alumnus.graduate_info.last_name,
                    "email"       : alumnus.social_email,
                    "title"       : alumnus.title,
                    "netid_token" : ts.dumps(
                        alumnus.net_id, salt="netid-confirm-key"
                    )
            }
            try:
                notify = self.mail_email_change(alumnus_details, new_email)
                return jsonify({'Success': "Success"})
            except Exception as e:
                print("Exception: ", e)
                print("Email: \n", notify)
                return jsonify({'email':new_email})
        else:
            data = request.get_json() 
            print(data)
            # print(request.args)
            print("Nothing came in")
            return jsonify({'error':'Missing data'})

    
    def mail_email_change(self, alumnus_details, new_email):
        """
        Sends an email containing a 'change of email' authentication
        link to the alumni whose details are encapsulated in 
        alumnus details.

        :param alumnus_details: dictionary object containing details 
        about the alumni making the 'change of email' request.
        """

        new_email_token = ts.dumps(new_email,salt="email-confirm-key")
        email_title = "Alumni Directory: Change of Email"
        from_name   = "CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>Dear {username},<br></p>

                    <p>
                        We have you received your request to change your email address on CSE Alumni Directory to {new_email}. If you still wish to do so, kindly complete the process by clicking <a href="{change_email_link}">here</a>.
                    <br> 
                    </p>
                    <p>
                        Also, kindly note that this link will only be valid for 24 hrs. You can, however, re-initiate the process by clicking on the "Change Email" button in your profile editing page to have another link sent to you.
                        <br>
                    </p>
                    <p>
                        Best regards, <br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>
                </body>
            </html>

        """.format(
            username = alumnus_details["first_name"] + " " + alumnus_details["last_name"],
            new_email = new_email,
            change_email_link = url_for(
                'AlumniDirectoryApp:confirm_email_change',
                 id_token = alumnus_details["netid_token"], email_token = new_email_token, 
                 _external=True
            ) 
        )
        email_body_html = email_body
        try:
            Mailer().send_mail(
                ["webmaster-cse1@uta.edu", alumnus_details['email']],
               email_title, email_body, email_body_html, from_name=from_name
            )
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))           
    
    @route('/view/confirm_update_email/<id_token>/<email_token>')
    def confirm_email_change(self, id_token=None, email_token=None):
        """
        This route is reached when an Alumnus clicks on the "change
        email" confirmation link. It replaces the Alumnus' email with
        the new email which is encoded in the URL.

        :param id_token   : this is the tokenized netid of the Alumni
        :param email_token: this is the tokenized email of the Alumni
        """

        print("Thank you for confirming your email change.")
        return "In Progress"
    
    
    
    
    
    # Compute token and forward to confirmation view
    @route('/view/user/edit_request/temp/<user_id>')
    def edit_request(self, user_id=None):
        if user_id:
            if session['edit_permission_for'] == user_id:
                query_result = Alumni.query.filter(Alumni.net_id == user_id).first()
                grad_query_result = Graduates.query.filter(Graduates.net_id == user_id).first()
                alumnus = {
                    "first_name": grad_query_result.first_name,
                    "last_name": grad_query_result.last_name,
                    "email": grad_query_result.alt_email,
                    "title": query_result.title
                }
                print(os.environ.get('APP_SECRET_KEY', default=None))
                token = ts.dumps(alumnus["email"], salt='email-confirm-key')
                return redirect(url_for('AlumniDirectoryApp:confirm_edit_request', token=token))
            else:
                flash('You do not have permission to edit this user.', 'error')
                return redirect(url_for("AlumniDirectoryApp:view_user", user_id=user_id))


    @route('/view/user/edit_request/confirm/<token>')
    def confirm_edit_request(self, token=None):
        # store token in session here
        try:
            print("Token 2: ", token)
            email = ts.loads(token, salt='email-confirm-key', max_age=86400)
            session["logged_in"] = True
        except Exception as e:
            return "Not Found"
            abort(404)

        alumni = Alumni.query.filter(Alumni.graduate_info.has(alt_email=email)).first_or_404()
        return redirect(url_for('AlumniDirectoryApp:edit_user', user_id=alumni.net_id))


    @route('/authorize/<provider>/<email_token>')
    def oauth_authorize(self, provider, email_token=None):
        oauth = OAuthSignIn.get_provider(provider)
        return oauth.authorize(email_token)


    @route('/callback/<provider>')
    #def oauth_callback(self, provider, email_token=None):
    def oauth_callback(self, provider):
        oauth = OAuthSignIn.get_provider(provider)
        social_id, username, email = oauth.callback()

        if provider == 'facebook' and session['social_email_token']: 
            email = ts.loads(session['social_email_token'], salt="email-confirm-key", max_age=86400)
            #email = ts.loads(email_token, salt="email-confirm-key", max_age=86400)

        print("Email: ", email)
        if (social_id is None) or (email is None):
            message = """
            We did not receive your {info} from your selected authentication provider, {oauth_provider}. Please attempt registering for Alumni Directory using one of the other providers we have made available to you.""".format(
                info = "social ID" if social_id is None else "email",
                oauth_provider = provider
            )
            return self.info_message(message)
            #return redirect(url_for("AlumniDirectoryApp:index"))
        
        if 'edit_target' in session:
            edit_target = session['edit_target']
        else:
            return redirect(url_for("AlumniDirectoryApp:index"))

        # User is signing up
        if ('first_time_login' in session) and (session['first_time_login'] == True):
            new_alumni = Alumni.query.filter(Alumni.graduate_info.has(alt_email=email)).first()
            if new_alumni:
                try:
                    if provider == 'facebook':
                        target_alumni = Alumni.query.filter(Alumni.graduate_info.has(alt_email=email)).first()
                        target_alumni.facebk_id = social_id
                        db.session.commit()
                    if provider == 'google':
                        target_alumni = Alumni.query.filter(Alumni.graduate_info.has(alt_email=email)).first()
                        target_alumni.google_id = social_id
                        db.session.commit()
                    if provider == 'linkedin':
                        target_alumni = Alumni.query.filter(Alumni.graduate_info.has(alt_email=email)).first()
                        target_alumni.linkedin_id = social_id
                        db.session.commit()
                        print("Obtained target: %s" % target_alumni.graduate_info.first_name)
                        print("Linkedin socialid signup: %s" % social_id)
                except exc.IntegrityError as err:
                    db.session.rollback()
                    message = """
                    This email address or social-network profile is already in use by another account. Please try registering for Alumni Directory with a different email address."""
                    return self.info_message(message)
                    #return redirect(url_for("AlumniDirectoryApp:index"))

            else:
                message = """
                There is no user on our system associated with the email address we received from {oauth_provider}. Please ensure that you are using the same email address, and the same authentication provider that you used when signing up to Alumni Directory.
                """.format(oauth_provider = provider)
                return self.info_message(message)
        
        current_user.social_id = social_id
        if provider == 'facebook':
            target_alumni = Alumni.query.filter_by(facebk_id=social_id).first()
        elif provider == 'google':
            target_alumni = Alumni.query.filter_by(google_id=social_id).first()
        else:
            target_alumni = Alumni.query.filter_by(linkedin_id=social_id).first()
        if not target_alumni:
            message = """
            Sorry, it appears this {oauth_provider} account is not associated with any user on our system. Please verify that the account you are using to login is the same one you used to register for Alumni Directory. You can also try registering with this account if you are unsure.
            """.format(oauth_provider = provider)
            return self.info_message(message)
        else:
            #edit here to prevent allowance if email changes.
            session['edit_permission_for'] = edit_target
            # use this @destination to verify permission to edit page
            return redirect(url_for("AlumniDirectoryApp:edit_request", user_id=edit_target))


    @route('/oauth/logout')
    def oauth_logout(self):
        if ("logged_in" in session) and (session["logged_in"] == True):
            session.pop('logged_in')
        return redirect(url_for("AlumniDirectoryApp:index"))


    def info_message(self, message):
        return render_template('signup/general_info.html', error_info_message=message)

    @route('/alumnidirectory/signup')
    def alumni_dir_signup(self):
        # create and send token to users email address
        alumni_id = session['edit_target']
        alumni_query = Alumni.query.filter_by(net_id=alumni_id).first()
        grad_alumni_query = Graduates.query.filter(Graduates.net_id == alumni_id).first()

        if grad_alumni_query.alt_email:
            # case 1: email for user exists on record
            alumni = {
                'email': grad_alumni_query.alt_email,
                'first_name': grad_alumni_query.first_name,
                'last_name': grad_alumni_query.last_name,
                'title': alumni_query.title
            }

            email_address = alumni['email']
            token = ts.dumps(email_address, salt="email-confirm-key")
            email_title = "Registration Request Received"
            from_name = "CSE Alumni Directory"

            email_body = """\
                <html>
                    <body>
                        <p>
                        Dear {0} {1},<br>

                        <p>
                            We received your request to register and edit <a href="{3}">your public profile information</a> on the CSE Alumni Directory of the University of Texas at Arlington.
                            <br>
                        </p>
                        <p>
                            If you did not initate this request, no worries. Someone else may have accidentally initiated the request by clicking the "Edit Profile" button on that page.
                            <br>
                        </p>

                        <p>
                            If it is indeed your intent to register and edit your profile, please <a href="{2}">click here</a> to proceed. Note that this link is valid for only 24 hours after you make the request. If it is past 24 hours, please inititatie the registration again by clicking the "Edit Profile" link on <a href="{3}">your profile page</a>. We will resend this email with a new link.
                            <br>
                        </p>

                        <p>
                            If you have questions, please contact webmaster-cse@uta.edu.
                            <br>
                        </p>

                        <p>
                            Best regards,<br>
                            Department of Computer Science and Engineering<br>
                            University of Texas at Arlington
                        </p>
                    </body>
                </html>
            """.format(
                alumni["first_name"],
                alumni["last_name"],
                url_for('AlumniDirectoryApp:alumni_signup_confirm', token=token, _external=True),
                url_for('AlumniDirectoryApp:view_user', user_id=alumni_id, _external=True)
            )

            email_body_html = email_body
        
            try:
                ##take out##
                #print("{0} \n {1}".format(email_title, email_body)) 
                ##take out##
                Mailer().send_mail(["webmaster-cse1@uta.edu", email_address], email_title, email_body, email_body_html, from_name=from_name)
                return redirect(url_for('AlumniDirectoryApp:inform_email'))
            except Exception as err:
                print("ConnectionRefusedError: {0}".format(err))
                print("{0} \n {1}".format(email_title, email_body))
                return "{0} \n {1}".format(email_title, email_body)



    
    @route('/alumnidirectory/signup_information_page')
    def signup_info_page(self):
        return render_template('/alumni_directory/signup_info.html')


    @route('/alumnidirectory/signup/done/<netid_token>/<social_email_token>')
    def alumni_signup_done(self, netid_token=None, social_email_token=None):
        try:
            net_id = ts.loads(netid_token, salt='email-confirm-key', max_age=86400)
            social_email = ts.loads(social_email_token, salt='email-confirm-key', max_age=86400)
            graduate_query = Graduates.query.filter(Graduates.net_id == net_id).first()
            alumni_query = Alumni.query.filter_by(net_id = net_id).first()

            if alumni_query:
                session['first_time_login'] = True
                session['edit_target'] = net_id
                graduate_query.alt_email = social_email
                db.session.commit()
                
                session['social_email_token'] = social_email_token

                return render_template('/alumni_directory/login.html', first_time_login=True, email=social_email, social_email_token=social_email_token)
            else:
                flash('No user mathches this email address', 'error')
                return redirect(url_for("AlumniDirectoryApp:index"))

        except Exception as e:
            print(e)
            return "Not Found"
            abort(404)
        return redirect(url_for("AlumniDirectoryApp:index"))


    @route('/alumnidirectory/signup/confirm/<token>')
    def alumni_signup_confirm(self, token=None):
        try:
            email = ts.loads(token, salt='email-confirm-key', max_age=86400)
            graduate_query = Graduates.query.filter_by(alt_email = email).first()
            alumni_query = Alumni.query.filter_by(net_id = graduate_query.net_id).first()

            if alumni_query:
                session['first_time_login'] = True
                session['edit_target'] = graduate_query.net_id

                return redirect(url_for('AlumniDirectoryApp:signup_email_capture'))
            else:
                flash('No user mathches this email address', 'error')
                return redirect(url_for("AlumniDirectoryApp:index"))

        except Exception as e:
            print(e)
            return "Not Found"
            abort(404)
        return redirect(url_for("AlumniDirectoryApp:index"))


    @route('/alumnidirectory/signup/email_capture', methods=['GET', 'POST'])
    def signup_email_capture(self):
        if request.method == 'GET':
            return render_template('/alumni_directory/signup/email_capture.html')

        if request.method == 'POST':
            try:
                social_email = request.form.get('social_email')
                alumni_id = session['edit_target']
                alumni_query = Alumni.query.filter_by(net_id=alumni_id).first()
                grad_alumni_query = Graduates.query.filter(Graduates.net_id == alumni_id).first()

                if grad_alumni_query.alt_email:
                    alumni = {
                        'first_name': grad_alumni_query.first_name,
                        'last_name': grad_alumni_query.last_name
                    }

                    social_email_token = ts.dumps(social_email, salt="email-confirm-key")
                    netid_token = ts.dumps(alumni_id, salt="email-confirm-key")

                    email_title = "Social Login Email Received"
                    from_name = "CSE Alumni Directory"

                    email_body = """\
                        <html>
                            <body>
                                <p>
                                Dear {0} {1},<br>

                                <p>
                                    Thank you for providing the email address ({4}) associated with your social media account, as part of the registration step before you can edit <a href="{3}">your public profile information</a> on the CSE Alumni Directory of the University of Texas at Arlington.
                                    <br>
                                </p>
                                <p>
                                    If you did not provide the email address or you did not initate the registration, please email webmaster-cse@uta.edu to let us know.
                                    <br>
                                </p>

                                <p>
                                    If it is indeed your intent to register and edit your profile, please <a href="{2}">click here</a> to proceed. Note that this link is valid for only 24 hours after you make the request. If it is past 24 hours, please inititatie the registration again by clicking the "Edit Profile" link on <a href="{3}">your profile page</a>. We will resend the emails for continuing the registration.
                                    <br>
                                </p>

                                <p>
                                    If you have questions, please contact webmaster-cse@uta.edu.
                                    <br>
                                </p>

                                <p>
                                    Best regards,<br>
                                    Department of Computer Science and Engineering<br>
                                    University of Texas at Arlington
                                </p>
                            </body>
                        </html>
                    """.format(
                        alumni["first_name"],
                        alumni["last_name"],
                        url_for('AlumniDirectoryApp:alumni_signup_done', netid_token=netid_token, social_email_token=social_email_token, _external=True),
                        url_for('AlumniDirectoryApp:view_user', user_id=alumni_id, _external=True), 
                        social_email
                    )

                    email_body_html = email_body
        
                    try:
                        ##take out##
                        #print("{0} \n {1}".format(email_title, email_body))
                        ##takeout##
                        Mailer().send_mail(["webmaster-cse1@uta.edu", social_email], email_title, email_body, email_body_html, from_name=from_name)
                        return render_template('signup/social_email_received.html', social_email = self.obfuscate_email(social_email))
                    except Exception as err:
                        print("ConnectionRefusedError: {0}".format(err))
                        return "{0} \n {1}".format(email_title, email_body)
                        
            except:
                flash('There was a problem while executing your request.', 'error')
                return redirect(url_for("AlumniDirectoryApp:index"))


    @route('/alumnidirectory/init_signup', methods=['GET', 'POST'])
    def alum_dir_init_signup(self):
        if request.method == 'POST':
            return render_template('signup/verify_identity.html')

        if request.method == 'GET':
            alumni_id = session['edit_target']
            alumnus = Alumni.query.join(Alumni.graduate_info).filter(Alumni.net_id == alumni_id).first()

            if not alumnus.graduate_info.alt_email:
                return render_template('signup/no_signup.html')
            else:
                try:
                    return self.alumni_dir_signup()
                except Exception as err:
                    print("Error sending mail: {error}".format(err=err))
                    return redirect(url_for("AlumniDirectoryApp:index"))


    @route('view/user/edit_request/signup_request/signup', methods=['GET','POST'])
    def signup_submit_docs(self):
        #target = os.path.join(os.path.dirname(os.path.abspath(__file__)), '/user_uploads')
        alumnus_name = request.form.get('alumnus_name')
        alumni_netID = request.form.get('selected_user_net_id')
        file = request.files.getlist("certificate_copy")[0]
        folder_path = "{0}/user_uploads/{1}".format(self.__APP_PATH__, alumni_netID) 

        if file and alumni_netID:
            try:
                Path(folder_path).mkdir(parents=True, exist_ok=True)
                filename = secure_filename(file.filename)
                file.save(path.join(folder_path, filename))
                alt_email = request.form["alt_email"]
                details = {
                    'alt_email': alt_email,
                    'user_name': alumnus_name
                }
                # send email to the alumnus
                notify = self.email_deg_cert(details)
                signup_alert  = self.manual_signup_alert_webmaster(details) 
            except Exception as e:
                print(e)
                print(notify)
                print(signup_alert)
                return render_template('signup/complete_signup.html', failed_process=True)

            return render_template('signup/complete_signup.html')
        else:
            return render_template('signup/complete_signup.html', faulty_documents_or_id=True)


    def manual_signup_alert_webmaster(self, request_details):
        email_title = "Alumni Directory notification: Manual signup request"
        from_name = "CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>
                        Good day, <br>
                    </p>

                    <p> 
                        This email is to inform you that {0} has submitted a request to signup for Alumni Directory. To approve/deny this request, please visit the application management portal. It can be accessed by clicking on the following <a href="{1}">link</a>.
                        <br> 
                    </p>

                    <p>
                        Best regards, <br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>
                </body>
            </html>
        """.format(
            request_details['user_name'],
            url_for("AlumniDirectoryApp:account_management_portal", _external=True)
        )
        email_body_html = email_body

        try: 
            email_dest = "webmaster-cse1@uta.edu"
            Mailer().send_mail([email_dest], email_title, email_body, email_body_html, from_name=from_name)
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))


    def email_deg_cert(self, request_details):
        email_title = "Manual Registration Request Received"
        from_name = "CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>Dear {0},<br></p>

                    <p>
                        We received your request to register for the CSE Alumni Directory. Your request will be processed shortly. You will receive an email from us regarding the next step.<br>
                    </p>

                    <p>
                        Best regards,<br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>

                </body>
            </html>
        """.format(
            request_details['user_name']
        )

        email_body_html = email_body

        try:
            email_dest = request_details['alt_email']
            Mailer().send_mail(["webmaster-cse1@uta.edu", email_dest], email_title, email_body, email_body_html, from_name=from_name)
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))


    @route('/account_docs/return_pdf/<netID>/<file_name>')
    def get_account_docs(self, netID, file_name):
        try:
            return send_file("{0}/user_uploads/{1}/{2}".format(self.__APP_PATH__, netID, file_name))
        except:
            return (" File not available. <a href={{url_for('AlumniDirectoryApp:index')}}> Return </a>" )
    
    
    @route('view/user/edit_request/signup_file_upload/signup_approve_docs/<email_token>/<netID>', methods=['POST'])  
    def signup_approve_docs(self, email_token ,netID):
        if request.form.get('optionsRadios') is not None:
            val = request.form.get('optionsRadios')
            if val == "on_record":
                return redirect(url_for("AlumniDirectoryApp:signup_approve_docs_approved", netID=netID, _email_token=email_token))
            elif val == "not_on_record":
                return redirect(url_for("AlumniDirectoryApp:signup_approve_docs_denied",netID=netID, 
                _email_token=email_token))
        return render_template('signup/verify_applicant.html', status_complete=True)


    @route('view/user/edit_request/signup_file_upload/signup_approve_docs_approved/<netID>/<_email_token>', methods=['GET','POST'])
    def signup_approve_docs_approved(self, netID, _email_token):
        session['edit_target'] = netID
        alt_email = ts.loads(_email_token, salt="email-confirm-key")

        grad_query = Graduates.query.filter(Graduates.net_id == netID).first()
        if (grad_query.alt_email != alt_email):
            grad_query.alt_email = alt_email
            db.session.commit()
        self.alumni_dir_signup()
        self.email_approve_complete_webmaster(alt_email)
        return render_template('signup/verify_applicant.html', status_complete=True)


    @route('view/user/edit_request/signup_file_upload/signup_approve_docs_denied/<netID>/<_email_token>', methods=['GET','POST'])
    def signup_approve_docs_denied(self, netID, _email_token):
        session['edit_target'] = netID
        alt_email = ts.loads(_email_token, salt="email-confirm-key")

        self.email_approval_denied_applicant(alt_email)
        return render_template('signup/verify_applicant.html', status_complete=True)


    def email_approve_complete_webmaster(self,alt_email):
        email_title = "Approval of Registeration Submitted"
        from_name="CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>Good day, <br></p>

                    <p>
                    This email is to confirm submission of the approval for the CSE@UTA Alumni Directory new user, with email: {0}<br>
                    </p>

                    <p>
                        Best regards,<br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>

                </body>
            </html>
        """.format(
            alt_email
        )

        email_body_html = email_body

        try:
            Mailer().send_mail(["webmaster-cse@uta.edu"], email_title, email_body, email_body_html, from_name=from_name)
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))


    def email_approval_denied_applicant(self,alt_email):
        email_title = "Registeration Declined"
        from_name="CSE Alumni Directory"

        email_body = """
            <html>
                <body>
                    <p>Good day, <br></p>

                    <p>
                    This email is to confirm that your request to set up an account has  been denied. Please contact the department for further information.<br>
                    </p>

                    <p>
                        Best regards,<br>
                        Department of Computer Science and Engineering<br>
                        University of Texas at Arlington
                    </p>

                </body>
            </html>
        """.format(
            alt_email
        )

        email_body_html = email_body

        try:
            Mailer().send_mail(["webmaster-cse@uta.edu", alt_email], email_title, email_body, email_body_html, from_name=from_name)
            return True
        except Exception as err:
            print("ConnectionRefusedError: {0}".format(err))
            return("Webmaster email body: \n {}".format(email_body))


    def obfuscate_email(self, email):
        split_email = email.split('@')
        split1 = split_email[0]
        avg = int(len(split1)/2)
        split1 = split1[:(len(split1 )- avg) ]
        split2 = split_email[1]     
        new_email = split1+'...@'+split2
        return new_email 


    @route('/test/inform_email')
    def inform_email(self):
        """
        Displays a page which informs user about the sent-out instruction page.
        """
        alumni_id = session['edit_target']
        alumnus = Alumni.query.join(Alumni.graduate_info).filter(Alumni.net_id == alumni_id).first()
        alumnus_details = {
            "name"      : alumnus.graduate_info.first_name + " " + alumnus.graduate_info.last_name,
            "netID"     : alumnus.graduate_info.net_id,
            "grad_yr"   : alumnus.graduate_info.graduation_year,
            "degree"    : alumnus.graduate_info.degree,
            "email"     : alumnus.social_email
        }
        if alumnus_details['email'] is not None:
            return render_template('signup/inform_signup_email.html', alumnus_email = self.obfuscate_email(alumnus_details['email']))
        else:
            return render_template('signup/inform_signup_email.html', alumnus_name=alumnus_details["name"])


    @route('/test/account_management_portal')
    def account_management_portal(self):
        return "Site in progress."

