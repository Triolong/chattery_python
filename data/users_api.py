import flask
from flask import jsonify

from . import db_session
from .rooms import Room
from .users import User

blueprint = flask.Blueprint(
    "users_api",
    __name__,
    template_folder="templates"
)


@blueprint.route("/api/users")
def users_list():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return jsonify(
        {
            "users":
                [item.to_dict(only=("name", "email", "id")) for item in users]
        }
    )