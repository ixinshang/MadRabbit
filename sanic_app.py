from sanic import Sanic

from App import init
from App.views.apis import Api_bp
from App.views.login import Login_bp

app = Sanic(__name__)

init(app)

app.blueprint(Login_bp)
app.blueprint(Api_bp)


if __name__ == "__main__":
    # app.run(host="127.0.0.1", port=1234, debug=True)
    app.run(host="0.0.0.0", port=1234)

