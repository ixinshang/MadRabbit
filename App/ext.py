from sanic import Sanic

from JDBrowser import JDBrowser

jd_browser = JDBrowser()


def init(app: Sanic):
    # app.add_task(jd_browser.init())
    pass
