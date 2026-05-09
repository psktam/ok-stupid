import flask_login


class User(flask_login.UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password = password


users = {"admin": User("admin", "admin-password")}


_login_manager = flask_login.LoginManager()


@_login_manager.user_loader
def user_loader(id):
    return users.get(id)


def get_login_manager():
    return _login_manager
