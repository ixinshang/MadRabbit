from jinja2 import Environment, PackageLoader, select_autoescape
from sanic import html, Blueprint

Login_bp = Blueprint('login')
Login_bp.static("/", "./App/static")

env = Environment(
    loader=PackageLoader('App', 'templates'),
    autoescape=select_autoescape(['html', 'xml', 'tpl']))


def template(tpl, **kwargs):
    template = env.get_template(tpl)
    return html(template.render(kwargs))


@Login_bp.route("/")
async def redirect_index(request):
    return template("index.html")


@Login_bp.route("/login")
async def index(request):
    return template("index.html")
