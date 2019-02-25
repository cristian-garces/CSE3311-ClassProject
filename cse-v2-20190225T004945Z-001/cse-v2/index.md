# Developing Web Apps for UTA CSE

1. [Introduction](#introduction)
   - [Environment](#environment)
   - [Requirements](#requirements)
   - [Recommendations](#recommendations)
2. [Authentication](#authentication)
3. [Endpoint programming](#endpoint-programming)
   - [Creating an endpoint](#creating-an-endpoint)
   - [Login protection](#login-protection)
   - [POST, GET, etc. requests](#post-get-etc-requests)
   - [Creating templates](#creating-templates)
4. [Wrapping it up](#wrapping-it-up)
   - [Summary](#summary)
   - [Conclusion](#conclusion)

## Introduction
### Environment

All web applications should be developed in a Python 3.6.X environment, your code should be neat and require minor adjustments when upgrading to a minor version within the same major version release (i.e., Python 3.5.0 to 3.6.0). Our goal is to program in such a way that even when a major release comes, we can port our code to it with very minor tweaks.

Code will be managed mainly through GitHub and any changes will be pushed to the repository and then pulled from the repository on the server. Development should be done locally, unless circumstances make it impossible to do so.
		
You should be familiar with Python, HTML5, CSS3, Jinja2, Bootstrap 4, and JavaScript (jQuery, AJAX, and miscellaneous libraries as you develop).

Before you get started make a simple “Hello World” app with Flask and try to incorporate some templating techniques using Jinja2. You’ll need to understand the basic workflow of these tools to follow the rest of the documentation closely.

#### Can I Use Windows?
It's possible to develop in Windows if you use the [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/install-win10). The following steps are for a Windows machine running Ubuntu with the WSL.
```sh
sudo apt-get update
sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
sudo apt-get install libmysqlclient-dev
sudo apt-get install gcc
sudo pip3 install -r requirements.txt
```

### Requirements
The [requirements.txt](./requirements.txt) contains all the requirements that need to be installed via `pip` with `pip install -r requirements.txt`. You might need some extra system packages like open-ldap development packages or mysql-client development packages as these have some files the pip packages require for a successful installation.

### Recommendations
There are several editors that can help you develop, and you might have a favorite one (e.g., Sublime Text, Visual Studio Code, Atom, Notepad++, etc.). However, there is something to be said of an integrated development environment like PyCharm. This IDE, for example, gives you all the commodities of a good IDE and provides an excellent debugger which allows you to visualize your variables, their contents, and travel the path of the code in real time. Using it, or any IDE, is not required but it is likely to make your life easier.

If you are unfamiliar with Git or simply want an easy to use GUI, I recommend either the free desktop client from GitHub (https://desktop.github.com/), or my personal go to (which sadly isn’t free) GitKraken (https://www.gitkraken.com/). Alternatively, you can install git on your machine and issue commands through the command prompt/terminal. That being said when you are working on the server you should at least know these basic commands.

- `git pull`
  - How you pull changes from the GitHub repository.
- `git commit . -m “Your commit message here [REQUIRED]”`
  - How you commit all local changes locally.
  - Your commit message should describe the changes you made, so as others can quickly understand what this change is doing.
- `git push origin master`
  - How you push your committed local changes to the GitHub repository.

## Authentication
Authentication for apps running in Python has already been implemented with [LDAP](https://www.ldap.com/ldap-dns-and-rdns), the classes handling the authentication can be found in ldap_auth.py and login_handler.py. The following is passed to an instance of the class within ldap_auth.py which is used in login_handlers.py:

- The LDAP server
  - ldaps://some-ldap-server
- The base user distinguished name (dn)
  - cn=cn_name,dc=dc_name,dc=dc_name
- The user dn
  - dc=dc_name,dc=dc_name
- The username for the user
  - Provided by the user through the login page
- The password for the user
  - Provided by the user through the login page
- A dictionary containing all users with developer privileges
  - `{“user1”: True,  “user2”: True, … }`

In the authenticate method (in ldap_auth.py), we connect to the LDAP server using the credentials the the user gave us. If the credentials are not valid an error is thrown and we handle it by letting the user know the credentials were invalid via a notification on the webpage.

## Endpoint programming
### Creating an endpoint
In order to create an endpoint you need to decorate a method with the @app.route(). You will pass the endpoint as a string to that decorator. The “/” will be routed to the root of the application, and is already defined so your endpoints will be subdomains of that.

```python
@app.route(“/my_app_endpoint”)
def my_app_function():
	return render_template("my_app.html")
```

### Login protection
In order to password protect any of your routes/endpoints you can use the @login_required decorator after the definition of your route/endpoint.

```python
@app.route(“/my_app_endpoint”)
@login_required
def my_app_function():
	return render_template("my_app.html")
```

### POST, GET, etc. requests
Sometimes you’ll want to return data to an AJAX request without reloading the page. To do so you’ll need to submit a POST/GET request through an AJAX call and process the response in the success function of the AJAX call. Below is an example detailing a POST request and subsequent response from the server.

In this example we are making an AJAX call to the route “/my_app_endpoint”, this particular route also serves as a normal webpage so the AJAX call we are making to it is specifically a POST request. In this POST request we are sending the the arguments A, B, C as a JSON object which we retrieve in the Python code using the `request.json()` method and referencing the name of the argument we want. Essentially, the JSON object gets mapped to a Python dictionary. We then send back a JSON object to the AJAX call and from within the success function of the AJAX call we reference the Python dictionary keys as attributes of the JSON response object. Finally, if the request isn’t a POST request, the Python code simply renders the HTML for that page, so in this way we decouple GET and POST requests to handle each as we wish.

```javascript
$("#my-ajax-form").submit(function (e) {
	$.ajax({
		type: “POST”,
		contentType: “application/json;charset=UTF-8”,
		data: JSON.stringify({A: "Test", B: 0, C: false, null, "\t"),
		url: “/my_app_endpoint”,
		dataType: "json",
		success: function (data) {
			if(data.a) {
			    console.log(data.b);
			}
			else {
				console.log(data.c);
			}
		}
	});
});
```

```python
@app.route(“/my_app_endpoint”, methods=[“GET”, “POST”])
def my_app_function():
	if request.method == “POST”:
	A = request.json[“A”]
	B = request.json[“B”]
	C = request.json[“C”]

	print(A, B, C)

	return jsonify({"a": False, "b": “Hello”, "c": “world.”})

	return render_template("my_app.html")
```

## Creating templates
You’ll notice that in the example Python functions above we reference a method called `render_template()` with the name of an HTML document passed as an argument. Those HTML documents are templates, and they are rendered dynamically upon request and allow you, the programmer, to determine what content you want to show a user based on a slew of variables (e.g., who they are, the time of day, etc.). This is the power of the Jinja2 templating engine. A template is basically a regular HTML document with some special tags that allow the templating engine to programatically render the HTML. Take a look at the code below:

```django
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>My App</title>
</head>
<body>
	{{ '{% for user in users ' }}%}
	<p>{{ '{{ user ' }}}}<p>
	{{ '{% endfor ' }}%}
</body>
</html>
```

In the example above we have passed a variable called users to the template by calling the render_template function like so: `render_template(“example.html”, users=my_local_python_var)`. In doing so we have passed a list of users which we iterate through to dynamically generate content on the page each time it is rendered in a web browser.

When developing for the CSE department, you should try to make use of the base.html that is provided and extend that. When you extend the base HTML file, you are importing that file and over-writing sections as you see fit. So for example, an app you might develop might look like so:

```django
{{ '{% extends "base.html" ' }}%}
{{ '{% block title ' }}%}CSE Apps Login{{ '{% endblock ' }}%}
{{ '{% block custom_css ' }}%}
	<link rel="stylesheet" href="{{ '{{ url_for("static", filename="css/my.css") ' }}}}">
{{ '{% endblock ' }}%}
{{ '{% block navbar ' }}%}{{ '{{ include "navbar.html" ' }}}}{{ '{% endblock ' }}%}
{{ '{% block content ' }}%}My first app!{{ '{% endblock ' }}%}
{{ '{% block custom_js_import ' }}%}
<script src="{{ '{{ url_for("static", filename="js/my_app.js") ' }}}}"></script>
{{ '{% endblock ' }}%}
```

Each piece of HTML/text that is surrounded by a `{{ '{% block block_name ' }}%}` HTML/text here `{{ '{% endblock ' }}%}` is something that you can overwrite from the base.html file. You’ll see that we start by stating `{{ '{% extends "base.html" ' }}%}`, which lets the templating engine know we will use that file as our scaffolding. Get yourself familiar with the “base.html” file so you know what sections you can overwrite and understand the structure of pages. You might also notice statements like, `{{ '{{ include "some_file.html" ' }}}}` which import that file, in its entirety to that portion of the current HTML file. Finally, statements like `{{ '{{ url_for("static", filename="folder/file.ext") ' }}}}` are the standard way of reference static files (i.e., .css, .js, .jpg, .png, etc.) in the HTML code. All static files should be stored in the “static” folder in the appropriate sub-folder.

## Wrapping it up
### Summary
You’ll need to make use of everything that has been mentioned above and many more things to create functional and robust apps. You should always program with the next developer in mind. You won’t always be there to maintain your app, at some point (even before you graduate) someone might have to make changes or fix something in an application you wrote. With that in mind, we are trying to make it as easy as possible for any developer to pick up an app and understand how it works fairly quickly. We do this by adhering to coding standards, doing things in “best-practices” types of ways, and writing robust code that isn’t held together with “spit and glue.”

### Conclusion
There are many things that weren’t covered in this brief documentation of getting started with programming web apps for the CSE department. You’ll have to learn and pick up many things along the way. The web is your best resource and never shy away from asking a fellow developer as they may have already solved similar issues to the one you are facing and could provide you with time saving insight.
