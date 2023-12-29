from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT


class User(db.Model):
    """用户表"""
    __tablename__ = "user"
    # 用户id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 用户名
    username = db.Column(db.String(128))
    # 余额（积分）
    balance = db.Column(db.String(128))
    # 注册时间
    register_time = db.Column(db.DateTime(), default=datetime.now())
    # tg的id
    t_id = db.Column(db.String(96))

    # 将映射与数据库引擎绑定
    __table_args__ = {'mysql_engine': 'InnoDB'}


class Conf(db.Model):
    """配置表"""
    __tablename__ = 'conf'
    # id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 配置名称
    name = db.Column(db.String(512))
    # 配置值
    value = db.Column(LONGTEXT)
    # 值类型
    typestr = db.Column(db.String(48))
    # 创建时间
    create_time = db.Column(db.DateTime(), default=datetime.now())
    # 备注
    memo = db.Column(db.String(128))


class Recharge(db.Model):
    """充值表"""
    __tablename__ = "recharge"
    # id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 充值金额
    money = db.Column(db.String(256))
    # 状态 0失败，1成功，2待支付，3已超时，4已取消
    status = db.Column(db.Integer())
    # 转账钱包
    from_address = db.Column(db.String(256))
    # 创建时间
    create_time = db.Column(db.DateTime(), default=datetime.now())
    # tg的id
    t_id = db.Column(db.String(96))
    # 用户id
    user_id = db.Column(db.Integer())
    # 第一名字
    firstname = db.Column(db.String(96))


class Wallet(db.Model):
    """钱包记录表"""
    __tablename__ = 'wallet'
    # 订单id
    id = db.Column(db.String(68), unique=True, primary_key=True)
    # 订单金额
    money = db.Column(db.String(256))
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 发起人
    sender = db.Column(db.String(256))
    # 接收人
    recipient = db.Column(db.String(256))
    # 类型
    typestr = db.Column(db.String(48), default="USDT")
    # 插入时间
    insert_time = db.Column(db.DateTime(), default=datetime.now())


class Orders(db.Model):
    """订单记录表"""
    __tablename__ = 'orders'
    # 订单id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 订单金额
    money = db.Column(db.String(256))
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 订单类型
    typestr = db.Column(db.String(256))
    # 订单状态 1成功 2失败
    status = db.Column(db.Integer())
    # 用户id
    t_id = db.Column(db.String(256))


class Newone(db.Model):
    """新人进群记录表"""
    __tablename__ = 'newone'
    # 订单id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 用户名
    first_name = db.Column(db.String(256))
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 用户id
    t_id = db.Column(db.String(128))
    # 验证状态（1通过，2验证中, 3拒绝）
    status = db.Column(db.Integer())
    # 群聊id
    chat_id = db.Column(db.String(128))
    # 消息id
    message_id = db.Column(db.String(128))


class Word_ban(db.Model):
    """关键词禁言表"""
    __tablename__ = 'word_ban'
    # id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 关键词
    word = db.Column(db.String(48))
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 操作人id
    t_id = db.Column(db.String(48))


class Word_reply(db.Model):
    """精准关键词回复表"""
    __tablename__ = 'word_reply'
    # id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 关键词
    word = db.Column(db.String(48))
    # 回复内容
    reply_text = db.Column(LONGTEXT)
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 操作人id
    t_id = db.Column(db.String(48))


class Word_h_reply(db.Model):
    """包含关键词回复表"""
    __tablename__ = 'word_h_reply'
    # id
    id = db.Column(db.Integer(), unique=True, primary_key=True, autoincrement=True)
    # 关键词
    word = db.Column(db.String(48))
    # 回复内容
    reply_text = db.Column(LONGTEXT)
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 操作人id
    t_id = db.Column(db.String(48))


class Keywords(db.Model):
    """用户关键词表"""
    __tablename__ = 'keywords'
    # id
    id = db.Column(db.String(48), unique=True, primary_key=True)
    # 关键词
    word = db.Column(db.String(48))
    # 创建时间
    create_time = db.Column(db.DateTime())
    # 发送人id
    t_id = db.Column(db.String(48))
