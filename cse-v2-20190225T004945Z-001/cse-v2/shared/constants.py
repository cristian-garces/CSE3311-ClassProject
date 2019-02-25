from math import ceil
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from tzlocal import get_localzone
from subprocess import check_output as check_process_output
from os import path
from urllib.parse import urlparse, urljoin
from flask import request
from shared.json_loader import JSONLoader
import ssl

ssl.match_hostname = lambda cert, hostname: True
SHARED_DIRECTORY = path.dirname(path.realpath(__file__))
with open("{0}/.settings_key".format(SHARED_DIRECTORY), mode="r") as sk:
    SETTINGS = JSONLoader("{0}/settings.json.encrypted".format(SHARED_DIRECTORY), True, sk.readline().strip())
APP_HOST = "0.0.0.0"
NO_PHOTO = SETTINGS.get("no_photo")

if "cse.uta.edu" in path.dirname(path.abspath(__file__)):
    SRV = "prod"
    URL_PREFIX = "/v2"
    URL_FULL_PATH = "https://cse.uta.edu/v2/"
    CA_FILE = "&ssl_ca=/opt/mysql_ssl/prod/ca.pem"
    APP_PORT = 5001
elif "cse-test.uta.edu" in path.dirname(path.abspath(__file__)):
    SRV = "test"
    URL_PREFIX = "/v2-test"
    URL_FULL_PATH = "https://cse-test.uta.edu/v2-test/"
    CA_FILE = "&ssl_ca=/opt/mysql_ssl/test/ca.pem"
    APP_PORT = 5002
elif "cse-dev.uta.edu" in path.dirname(path.abspath(__file__)):
    SRV = "dev"
    URL_PREFIX = "/v2-dev"
    URL_FULL_PATH = "https://cse-dev.uta.edu/v2-dev/"
    CA_FILE = "&ssl_ca=/opt/mysql_ssl/dev/ca.pem"
    APP_PORT = 5003
elif "cse-sandbox.uta.edu" in path.dirname(path.abspath(__file__)):
    SRV = "sandbox"
    URL_PREFIX = "/v2-sandbox"
    URL_FULL_PATH = "https://cse-sandbox.uta.edu/v2-sandbox/"
    CA_FILE = "&ssl_ca=/opt/mysql_ssl/dev/ca.pem"
    APP_PORT = 5004
else:
    SRV = "localhost"
    URL_PREFIX = ""
    URL_FULL_PATH = "https://0.0.0.0:5000/"
    CA_FILE = ""
    APP_PORT = 5000


def generate_version_file(app_dir):
    if SRV == "localhost":
        app_version = check_process_output(["git", "describe", "--always", "--abbrev=8"]).decode("utf-8").strip()

        with open("{0}/APP.VERSION".format(app_dir), mode="w") as app_version_file:
            app_version_file.write(app_version)

        return app_version
    else:
        with open("{0}/APP.VERSION".format(app_dir), mode="r") as app_version_file:
            return app_version_file.readline().strip()


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_log_time():
    return datetime.now().strftime("%a %Y-%m-%d %H:%M:%S.%f"), get_localzone().zone


def str_2_bool(s, default=False):
    try:
        if s.lower().strip() == "true" or int(s) >= 1:
            return True
    except ValueError:
        pass

    return default


def pikaday_to_datetime(d, default=None):
    if d:
        return datetime.strptime(d, '%a %b %d %Y')
    return default


def paginate_it(current_index=None, num_to_display=5, num_links=5, num_items=None):
    if current_index is not None and num_items is not None:
        current_index = int(current_index)
        num_links_half = ceil(num_links / 2) - 1

        if (current_index - num_to_display) < 0:
            previous_index = None
        else:
            previous_index = current_index - num_to_display

        if (current_index + num_to_display) >= num_items:
            next_index = None
        else:
            next_index = current_index + num_to_display

        if (ceil(current_index / num_to_display) - num_links_half) < 0:
            first_page = 0
        elif ((ceil(current_index / num_to_display) + 1) + num_links_half) >= ceil(num_items / num_to_display):
            first_page = ceil((current_index / num_to_display) - (num_links - (ceil(num_items / num_to_display) - ceil(current_index / num_to_display))))
            if first_page < 0:
                first_page = 0
        else:
            first_page = ceil(current_index / num_to_display) - num_links_half

        if ((ceil(current_index / num_to_display) + 1) + num_links_half) >= ceil(num_items / num_to_display):
            last_page = ceil(num_items / num_to_display)
        elif (ceil(current_index / num_to_display) - num_links_half) <= 0:
            last_page = num_links
            if last_page >= ceil(num_items / num_to_display):
                last_page = ceil(num_items / num_to_display)
        else:
            last_page = (ceil(current_index / num_to_display) + 1) + num_links_half

        return {"current_index": current_index/num_to_display, "previous_index": previous_index, "first_page": first_page,
                "last_page": last_page, "next_index": next_index, "number_displayed": num_to_display}
    print("Error: current_index and num_items must be defined.")


def allowed_file(filename=None, extensions=None):
    if filename and extensions:
        return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in extensions)
    return False


def date_expired(start_date=None, end_date=None):
    if start_date:
        end_date = end_date or datetime.now()
        delta = relativedelta(parse(start_date), end_date)

        return delta.years + delta.months + delta.days + delta.hours + delta.minutes + delta.seconds < 0
    return False
