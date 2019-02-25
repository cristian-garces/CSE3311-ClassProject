from socket import gaierror
import smtplib
import traceback
from email.headerregistry import Address
from email.message import EmailMessage
from shared.constants import SRV


class MissingEmailFieldError(Exception):
    def __init__(self):
        default_message = "Please make sure the recipient e-mails, e-mail subject, and e-mail body are properly set."
        super().__init__(default_message)


class InvalidToEmailsError(Exception):
    def __init__(self):
        default_message = "Please make sure the recipient e-mails are properly formatted (i.e., a list of e-mails or list of name and e-mail pairs)."
        super().__init__(default_message)


class InvalidEmailFormatError(Exception):
    def __init__(self):
        default_message = "Please make sure all the e-mails are properly formatted (i.e., user@host.com)."
        super().__init__(default_message)


class Mailer:
    def __init__(self, server="localhost"):
        self.server = server

    @staticmethod
    def process_recipient_emails(recipient_emails):
        processed_recipient_emails = []

        for email in recipient_emails:
            try:
                if isinstance(email, list) and len(email) == 2:
                    processed_recipient_emails.append(Address(email[0], email[1].split("@")[0], email[1].split("@")[1]))
                elif isinstance(email, str):
                    processed_recipient_emails.append(Address(email, email.split("@")[0], email.split("@")[1]))
                else:
                    raise InvalidToEmailsError
            except Exception:
                raise InvalidEmailFormatError

        return tuple(processed_recipient_emails)

    def send_mail(self, recipient_emails=None, email_subject=None, email_body=None, email_body_html=None, from_email="webmaster-cse@uta.edu", from_name="CSE Webmaster"):
        if email_subject and email_body and recipient_emails:
            if len(from_email.split("@")) == 2:
                message = EmailMessage()
                message["Subject"] = email_subject
                message["From"] = Address(from_name, from_email.split("@")[0], from_email.split("@")[1])
                message["To"] = self.process_recipient_emails(recipient_emails)
                message.set_content(email_body)
                if email_body_html:
                    message.add_alternative(email_body_html, subtype="html")

                try:
                    with smtplib.SMTP(self.server) as email_server:
                        email_server.send_message(message)
                except Exception as e:
                    if (isinstance(e, ConnectionRefusedError) or isinstance(e, gaierror)) and SRV == "localhost":
                        print(message.as_string())
                    else:
                        print("Error:\n{0}\n{1}\n".format(e, traceback.format_exc()))
            else:
                raise InvalidEmailFormatError
        else:
            raise MissingEmailFieldError
