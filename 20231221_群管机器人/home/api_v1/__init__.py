from flask import Blueprint

# 创建蓝图对象
api = Blueprint("order",__name__)

# 导入蓝图的视图
from . import order