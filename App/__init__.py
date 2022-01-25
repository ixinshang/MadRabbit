from sanic import Sanic

from App.ext import init


def creat_app(app: Sanic):
    init(app)

    return app
