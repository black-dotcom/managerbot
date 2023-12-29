from . import api
from home import db, models


@api.route("/order")
def order():
    return "你好黑客！"
