<h1 align="center">Configuring the CSE Dev, Test & Production Servers to Run MavApps</h1>

## Table of Contents
1. [Server Preparation](#server-preparation)
2. [Installing Dependencies](#installing-dependencies)
3. [Configuring Apache (httpd.conf)](#configuring-apache-httpdconf)
   - [Restarting the Apache Server](#restarting-the-apache-server--locating-server-logs)
4. [Starting, Stopping and Managing the App](#starting-stopping-and-managing-the-app)
   - [Verifying the Application](#verifying-the-application)
   - [Launching the Application](#launching-the-application)
   - [Killing the Application](#killing-the-application)
5. [Appendix A (proxy\.py)](#appendix-a-proxypy)

## Preface
The following instructions make the assumption that the servers in question are running RedHat Enterprise Linux 6 (el6 or rhel6), if this is not the case then the general workflow of getting the servers prepped should be the same, but you may need to find the appropriate packages for your distribution and install them with that distributions package manager or build from source if necessary. To check what distro or version of linux you are on you can try using one of the following commands: `cat /etc/*-release` or `uname -a`.

## Server Preparation
Make sure the /tmp directory does not have the noexec flag by running:
`mount | grep noexec`
If something like `/dev/mapper/disk1-LogVol02 on /tmp type ext4 (rw,noexec,nosuid,nodev)` shows up where `on /tmp` and `noexec` are present, then you must disable this flag as instructed below and re-enable it once you are done.
- Disable the noexec flag while installing dependencies by:
	`mount -o remount,exec /tmp`
- Then re-enable the flag when you are done installing dependencies by:
	`mount -o remount,noexec /tmp`

## Installing Dependencies
The application relies on some libraries and programs that may not be installed on the server. Run the following commands to make sure that the server has everything the application needs to be setup successfully. You may need to run these with sudo or as root.
```sh
yum -y update
yum -y install yum-utils
yum -y groupinstall development
yum install httpd-devel
yum install openldap-devel
yum install mysql mysql-devel
```
If Python 3.6 isn’t installed:
```sh
yum -y install https://rhel6.iuscommunity.org/ius-release.rpm
yum -y install python36u
yum -y install python36u-devel
```

The following list of Python dependencies should be (kept) updated and you can install them one-by-one using the commands below or install them via the **requirements.txt** in the repository by running: `pip3.6 install -r requirements.txt`
```sh
pip3.6 install -U setuptools
pip3.6 install -U wheel
pip3.6 install requests
pip3.6 install tzlocal
pip3.6 install simple-crypt
pip3.6 install python-ldap
pip3.6 install mysqlclient
pip3.6 install pymysql
pip3.6 install python-dateutil
pip3.6 install fpdf
pip3.6 install fuzzywuzzy
pip3.6 install python-Levenshtein
pip3.6 install sqlalchemy
pip3.6 install Flask
pip3.6 install flask-classful
pip3.6 install flask-login
pip3.6 install Flask-SQLAlchemy
pip3.6 install rauth
pip3.6 install oauthlib
pip3.6 install flask-dance
pip3.6 install itsdangerous
pip3.6 install blinker
pip3.6 install gunicorn
```

### Installing runit (only on the Production Server)
To install runit on the production server simply download the [rpm package](https://packagecloud.io/.../runit-2.1.2-1.el6.x86_64.rpm)<sup>1</sup> or transfer it via sftp to the production server into the **/tmp/ directory**. Then just execute: `yum install runit-2.1.2-1.el6.x86_64.rpm`.

<sub>1. This package is for RedHat Enterprise Linux 6,i.e., el6 or rhel6, so if you are on a different version of RedHat or a different distro altogether this package probably won't work for you.</sub>

To make sure that runit starts on it’s own make sure that a file called **runsvdir.conf** or **runsvdir-start.conf** is located in **/etc/init/**. The contents of this file should be:
```sh
# for runit - manage /usr/sbin/runsvdir-start
start on runlevel [2345]
stop on runlevel [^2345]
normal exit 0 111
respawn
exec /sbin/runsvdir-start
```
It should be chmod’ed to 644 as well. Then make sure a symlink exists between **/sbin/runsvdir-start** and **/etc/init.d/runsvdir-start** if it doesn’t simply execute: `ln -s /sbin/runsvdir-start /etc/init.d/runsvdir-start`.

Finally, make sure that the service has been started by issuing `start runsvdir` or `start runsvdir-start`, depending on the filename in **/etc/init/**. Runit services can be managed with [**sv**](http://smarden.org/runit/sv.8.html)

## Configuring Apache (httpd.conf)
The configuration file is located at: **/opt/rh/httpd24/root/etc/httpd/conf/httpd.conf**

Add the following line(s) to the bottom of the file:
- On the Dev, Test, and Production servers <sup>2</sup>
    ```sh
    SSLProxyEngine on
    SSLProxyCheckPeerCN off
    RewriteEngine On
    
    RewriteCond %{HTTPS} !=on
    RewriteRule ^/v2(.*) https://%{SERVER_NAME}/v2$1 [R,L]
    ```
    <sub>2. We need `SSLProxyCheckPeerCN off` because we use the server's key and certificate files to encrypt traffic going through Gunicorn and the common name (CN) for the server isn't localhost so this causes an error.</sub>
    
- On the Sandbox, Dev and Test servers <sup>3</sup>
    ```sh
    ProxyPass /v2-sandbox https://localhost:5004
    ProxyPassReverse /v2-sandbox/ https://cse-dev.uta.edu/v2-sandbox/
    
    ProxyPass /v2-dev https://localhost:5003
    ProxyPassReverse /v2-dev/ https://cse-dev.uta.edu/v2-dev/

    ProxyPass /v2-test https://localhost:5002
    ProxyPassReverse /v2-test/ https://cse-test.uta.edu/v2-test/
    ```
    <sub>3. The endpoints for the dev and test servers need to be different (i.e., mavapps-dev and mavapps-test) due to the fact that both the dev and test "servers" are actually on the same physical/virtual server. This causes weird behavior when both endpoints have the same name (e.g., `https://cse-dev.uta.edu/mavapps/` and `https://cse-test.uta.edu/mavapps/`).</sub>
- On the Production server <sup>4</sup>

    ```sh
    ProxyPass /v2 https://localhost:5001
    ProxyPassReverse /v2/ https://cse.uta.edu/v2/
    ```
    <sub>4. The first two rules are necessary due to some weird behavior caused by running the application on a route that matches the folder name (i.e., mavapps). Without it static files have to be referenced by including "mavapps" twice in the route (e.g., `https://cse.uta.edu/mavapps/mavapps/static/assets/main/erb.jpg`) which breaks some logic. With those rules in place the aforementioned route still works, but we can also use routes that only use "mavapps" once (e.g., `https://cse.uta.edu/mavapps/static/assets/main/erb.jpg`)</sub>
    
Where **/myapp_route** can be any route you want to serve requests to your app, in this case to reach the app (if it were hosted on **`https://cse.uta.edu`**) one would go to **`https://cse.uta.edu/myapp_route`** in their browser. The port on which the app will listen on localhost can be anything, you set that once you run the gunicorn command.

### Specifying Different Routes for Certain Apps
If you want to specify a different route for a particular app, for example:
You have an app that is run at the endpoint: **`https://localhost:5001/my_lonely_app/`**. And you don’t want this app to be a part of **/mavapps** (i.e., **`https://cse.uta.edu/mavapps/my_lonely_app/`**), but instead be found at **/my_lonely_app** (i.e., **`https://cse.uta.edu/my_lonely_app/`**). Then you’d need the following rules<sup>5</sup>:
```sh
ProxyPass /mavapps/my_lonely_app/ !
ProxyPass /my_lonely_app/ https://localhost:5001/my_lonely_app/
ProxyPassReverse /my_lonely_app/ https://cse.uta.edu/my_lonely_app/
Redirect /my_lonely_app https://cse.uta.edu/my_lonely_app/
```
<sub>5. The last, "Redirect", rule re-routes calls with a trailing slash attached. That is `https://cse.uta.edu/my_app_route` becomes `https://cse.uta.edu/my_app_route/`. Notice the "/" has been appended to the redirected route. This is important as apps are proxy-ed to specific routes and going to the first link would result in a "Not Found" error.</sub>

The first rule tells apache to not proxy anything sent to **/mavapps/my_lonely_app/** which is what would normally happen since all Gunicorn applications live under the route **/mavapps/**, so we basically exclude this application from that rule. Then the next set of rules tell apache to route any requests being sent to the server at route **/my_lonely_app/** (i.e., **`https://cse.uta.edu/my_lonely_app/`**) to our app that is hosted by Gunicorn on **`https://localhost:5001/`**.

### Restarting the Apache Server & Locating Server Logs
To restart the server so that any changes you made in the httpd.conf are propagated, issue the following command with sudo or as root: `service httpd24-httpd reload`
Server logs can be found at: **/var/log/httpd/**

## Starting, Stopping and Managing the App

### Verifying the Application
We need to make sure an import is present in the main **app.py**:
```python
import proxy
```
The main **app.py** file should look something like:
```python
import proxy
from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from shared.constants import APP_HOST, APP_PORT, SRV, URL_PREFIX

from app1.app import app as app1
from app2.app import app as app2
⋮
from app_n.app import app as app_n

app = Flask(__name__)

if SRV != "localhost":
    app.config["SESSION_COOKIE_SECURE"] = True
app.config["APPLICATION_ROOT"] = URL_PREFIX
app.config["PREFERRED_URL_SCHEME"] = "https"

app.wsgi_app = proxy.ReverseProxied(DispatcherMiddleware(NotFound(), {
    "/app1": app1,
    "/app2": app2,
    ⋮
    "/app_n": app_n
}), script_name=URL_PREFIX)

app.secret_key = 'P"sVt*Hqtz*5;!*7A2<h?;t+;IoQWV'


if __name__ == "__main__":
    ssl_context = ("/opt/www/certs/server.crt", "/opt/www/certs/server.key") if SRV != "localhost" else None
    app.run(host=APP_HOST, port=APP_PORT, threaded=True, debug=True, ssl_context=ssl_context)
```
There might be other things inside the function (builders, database instantiations, etc.), but the important parts are above. We need to make sure that it returns the Flask app instance and and that the **script_name** matches the url endpoint where the app will live (e.g., **cse.uta.edu/my_app**). Finally, we need to add the file **proxy.py** to the same directory where **app.py** is in. The contents of that file are at the bottom of these instructions in **Appendix A**.

### Launching the Application
Here we specify the port that localhost will listen on, just make sure that this value and the one in the httpd.conf match. You can read in detail about the other options at: http://docs.gunicorn.org/en/stable/settings.html

##### Server key and certificate files
If the **server.key** or **server.crt** files are expired, then you need to update the versions in the folder **/opt/www/certs/** to the new ones. These are found in **/opt/httpd-node-local/conf/ssl.crt/server.crt** and **/opt/httpd-node-local/conf/ssl.key/server.key**

To update these, simply delete the files in **/opt/www/certs/** and then copy the **server.key** and **server.crt** files from the two locations mentioned above into the **/opt/www/certs/**. After copying them don’t forget to change their group to csewebdev and chmod them to 440 as well.

If the files are no longer in the folders mentioned above, note that you are required to be root to access them, then you need to look in the httpd.conf for references to the new locations of the certificate and key files or ask OIT.

##### On the dev and test servers
On dev and test the scripts **start-servers.sh** and **kill-servers.sh** in the **mavapps** folder can take care of starting and stopping the servers. If you want to see any output (e.g., code execution traces) for debugging you can also just run the commands below, from the appropriate mavapps directory, for the dev and test server, respectively.

- For Dev
`gunicorn -k gthread --threads 5 -w 7 -t 180 --max-requests 250 --reload --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5003 'app:app' >> server.log & disown`
or
`python3.6 app.py`

- For Test
`gunicorn -k gthread --threads 5 -w 7 -t 180 --max-requests 250 --reload --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5002 'app:app' >> server.log & disown`
or
`python3.6 app.py`

##### On the production server
The production server has a **runit** service that keeps the applications alive and makes sure they are initiated on a system reboot. If you have already installed the runit package, as instructed above, and need to create a service to keep the applications alive then simply follow the directions provided in the [gunicorn documentation](http://docs.gunicorn.org/en/stable/deploy.html#runit). Once this is done the application can be started using `sudo sv start csev2` or restarted using `sudo sv restart csev2`

The service file should look something like:
```sh
#!/bin/sh

# For more info see: http://docs.gunicorn.org/en/stable/deploy.html#runit

GUNICORN=/usr/bin/gunicorn
ROOT=/opt/www/cse.uta.edu/cse-v2
PID=/var/run/gunicorn.pid

APP=main:application

if [ -f $PID ]; then rm $PID; fi

cd $ROOT
exec $GUNICORN -k gthread --threads 8 -w 12 -t 180 --max-requests 250 --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5001 'app:app' >> /opt/www/cse.uta.edu/cse-v2/server.log
```

Alternatively, if you need to manually start the applications you can issue the following command from the mavapps directory:

`gunicorn -k gthread --threads 8 -w 12 -t 180 --max-requests 250 --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5001 'app:app' >> server.log & disown`
or
`python3.6 app.py`

The `--reload` flag in the manual commands for the dev and test servers enables gunicorn to reload on source code changes. Since production should be stable we want to manually restart this ourselves. Documentation for Gunicorn also states the `--reload` feature is intended **only for development**.

### Killing the Application
On the dev and test servers the **kill-servers.sh** script can take care of killing either of these. On the production server, if you are using **runit**, you can use `sudo sv stop mavapps`. More generally the steps below can be used on the dev, test, and production servers to kill the applications as well.

- If you know the pid of the parent process just do (where PID is the process ID for the process you want to kill, this should be an integer):
`kill PID`
- If you don’t know then (where PORT_NUMBER is the port number for the Gunicorn instance you want to kill — 5001 for prod, 5002 for test, and 5003 for dev):
`kill $(ps -aux | grep gunicorn | grep PORT_NUMBER | grep ' [RS]\{1\}+\? ' | awk '{print $2}')`
- If that doesn’t work, search for all  pids with:
`ps -aux | grep gunicorn`
then kill the parent process (usually the pid with the smallest number). Worst case, you’ll have to kill all the gunicorn processes one by one.

## Appendix A (proxy\.py)
```python
class ReverseProxied(object):
    """
    sources: http://blog.macuyiko.com/post/2016/fixing-flask-url_for-when-behind-mod_proxy.html
             https://raw.githubusercontent.com/wilbertom/flask-reverse-proxy/master/flask_reverse_proxy/__init__.py
    """
    def __init__(self, app, script_name=None):
        """
        Initialize the class and all the related class variables.

        :param app: App to be fixed.
        :param script_name: Script to be used to setup the environment
        """
        self.app = app
        self.script_name = script_name

    def __call__(self, environ, start_response):
        """
        Set up an app to work appropriately when behind mod proxy.

        :param environ: Callers environment.
        :param start_response: Response upon starting.
        :return: Properly configured app.
        """
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '') or self.script_name

        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')

            if path_info and path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        server = environ.get('HTTP_X_FORWARDED_SERVER_CUSTOM', environ.get('HTTP_X_FORWARDED_SERVER', ''))

        if server:
            environ['HTTP_HOST'] = server

        # scheme = environ.get('HTTP_X_SCHEME', '')
        scheme = "https"

        if scheme:
            environ['wsgi.url_scheme'] = scheme

        return self.app(environ, start_response)

```
