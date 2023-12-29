from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect

# mysql
db = SQLAlchemy()
# redis
redis_store = None


def create_app():
    """创建app对象"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化db
    db.init_app(app)

    # 利用flask-session，将session数据保存到redis中
    Session(app)
    # 为flask补充CSRF防护
    CSRFProtect(app)

    # 初始化redis对象
    global redis_store
    redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

    # 注册蓝图
    app.register_blueprint(api_v1.api, url_prefix="/order")

    return app


from home.api_v1 import api
