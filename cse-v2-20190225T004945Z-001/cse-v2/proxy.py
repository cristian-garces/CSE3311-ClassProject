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
