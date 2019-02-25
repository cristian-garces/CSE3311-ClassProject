import requests
import json
from os import path
from json import load
from fuzzywuzzy import fuzz
from flask import jsonify
from flask_login import current_user
from flask_classful import FlaskView, route
from mavapps.constants import verify_roles, cse_referrer_required
from mavapps.apps.main.models import Users, Alumni, Graduates, db


class APIApp(FlaskView):
    decorators = [cse_referrer_required()]
    excluded_methods = ["process_query_results", "process_alumni_query_results"]
    route_base = "/{0}/".format(path.dirname(path.realpath(__file__)).split("/")[-1])

    def __init__(self):
        self.__APP_PATH__ = path.dirname(path.realpath(__file__))
        self.__APP_DIR__ = self.__APP_PATH__.split("/")[-1]

    @route('/search/site/<user_query>')
    def search_site(self, user_query):
        user_query = user_query.lower().strip()
        search_results = []
        with open("{0}/site-wide-search.json".format(self.__APP_PATH__), mode="r") as search_json:
            search_dict = load(search_json)

        for k in search_dict:
            for keyword in search_dict[k]["keywords"]:
                if fuzz.partial_ratio(user_query, keyword) > 80:
                    if ("ANY" in search_dict[k]["access_roles"] or verify_roles(search_dict[k]["access_roles"])) and not (search_dict[k]["must_login"] and current_user.is_authenticated is False):
                        search_results.append({"title": " ".join(word.capitalize() for word in k.split("_")),
                                               "description": search_dict[k]["description"],
                                               "url": search_dict[k]["url"]})
                    break

        return jsonify(search_results)

    @route("/search/places/city/<user_query>")
    def search_places(self, user_query):
        headers = {'X-Algolia-Application-Id': 'plZH7226BG8X',
                   'X-Algolia-API-Key': '2cfe6a48727d041d4bc4b0c77ee56163'}
        payload = json.dumps({'query': user_query})
        res = requests.post('https://places-dsn.algolia.net/1/places/query', data=payload, headers=headers)
        res = json.loads(res.content, encoding="utf-32")
        results = []

        for hit in res["hits"]:
            country = hit["country"].get("en", hit["country"].get("default", "N/A")).strip()
            state = hit.get("administrative", ["N/A"])[0].strip()
            city = hit["locale_names"].get("en", hit["locale_names"].get("default", "N/A"))[0].strip()

            if hit["is_city"] and country != "" and state != "" and city != "":
                results.append({"country": country,
                                "state": state,
                                "city": city})

        return jsonify(results)

    @route('/search/alumni/name/<name>')
    def search_alumni_name(self, name):
        query_results = []
        query_results += Alumni.query.join(Alumni.graduate_info).filter(db.func.soundex(db.func.concat(Graduates.first_name, " ", Graduates.middle_name, " ", Graduates.last_name)).like(db.func.soundex(name)) |
                                             db.func.soundex(db.func.concat(Graduates.first_name, " ", Graduates.last_name)).like(db.func.soundex(name))).distinct().all()

        for q in name.split():
            query_results += Alumni.query.join(Alumni.graduate_info).filter(db.func.soundex(Graduates.first_name).like(db.func.soundex(q.strip())) |
                                                                            db.func.soundex(Graduates.middle_name).like(db.func.soundex(q.strip())) |
                                                                            db.func.soundex(Graduates.last_name).like(db.func.soundex(q.strip())) |
                                                                            Graduates.first_name.like("{0}%".format(q.strip())) |
                                                                            Graduates.last_name.like("{0}%".format(q.strip()))).distinct().all()

        return jsonify(sorted(self.process_alumni_query_results(query_results), key=lambda res: (fuzz.ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 10) + (fuzz.token_set_ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.partial_ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.ratio(name.lower(), "{0} {0}".format(res["first_name"], res["last_name"]).lower()) * 10) + (fuzz.ratio(name.lower(), "{0}".format(res["first_name"]).lower()) * 5) + (fuzz.ratio(name.lower(), "{0}".format(res["last_name"]).lower()) * 5), reverse=True))

    @route('/search/user/name/<name>')
    def search_user_name(self, name):
        query_results = []
        query_results += Users.query.filter(db.func.soundex(db.func.concat(Users.first_name, " ", Users.middle_name, " ", Users.last_name)).like(db.func.soundex(name)) |
                                            db.func.soundex(db.func.concat(Users.first_name, " ", Users.last_name)).like(db.func.soundex(name))).distinct().all()

        for q in name.split():
            query_results += Users.query.filter(db.func.soundex(Users.first_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.middle_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.last_name).like(db.func.soundex(q.strip())) |
                                                Users.first_name.like("{0}%".format(q.strip())) |
                                                Users.last_name.like("{0}%".format(q.strip()))).distinct().all()

            return jsonify(sorted(self.process_query_results(query_results), key=lambda res: (fuzz.ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 10) + (fuzz.token_set_ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.partial_ratio(name.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.ratio(name.lower(), "{0} {0}".format(res["first_name"], res["last_name"]).lower()) * 10) + (fuzz.ratio(name.lower(), "{0}".format(res["first_name"]).lower()) * 5) + (fuzz.ratio(name.lower(), "{0}".format(res["last_name"]).lower()) * 5), reverse=True))

    @route('/search/user/name/first/<first_name>')
    def search_user_first_name(self, first_name):
        query_results = Users.query.filter(db.func.soundex(db.func.concat(Users.first_name)).like(db.func.soundex(first_name)) |
                                           Users.first_name.like("{0}%".format(first_name.strip()))).distinct().all()

        return jsonify(sorted(self.process_query_results(query_results), key=lambda res: fuzz.ratio(first_name.lower(), "".format(res["first_name"]).lower()), reverse=True))

    @route('/search/user/name/last/<last_name>')
    def search_user_last_name(self, last_name):
        query_results = Users.query.filter(db.func.soundex(db.func.concat(Users.last_name)).like(db.func.soundex(last_name)) |
                                           Users.last_name.like("{0}%".format(last_name.strip()))).distinct().all()

        return jsonify(sorted(self.process_query_results(query_results), key=lambda res: fuzz.ratio(last_name.lower(), "".format(res["last_name"]).lower()), reverse=True))

    @route('/search/user/name/and/uta_id/<query>')
    def search_user_name_uta_id(self, query):
        query_results = []
        query_results += Users.query.filter(db.func.soundex(db.func.concat(Users.first_name, " ", Users.middle_name, " ", Users.last_name)).like(db.func.soundex(query)) |
                                            db.func.soundex(db.func.concat(Users.first_name, " ", Users.last_name)).like(db.func.soundex(query))).distinct().all()

        for q in query.split():
            query_results += Users.query.filter(db.func.soundex(Users.first_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.middle_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.last_name).like(db.func.soundex(q.strip())) |
                                                Users.first_name.like("{0}%".format(q.strip())) |
                                                Users.last_name.like("{0}%".format(q.strip())) |
                                                Users.uta_id.like("{0}%".format(q.strip()))).distinct().all()

        return jsonify(sorted(self.process_query_results(query_results), key=lambda res: (fuzz.ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 10) + (fuzz.token_set_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.partial_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.ratio(query.lower(), "{0} {0}".format(res["first_name"], res["last_name"]).lower()) * 10) + (fuzz.ratio(query.lower(), "{0}".format(res["first_name"]).lower()) * 5) + (fuzz.ratio(query.lower(), "{0}".format(res["last_name"]).lower()) * 5) + fuzz.token_set_ratio(query.lower(), "".format(res["uta_id"]).lower()), reverse=True))

    @route('/search/user/name/and/net_id/<query>')
    def search_user_name_net_id(self, query):
        query_results = []
        query_results += Users.query.filter(db.func.soundex(db.func.concat(Users.first_name, " ", Users.middle_name, " ", Users.last_name)).like(db.func.soundex(query)) |
                                            db.func.soundex(db.func.concat(Users.first_name, " ", Users.last_name)).like(db.func.soundex(query))).distinct().all()

        for q in query.split():
            query_results += Users.query.filter(db.func.soundex(Users.first_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.middle_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.last_name).like(db.func.soundex(q.strip())) |
                                                Users.first_name.like("{0}%".format(q.strip())) |
                                                Users.last_name.like("{0}%".format(q.strip())) |
                                                Users.net_id.like("{0}%".format(q.strip()))).distinct().all()

        return jsonify(sorted(self.process_query_results(query_results), key=lambda res: (fuzz.ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 10) + (fuzz.token_set_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.partial_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.ratio(query.lower(), "{0} {0}".format(res["first_name"], res["last_name"]).lower()) * 10) + (fuzz.ratio(query.lower(), "{0}".format(res["first_name"]).lower()) * 5) + (fuzz.ratio(query.lower(), "{0}".format(res["last_name"]).lower()) * 5) + fuzz.token_set_ratio(query.lower(), "".format(res["net_id"]).lower()), reverse=True))

    @route('/search/user/name/and/net_id/and/uta_id/<query>')
    def search_user_name_net_id_uta_id(self, query):
        query_results = []
        query_results += Users.query.filter(db.func.soundex(db.func.concat(Users.first_name, " ", Users.middle_name, " ", Users.last_name)).like(db.func.soundex(query)) |
                                            db.func.soundex(db.func.concat(Users.first_name, " ", Users.last_name)).like(db.func.soundex(query))).distinct().all()

        for q in query.split():
            query.strip("()[]")
            query_results += Users.query.filter(db.func.soundex(Users.first_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.middle_name).like(db.func.soundex(q.strip())) |
                                                db.func.soundex(Users.last_name).like(db.func.soundex(q.strip())) |
                                                Users.first_name.like("{0}%".format(q.strip())) |
                                                Users.last_name.like("{0}%".format(q.strip())) |
                                                Users.net_id.like("{0}%".format(q.strip())) |
                                                Users.uta_id.like("{0}%".format(q.strip()))).distinct().all()

        return jsonify(sorted(self.process_query_results(query_results), key=lambda res: (fuzz.ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 10) + (fuzz.token_set_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.partial_ratio(query.lower(), "{0} {0} {0}".format(res["first_name"], res["middle_name"], res["last_name"]).lower()) * 15) + (fuzz.ratio(query.lower(), "{0} {0}".format(res["first_name"], res["last_name"]).lower()) * 10) + (fuzz.ratio(query.lower(), "{0}".format(res["first_name"]).lower()) * 5) + (fuzz.ratio(query.lower(), "{0}".format(res["last_name"]).lower()) * 5) + fuzz.token_set_ratio(query.lower(), "".format(res["net_id"]).lower()) + fuzz.token_set_ratio(query.lower(), "".format(res["uta_id"]).lower()), reverse=True))

    @route('/search/user/staff/name/<name>')
    def search_staff_name(self, name):
        pass

    @route('/search/user/staff/name/first/<first_name>')
    def search_staff_first_name(self, first_name):
        pass

    @route('/search/user/staff/name/last/<last_name>')
    def search_staff_last_name(self, last_name):
        pass

    @route('/search/user/student/name/<name>')
    def search_student_name(self, name):
        return "{}".format(name)

    @route('/search/user/student/name/first/<first_name>')
    def search_student_first_name(self, first_name):
        pass

    @route('/search/user/student/name/last/<last_name>')
    def search_student_last_name(self, last_name):
        pass

    @route('/search/user/student/undergraduate/name/<name>')
    def search_undergraduate_student_name(self, name):
        pass

    @route('/search/user/student/undergraduate/name/first/<first_name>')
    def search_undergraduate_student_first_name(self, first_name):
        pass

    @route('/search/user/student/undergraduate/name/last/<last_name>')
    def search_undergraduate_student_last_name(self, last_name):
        pass

    @route('/search/user/student/graduate/name/<name>')
    def search_graduate_student_name(self, name):
        pass

    @route('/search/user/student/graduate/name/first/<first_name>')
    def search_graduate_student_first_name(self, first_name):
        pass

    @route('/search/user/student/graduate/name/last/<last_name>')
    def search_graduate_student_last_name(self, last_name):
        pass

    @route('/get-by/user/name/<name>')
    def get_user_name(self, name):
        pass

    @route('/get-by/user/name/first/<first_name>')
    def get_user_first_name(self, first_name):
        pass

    @route('/get-by/user/name/last/<last_name>')
    def get_user_last_name(self, last_name):
        pass

    @route('/get-by/user/eid/<user_eid>')
    def get_user_eid(self, user_eid):
        pass

    @route('/get-by/user/id_number/<user_id_number>')
    def get_user_id_number(self, user_id_number):
        pass

    @route('/get-by/user/faculty/name/<name>')
    def get_faculty_name(self, name):
        pass

    @route('/get-by/user/faculty/name/first/<first_name>')
    def get_faculty_first_name(self, first_name):
        pass

    @route('/get-by/user/faculty/name/last/<last_name>')
    def get_faculty_last_name(self, last_name):
        pass

    @route('/get-by/user/faculty/eid/<user_eid>')
    def get_faculty_eid(self, user_eid):
        pass

    @route('/get-by/user/faculty/id_number/<user_id_number>')
    def get_faculty_id_number(self, user_id_number):
        pass

    @route('/get-by/user/students/name/<name>')
    def get_students_name(self, name):
        pass

    @route('/get-by/user/students/name/first/<first_name>')
    def get_students_first_name(self, first_name):
        pass

    @route('/get-by/user/students/name/last/<last_name>')
    def get_students_last_name(self, last_name):
        pass

    @route('/get-by/user/students/eid/<user_eid>')
    def get_students_eid(self, user_eid):
        pass

    @route('/get-by/user/students/id_number/<user_id_number>')
    def get_students_id_number(self, user_id_number):
        pass

    @route('/get-by/user/students/undergraduate/name/<name>')
    def get_students_undergraduate_name(self, name):
        pass

    @route('/get-by/user/students/undergraduate/name/first/<first_name>')
    def get_students_undergraduate_first_name(self, first_name):
        pass

    @route('/get-by/user/students/undergraduate/name/last/<last_name>')
    def get_students_undergraduate_last_name(self, last_name):
        pass

    @route('/get-by/user/students/undergraduate/eid/<user_eid>')
    def get_students_undergraduate_eid(self, user_eid):
        pass

    @route('/get-by/user/students/undergraduate/id_number/<user_id_number>')
    def get_students_undergraduate_id_number(self, user_id_number):
        pass

    @route('/get-by/user/students/graduate/name/<name>')
    def get_students_graduate_name(self, name):
        pass

    @route('/get-by/user/students/graduate/name/first/<first_name>')
    def get_students_graduate_first_name(self, first_name):
        pass

    @route('/get-by/user/students/graduate/name/last/<last_name>')
    def get_students_graduate_last_name(self, last_name):
        pass

    @route('/get-by/user/students/graduate/eid/<user_eid>')
    def get_students_graduate_eid(self, user_eid):
        pass

    @route('/get-by/user/students/graduate/id_number/<user_id_number>')
    def get_students_graduate_id_number(self, user_id_number):
        pass

    def process_query_results(self, query_results):
        parsed_results = []

        for result in query_results:
            parsed_result = {
                "net_id": result.net_id,
                "uta_id": result.uta_id,
                "first_name": result.first_name,
                "middle_name": result.middle_name,
                "last_name": result.last_name,
                "email": result.email,
                "phone_number": result.phone_number,
                "is_active": result.is_active,
                "is_temp": result.is_temp,
                "is_authenticated": result.is_authenticated
            }

            if parsed_result not in parsed_results:
                parsed_results.append(parsed_result)

        return parsed_results
    
    def process_alumni_query_results(self, query_results):
        parsed_results = []

        for result in query_results:
            parsed_result = {
                "net_id": result.graduate_info.net_id,
                "uta_id": result.graduate_info.uta_id,
                "first_name": result.graduate_info.first_name,
                "middle_name": result.graduate_info.middle_name,
                "last_name": result.graduate_info.last_name,
                "mavs_email": result.graduate_info.mavs_email,
                "alternate_email": result.graduate_info.alt_email,
                "phone_number": result.graduate_info.phone,
                "plan": result.graduate_info.plan,
                "degree": result.graduate_info.degree,
                "graduation_year": result.graduate_info.graduation_year,
                "graduation_semester": result.graduate_info.graduation_semester
            }

            if parsed_result not in parsed_results:
                parsed_results.append(parsed_result)

        return parsed_results
