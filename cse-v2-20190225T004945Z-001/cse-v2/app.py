import proxy
from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from shared.constants import SETTINGS, APP_HOST, APP_PORT, SRV, URL_PREFIX
# ############################################################################################
# ######################### Import Applications to be Mounted Here ###########################
# ############################################################################################
from mavapps.app import app as mavapps
from alumni_directory.app import app as alumni_directory
# ############################################################################################
# ############################################################################################
# ############################################################################################


app = Flask(__name__)

if SRV != "localhost":
    app.config["SESSION_COOKIE_SECURE"] = True
app.config["APPLICATION_ROOT"] = URL_PREFIX
app.config["PREFERRED_URL_SCHEME"] = "https"

app.wsgi_app = proxy.ReverseProxied(DispatcherMiddleware(NotFound(), {
    "/mavapps": mavapps,
    "/alumni_directory": alumni_directory
}), script_name=URL_PREFIX)

app.secret_key = SETTINGS.get("app_secret")


if __name__ == "__main__":
    ssl_context = ("/opt/www/certs/server.crt", "/opt/www/certs/server.key") if SRV != "localhost" else ("./0.0.0.0.crt", "./0.0.0.0.key")
    app.run(host=APP_HOST, port=APP_PORT, threaded=True, debug=True, ssl_context=ssl_context)
