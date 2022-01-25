from sanic import Sanic

from JDBrowser import JDBrowser

jd_browser = JDBrowser()


def init(app: Sanic):
    global jd_browser
    app.add_task(jd_browser.init())
