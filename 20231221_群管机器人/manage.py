# -*- coding: utf-8 -*
from home import create_app, db
from tronapi import HttpProvider, Tron
from threading import Thread
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from home.models import User, Recharge, Wallet, Orders, Newone, Keywords, Word_ban, Word_reply, Word_h_reply
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ParseMode, \
    BotCommand, ChatPermissions
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, \
    ChatMemberHandler, filters
from datetime import datetime, timedelta
import time, threading, json, requests, os, random, jieba, re
from config import TOKEN, Group_li, Admin_li, proxy_config
from decimal import Decimal
from config import Text_data
from telegram import ChatAction
from pybloom_live import BloomFilter

global_data = {}
kefu = "toumingde"
Admin_li = ["1707841429"]

# 创建flask应用对象
app = create_app()
manager = Manager(app)

Migrate(app, db)
manager.add_command("db", MigrateCommand)

commands = [
    BotCommand(command="id", description="查看当前ID"),
    BotCommand(command="start", description="开始使用机器人"),
    BotCommand(command="recharge", description="充值余额"),
]

# 创建一个Bloom Filter
banned_words_filter = set()

# 将关键词添加到Bloom Filter中
with app.app_context():
    for word_ban in Word_ban.query.all():
        banned_words_filter.add(word_ban.word)

updater = Updater(token=TOKEN, use_context=True, request_kwargs=proxy_config)
# updater = Updater(token=TOKEN, use_context=True)
updater.bot.set_my_commands(commands)
dispatcher = updater.dispatcher


class Spider():
    def __init__(self, wallet):
        self.url = "https://api.trongrid.io/v1/accounts/%s/transactions/trc20?only_to=true&limit=20&contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t" % wallet
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/112.0.0.0 Safari/537.36",
        }
        self.proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        self.result = []

    def parse(self):
        try:
            # data = json.loads(requests.get(self.url, headers=self.headers, proxies=self.proxies).content.decode())
            data = json.loads(requests.get(self.url, headers=self.headers).content.decode())
        except Exception as e:
            print("请求转账信息失败！")
            return 0
        for line in data.get("data", []):
            self.result.append(line)
        if not self.result:
            return 0
        return 1

    def run(self):
        if self.parse():
            print("获取数据成功！")
            return self.result
        return []


def timestr_to_time(timestr):
    """时间戳转换为时间字符串"""
    try:
        timestr = int(timestr)
    except Exception as e:
        print(e)
        return 0
    try:
        # 获取年份
        res = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestr))
    except Exception as e:
        return 0
    return res


def update_wallte():
    with app.app_context():
        # 查询当前监听的钱包地址
        myaddress = global_data.get("My_address", "TAZ5gPwfU4bn14dKRqJXbCZJGJMqgoJsaf")
        spider = Spider(myaddress)
        result = spider.run()
        print("当前监听钱包地址为：", myaddress)
        for line in result:
            # 2.判断数据是否在数据库中
            order_id = line.get("transaction_id", "")
            block_timestamp = line.get("block_timestamp", "")
            if block_timestamp:
                create_time = timestr_to_time(block_timestamp / 1000)
                # print("钱包转账时间：%s" % create_time)
            else:
                create_time = None
            if line["type"] != "Transfer":
                continue
            print("该笔订单交易类型为：", line["type"])
            try:
                obj = db.session.query(Wallet).filter_by(id=order_id).first()
            except Exception as e:
                print(e)
                continue
            if obj:
                continue
            money = int(line.get("value"))
            sender = line.get("from")
            recipient = line.get("to")
            print(sender)
            try:
                obj = Wallet(id=order_id, money=money, sender=sender, recipient=recipient, create_time=create_time,
                             insert_time=datetime.now())
            except Exception as e:
                print(e)
                continue
            # 3.入库
            try:
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
                continue
        db.session.close()


def update_wallet_task():
    while True:
        # 读取数据库数据
        with app.app_context():
            try:
                orders = Recharge.query.filter_by(status=2).all()
            except Exception as e:
                print(e)
                orders = []
            if not orders:
                time.sleep(30)
                continue
            # 更新钱包记录
            # update_wallte()
            for order in orders:
                # 订单金额
                money = str(int(Decimal(order.money) * 1000000))
                print("订单金额为：", money)
                # tg的id
                t_id = order.t_id
                # 订单创建时间
                create_time = order.create_time
                delta = timedelta(minutes=10)
                end_date = create_time + delta
                now = datetime.now()
                if now > end_date:
                    print("订单已超时！并且设置了订单为超时状态。")
                    # 设置订单状态为已超时
                    order.status = 3
                    try:
                        db.session.add(order)
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        db.session.rollback()
                        db.session.close()
                    continue
                # 通过订单金额去匹配钱包记录
                try:
                    obj = Wallet.query.filter(Wallet.money == money,
                                              Wallet.create_time.between(create_time, end_date)).first()
                except Exception as e:
                    print(e)
                    db.session.close()
                    continue
                if not obj:
                    print("没有匹配的订单")
                    db.session.close()
                    continue
                # 充值成功，给指定用户发送压缩文件
                print("发送了压缩文件！")
                order.status = 1
                flag = 1
                try:
                    db.session.add(order)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    db.session.rollback()
                    flag = 2
                if flag == 1:
                    print("发卡成功！")
                else:
                    print("发卡失败")
                    order.status = 0
                    try:
                        db.session.add(order)
                        db.session.commit()
                    except Exception as e:
                        db.session.close()
                        db.session.rollback()
                        continue
            time.sleep(6)
            db.session.close()


def update_yan_task():
    while True:
        # 读取数据库数据
        with app.app_context():
            try:
                orders = Newone.query.filter_by(status=2).all()
            except Exception as e:
                print(e)
                orders = []
            if not orders:
                time.sleep(30)
                continue
            for obj in orders:
                current_time = datetime.now()
                # 计算时间差
                time_difference = current_time - obj.create_time
                # 判断是否超过2分钟
                if time_difference < timedelta(minutes=2):
                    continue
                chat_id = obj.chat_id
                user_id = obj.t_id
                message_id = obj.message_id
                try:
                    # 踢出群组
                    updater.bot.ban_chat_member(chat_id, user_id)
                    # 删除最后的验证消息
                    updater.bot.delete_message(chat_id, message_id=message_id)
                except Exception as e:
                    pass
                try:
                    obj.status = 3
                    db.session.add(obj)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    db.session.rollback()
            time.sleep(30)


def register_user(user_id, username):
    with app.app_context():
        try:
            user = User.query.filter_by(t_id=user_id).first()
        except Exception as e:
            print(e)
            user = None
        if user:
            print("不是新用户")
            return
        try:
            user = User(username=username, t_id=user_id, balance=0, register_time=datetime.now())
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            print(e)
            print("注册失败")
            db.session.rollback()
            db.session.close()
            return
        return user


def turn_off(update, context):
    context.bot.delete_message(update.effective_chat.id, message_id=update.callback_query.message.message_id)
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id, text='已关闭！')


def get_filenames_in_path(path):
    try:
        # 获取指定路径下的所有文件和目录
        files_and_dirs = os.listdir(path)

        # 过滤出文件，去掉目录
        filenames = [f for f in files_and_dirs if os.path.isfile(os.path.join(path, f))]

        return filenames
    except Exception as e:
        print(f"Error: {e}")
        return None


def ceate_order(update, context):
    info = update.callback_query.to_dict()
    user_id = info["from"].get("id")
    query = update.callback_query
    callback_data = query.data
    info = callback_data.split("_")
    price = int(info[2])
    typestr = str(info[1])
    # 判断余额是否够price这么多！
    with app.app_context():
        try:
            user = User.query.filter_by(t_id=user_id).first()
        except Exception as e:
            print(e)
            text = "很抱歉，后台出现错误，请稍后重试！"
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
        if not user:
            text = "很抱歉，后台出现错误，请稍后重试！"
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
    if int(user.balance) < price:
        text = "余额不足，请及时充值！\n当前余额：0 USDT"
        context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
        return
    with app.app_context():
        try:
            order = Orders(money=price, create_time=datetime.now(), typestr=typestr, status=0, t_id=user_id)
        except Exception as e:
            print(e)
            text = "很抱歉，后台出现错误，请稍后重试！"
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
        user.balance = int(user.balance) - price
        try:
            db.session.add(user)
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.close()
            print(e)
            text = "很抱歉，后台出现错误，请稍后重试！"
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
    text = "下单成功，请耐心等待文件自动传输。\n预计5分钟内完成传输！"
    context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
    file_path = "home/utills/" + typestr
    print(file_path)
    filenames = get_filenames_in_path(file_path)
    for filename in filenames:
        path = "home/utills/" + typestr + "/" + filename
        print(path)
        try:
            context.bot.send_document(chat_id=user_id, document=open(path, 'rb'))
            # send_large_file(user_id, file_path)
        except Exception as e:
            print(e)
            text = "传输文件超时!\n请联系客服：@%s" % kefu
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
        time.sleep(1)
    with app.app_context():
        order.status = 1
        try:
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.close()
            print(e)
            text = "很抱歉，后台出现错误，请稍后重试！"
            context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            return
    text = "订单已完成！"
    context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)


def start(update, context):
    username = update.message.from_user["username"]
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    first_name = update.message.from_user["first_name"]
    text = "欢迎：<code>%s</code>\n使用萝卜群管机器人！\n您的ID为：<code>%s</code>" % (first_name, user_id)

    context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    register_user(user_id, username)


def get_id(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    username = update.message.from_user["username"]
    context.bot.send_message(chat_id=chat_id, text=str(chat_id))
    if str(user_id) not in Admin_li:
        # 说明是普通用户
        for c_id in Admin_li:
            # 通知目标聊天
            context.bot.send_message(chat_id=c_id,
                                     text="用户ID：<code>{}</code>\n用户名：@{}\n当前时间：{}\n调用了/id命令".format(
                                         user_id,
                                         username,
                                         str(datetime.now())[
                                         :19]), parse_mode=ParseMode.HTML)
            time.sleep(0.5)


def get_num():
    a = random.randint(1, 999)
    # 将整数转换为三位数的字符串
    a_str = str(a).zfill(3)
    return a_str


def move_order(update, context):
    kefu = global_data.get("kefu", "toumingde")
    language = global_data.get("language", "cn")

    info = update.callback_query.to_dict()
    # tg的id
    t_id = info["from"]["id"]
    with app.app_context():
        try:
            order = db.session.query(Recharge).filter_by(t_id=t_id, status=2).first()
        except Exception as e:
            print(e)
            context.bot.send_message(update.effective_chat.id, Text_data[language]["turn_order_false"] % kefu)
            db.session.close()
            return
        if not order:
            context.bot.send_message(update.effective_chat.id, Text_data[language]["order_not_found"] % kefu)
            return
        order.status = 4
        try:
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(update.effective_chat.id, Text_data[language]["turn_order_false"] % kefu)
            return
        order_id = order.id
        firstname = order.firstname
        create_time = order.create_time
        money = order.money
        content = Text_data[language]["order_move_info"] % (firstname, order_id, create_time, money)
        button = InlineKeyboardButton(Text_data[language]["close"], callback_data="关闭")
        button1 = InlineKeyboardButton(Text_data[language]["again_recharge"], callback_data="再次充值")
        buttons_row = [button, button1]
        keyboard = InlineKeyboardMarkup([buttons_row])
        context.bot.send_message(update.effective_chat.id, content, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(turn_off, pattern='^关闭$'))
        dispatcher.add_handler(CallbackQueryHandler(recharge, pattern='^再次充值$'))


def listen_order(order_id, chat_id):
    now1 = datetime.now()
    print("开始监听的时间为：%s" % str(now1))
    while True:
        language = global_data.get("language", "cn")
        now = datetime.now()
        # 1.查询该订单id
        with app.app_context():
            try:
                order = Recharge.query.filter_by(id=order_id).first()
            except Exception as e:
                print(e)
                time.sleep(20)
                continue
        print("查询出的订单状态：%s" % str(order.status))
        # 没有订单数据
        if not order:
            time.sleep(10)
            break
        if order.status == 1:
            # 用户支付成功
            print("订单完成！！")
            updater.bot.send_message(chat_id, Text_data[language]["order_recharge_success"])
            updater.bot.send_message(global_data.get("Admin_id"), "有新订单充值成功啦！\n时间：%s\n金额：%s\n昵称：%s" % (
                str(now), order.money, order.firstname))
            break
        if order.status == 3:
            print("订单超时！！")
            updater.bot.send_message(chat_id, Text_data[language]["order_time_out"])
            break
        if order.status == 4:
            print("订单已取消！！")
            break
        if order.status == 2:
            print("当前订单状态还是待支付！")

            # 判断是否已超时
            if (now - order.create_time).seconds > 600:
                print("订单已超时，现在设置为超时状态！")
                print("订单创建时间为：", order.create_time)
                print("当前时间为：", now)
                order.status = 3
                with app.app_context():
                    try:
                        db.session.add(order)
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        db.session.rollback()
                        db.session.close()
                        continue
                updater.bot.send_message(chat_id, Text_data[language]["order_time_out"])
                break
        time.sleep(5)

    print("已退出监听订单代码")


def create_order(update, context):
    kefu = global_data.get("kefu", "toumingde")
    language = global_data.get("language", "cn")
    # 我的钱包地址
    myaddress = global_data.get("My_address", "TAZ5gPwfU4bn14dKRqJXbCZJGJMqgoJsaf")
    info = update.callback_query.to_dict()
    # tg的id
    t_id = info["from"]["id"]
    with app.app_context():
        # 1.检测是否存在待支付的订单
        try:
            order = db.session.query(Recharge).filter_by(status=2, t_id=t_id).first()
        except Exception as e:
            print(e)
            context.bot.send_message(update.effective_chat.id, Text_data[language]["create_order_false"] % kefu)
            return

    if order:
        money = order.money
        create_time = order.create_time

        content = Text_data[language]["create_order_info"] % (myaddress, money, money, money, create_time)
        button = InlineKeyboardButton(Text_data[language]["close"], callback_data="关闭")
        button1 = InlineKeyboardButton(Text_data[language]["move_order"], callback_data="取消订单")
        button2 = InlineKeyboardButton(Text_data[language]["contact_customer"], url="https://t.me/%s" % kefu)
        row = [button, button1, button2]
        keyboard = InlineKeyboardMarkup([row])
        context.bot.send_message(update.effective_chat.id, content, parse_mode=ParseMode.HTML,
                                 reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(turn_off, pattern='^关闭'))
        dispatcher.add_handler(CallbackQueryHandler(move_order, pattern='^取消订单$'))
        return

    # 3.用户昵称
    first_name = info["from"]["first_name"]
    # 4.下单时间
    now = datetime.now()
    # 5.创建订单金额
    back_num = get_num()
    print("不存在旧订单，创建新订单！")
    try:
        money = Decimal(update.callback_query.data.replace(" USDT", ".") + back_num)
    except Exception as e:
        print("金额出错了！！")
        return

    content = Text_data[language]["create_order_info"] % (myaddress, money, money, money, str(now))
    button = InlineKeyboardButton(Text_data[language]["close"], callback_data="关闭")
    button1 = InlineKeyboardButton(Text_data[language]["move_order"], callback_data="取消订单")
    button2 = InlineKeyboardButton(Text_data[language]["contact_customer"], url="https://t.me/%s" % kefu)
    row = [button, button1, button2]
    keyboard = InlineKeyboardMarkup([row])
    with app.app_context():
        try:
            user = db.session.query(User).filter_by(t_id=t_id).first()
        except Exception as e:
            context.bot.send_message(update.effective_chat.id, Text_data[language]["create_order_false"] % kefu)
            db.session.close()
            return
        if not user:
            context.bot.send_message(update.effective_chat.id, Text_data[language]["create_order_false"] % kefu)
            db.session.close()
            return

        # 将订单入库
        try:
            order = Recharge(status=2, from_address=myaddress, t_id=t_id, money=money, user_id=1, firstname=first_name,
                             create_time=now)
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            print("订单入库失败")
            db.session.rollback()
            context.bot.send_message(update.effective_chat.id, Text_data[language]["create_order_false"] % kefu)
            db.session.close()
            return
        context.bot.send_message(update.effective_chat.id, content, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(turn_off, pattern='^关闭$'))
        dispatcher.add_handler(CallbackQueryHandler(move_order, pattern='^取消订单$'))

        # 开启另一个线程，监听订单完成与否，，出发发送消息至客户中
        t1 = threading.Thread(target=listen_order, args=(order.id, update.effective_chat.id))
        t1.start()


def recharge(update, context):
    Group_id = global_data.get("Group_id")
    kefu = global_data.get("kefu", "toumingde")
    language = global_data.get("language", "cn")
    if Group_id == str(update.effective_chat.id):
        message_id = update.message.message_id
        context.bot.send_message(update.effective_chat.id, Text_data[language]["recharge_tips"],
                                 reply_to_message_id=message_id)
        return

    button0 = InlineKeyboardButton('30 USDT', callback_data='30 USDT')
    button1 = InlineKeyboardButton('100 USDT', callback_data='100 USDT')
    button2 = InlineKeyboardButton('200 USDT', callback_data='200 USDT')
    row1 = [button0, button1, button2]
    button3 = InlineKeyboardButton('500 USDT', callback_data="500 USDT")
    button4 = InlineKeyboardButton('1000 USDT', callback_data="1000 USDT")
    button5 = InlineKeyboardButton('2000 USDT', callback_data='2000 USDT')
    row2 = [button3, button4, button5]
    button6 = InlineKeyboardButton(Text_data[language]["close"], callback_data="关闭")
    button7 = InlineKeyboardButton(Text_data[language]["contact_customer"], url="https://t.me/%s" % kefu)
    row3 = [button6, button7]

    keyboard = InlineKeyboardMarkup([row1, row2, row3])

    context.bot.send_message(update.effective_chat.id, Text_data[language]["recharge_info"] % kefu,
                             reply_markup=keyboard)

    dispatcher.add_handler(CallbackQueryHandler(create_order, pattern='^\d{1,} USDT$'))
    dispatcher.add_handler(CallbackQueryHandler(turn_off, pattern='^关闭$'))


def add_ban_word(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
    except Exception as e:
        print(e)
        return
    with app.app_context():
        try:
            w_obj = Word_ban(word=word, create_time=datetime.now(), t_id=user_id)
            db.session.add(w_obj)
            db.session.commit()
            banned_words_filter.add(word)
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="添加禁言关键词失败！")
            return

    context.bot.send_message(chat_id=chat_id, text="添加禁言关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def del_ban_word(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
    except Exception as e:
        print(e)
        return
    print("开始删除关键词")
    with app.app_context():
        try:
            w_obj = Word_ban.query.filter_by(word=word).first()
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text="删除禁言关键词失败！")
            return
        if not w_obj:
            context.bot.send_message(chat_id=chat_id, text="该关键词不存在！")
            return
        try:
            db.session.delete(w_obj)
            db.session.commit()

        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="删除禁言关键词失败！")
            return
        try:
            banned_words_filter.discard(word)
        except Exception as e:
            print(e)

    print("删除关键词完成")
    context.bot.send_message(chat_id=chat_id, text="删除禁言关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def add_reply_word(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
        content = str(args[1])
    except Exception as e:
        print(e)
        return
    with app.app_context():
        try:
            w_obj = Word_reply(word=word, create_time=datetime.now(), t_id=user_id, reply_text=content)
            db.session.add(w_obj)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="添加回复关键词失败！")
            return

    context.bot.send_message(chat_id=chat_id, text="添加回复关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def del_reply_word(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
    except Exception as e:
        print(e)
        return

    with app.app_context():
        try:
            w_obj = Word_reply.query.filter_by(word=word).first()
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text="删除回复关键词失败！")
            return
        if not w_obj:
            context.bot.send_message(chat_id=chat_id, text="该关键词不存在！")
            return
        try:
            db.session.delete(w_obj)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="删除回复关键词失败！")
            return

    context.bot.send_message(chat_id=chat_id, text="删除回复关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def add_hword(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
        content = str(args[1])
    except Exception as e:
        print(e)
        return
    with app.app_context():
        try:
            w_obj = Word_h_reply(word=word, create_time=datetime.now(), t_id=user_id, reply_text=content)
            db.session.add(w_obj)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="添加回复关键词失败！")
            return

    context.bot.send_message(chat_id=chat_id, text="添加回复关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def del_hword(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return
    args = context.args
    try:
        word = str(args[0])
    except Exception as e:
        print(e)
        return

    with app.app_context():
        try:
            w_obj = Word_h_reply.query.filter_by(word=word).first()
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text="删除回复关键词失败！")
            return
        if not w_obj:
            context.bot.send_message(chat_id=chat_id, text="该关键词不存在！")
            return
        try:
            db.session.delete(w_obj)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            context.bot.send_message(chat_id=chat_id, text="删除回复关键词失败！")
            return

    context.bot.send_message(chat_id=chat_id, text="删除回复关键词（<code>%s</code>）成功！" % word,
                             parse_mode=ParseMode.HTML)


def banwordsturn(update, context):
    query = update.callback_query
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    callback_data = query.data
    info = callback_data.split("_")
    now_page = int(info[1])
    status = info[2]  # 2是上一页，1是下一页
    if int(now_page) == 1 and int(status) == 2:
        query.answer("已经在第一页了！", show_alert=True)
        return
    if int(status) == 2:
        page = now_page - 1
    else:
        page = now_page + 1
    page_size = 10
    # 查询禁止关键词列表
    with app.app_context():
        try:
            total_num = Word_ban.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_ban.query.order_by(Word_ban.create_time.desc()).offset((page - 1) * page_size).limit(
                page_size).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word

        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="banwordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="banwordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML,
                                      reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(banwordsturn, pattern='^banwordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(banwordsturn, pattern='^banwordsturn_%s_1' % page))


def ban_words(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return

    page = 1
    page_size = 10
    # 查询禁止关键词列表
    with app.app_context():
        try:
            total_num = Word_ban.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_ban.query.order_by(Word_ban.create_time.desc()).offset((page - 1) * page_size).limit(
                page_size).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word

        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="banwordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="banwordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(banwordsturn, pattern='^banwordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(banwordsturn, pattern='^banwordsturn_%s_1' % page))


def wordsturn(update, context):
    query = update.callback_query
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    callback_data = query.data
    info = callback_data.split("_")
    now_page = int(info[1])
    status = info[2]  # 2是上一页，1是下一页
    if int(now_page) == 1 and int(status) == 2:
        query.answer("已经在第一页了！", show_alert=True)
        return
    if int(status) == 2:
        page = now_page - 1
    else:
        page = now_page + 1
    page_size = 10
    # 查询禁止关键词列表
    with app.app_context():
        try:
            total_num = Word_reply.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_reply.query.order_by(Word_reply.create_time.desc()).offset((page - 1) * page_size).limit(
                page_size).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word

        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="wordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="wordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML,
                                      reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(wordsturn, pattern='^wordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(wordsturn, pattern='^wordsturn_%s_1' % page))


def words(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return

    page = 1
    page_size = 10
    # 查询禁止关键词列表
    with app.app_context():
        try:
            total_num = Word_reply.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_reply.query.order_by(Word_reply.create_time.desc()).limit(page_size).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        if not objs:
            context.bot.send_message(chat_id=chat_id, text="数据为空！", parse_mode=ParseMode.HTML)
            return
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word
        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="wordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="wordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(wordsturn, pattern='^wordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(wordsturn, pattern='^wordsturn_%s_1' % page))
        return


def hwordsturn(update, context):
    query = update.callback_query
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    callback_data = query.data
    info = callback_data.split("_")
    now_page = int(info[1])
    status = info[2]  # 2是上一页，1是下一页
    if int(now_page) == 1 and int(status) == 2:
        query.answer("已经在第一页了！", show_alert=True)
        return
    if int(status) == 2:
        page = now_page - 1
    else:
        page = now_page + 1
    page_size = 10

    with app.app_context():
        try:
            total_num = Word_h_reply.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_h_reply.query.order_by(Word_h_reply.create_time.desc()).offset((page - 1) * page_size).limit(
                page_size).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word

        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="hwordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="hwordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML,
                                      reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(hwordsturn, pattern='^hwordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(hwordsturn, pattern='^hwordsturn_%s_1' % page))


def hwords(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    if str(user_id) not in Admin_li:
        return

    page = 1
    page_size = 10
    # 查询禁止关键词列表
    with app.app_context():
        try:
            total_num = Word_h_reply.query.count()
        except Exception as e:
            print(e)
            return
        try:
            objs = Word_h_reply.query.order_by(Word_h_reply.create_time.desc()).limit(10).all()
        except Exception as e:
            print(e)
            context.bot.send_message(chat_id=chat_id, text="查询失败！")
            return
        text = ""
        page_count = (total_num + page_size - 1) // page_size
        for obj in objs:
            word = obj.word
            text += "<code>%s</code>\n" % word
        text += "总页数为：<b>%s</b>，每页最多显示<b>%s</b>条数据" % (page_count, page_size)
        button1 = InlineKeyboardButton("上一页", callback_data="hwordsturn_%s_2" % page)
        button2 = InlineKeyboardButton(str(page), callback_data="next")
        button3 = InlineKeyboardButton("下一页", callback_data="hwordsturn_%s_1" % page)
        row1 = [button1, button2, button3]
        keyboard = InlineKeyboardMarkup([row1])
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        dispatcher.add_handler(CallbackQueryHandler(hwordsturn, pattern='^hwordsturn_%s_2' % page))
        dispatcher.add_handler(CallbackQueryHandler(hwordsturn, pattern='^hwordsturn_%s_1' % page))


def yan(update, context):
    query = update.callback_query
    c_info = update.callback_query.to_dict()
    c_user_id = c_info["from"].get("id")
    first_name = c_info["from"].get("first_name")
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    callback_data = query.data
    info = callback_data.split("_")
    qes = info[0]
    answer = info[1]
    user_id = info[2]
    num = int(info[3])
    name_li = ["大象", "羊", "鸡", "老虎"]
    if str(user_id) != str(c_user_id):
        query.answer("请勿点击他人按钮！", show_alert=True)
        return

    context.bot.delete_message(chat_id, message_id)
    if qes != answer:
        if num - 1 == 0:
            # 踢出群聊
            context.bot.ban_chat_member(chat_id, user_id)
            return
        answer = name_li[random.randint(0, len(name_li) - 1)]
        content = "<b>验证失败！</b>\n亲爱的用户：<code>%s</code>\n您还有 <code>%s</code> 次机会。\n请点击 <code>%s</code> 按钮进行入群验证！" % (
            first_name, num - 1, answer)

        button = InlineKeyboardButton("🐏", callback_data="羊_%s_%s_%s" % (answer, user_id, num - 1))
        button1 = InlineKeyboardButton("🐓", callback_data="鸡_%s_%s_%s" % (answer, user_id, num - 1))
        button2 = InlineKeyboardButton("🐅", callback_data="老虎_%s_%s_%s" % (answer, user_id, num - 1))
        button3 = InlineKeyboardButton("🐘", callback_data="大象_%s_%s_%s" % (answer, user_id, num - 1))

        buttons_row = [button, button1, button2, button3]
        button4 = InlineKeyboardButton("解禁✅", callback_data="admin_pass_%s" % user_id)
        button5 = InlineKeyboardButton("踢出🦶", callback_data="admin_out_%s" % user_id)

        row2 = [button4, button5]
        keyboard = InlineKeyboardMarkup([buttons_row, row2])
        message = context.bot.send_message(chat_id=chat_id, text=content, reply_markup=keyboard,
                                           parse_mode=ParseMode.HTML)

        with app.app_context():
            try:
                obj = Newone.query.filter_by(t_id=user_id, status=2, chat_id=chat_id).first()
                obj.message_id = message.message_id
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()

        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^羊_%s_%s_%s' % (answer, user_id, num - 1)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^鸡_%s_%s_%s' % (answer, user_id, num - 1)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^老虎_%s_%s_%s' % (answer, user_id, num - 1)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^大象_%s_%s_%s' % (answer, user_id, num - 1)))
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_pass_%s' % user_id))
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_out_%s' % user_id))
    else:
        context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
            ),
            until_date=0  # 将 until_date 设置为 0 表示解除禁言
        )
        content = "<b>验证通过！</b>\n欢迎您加入大家庭：<code>%s</code>" % first_name
        context.bot.send_message(chat_id=chat_id, text=content, parse_mode=ParseMode.HTML)

        with app.app_context():
            try:
                obj = Newone.query.filter_by(t_id=user_id, status=2, chat_id=chat_id).first()
                obj.status = 1
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()


def adminyan(update, context):
    query = update.callback_query
    c_info = update.callback_query.to_dict()
    c_user_id = str(c_info["from"].get("id"))
    first_name = c_info["from"].get("first_name")
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    callback_data = query.data
    info = callback_data.split("_")
    status = str(info[1])
    user_id = info[2]
    if c_user_id not in Admin_li:
        text = "<code>%s</code> 用户恶意点击管理员按钮\n禁言 <code>5</code> 分钟以示警告！" % first_name
        button4 = InlineKeyboardButton("解禁✅", callback_data="admin_pass_%s" % c_user_id)
        button5 = InlineKeyboardButton("踢出🦶", callback_data="admin_out_%s" % c_user_id)
        row2 = [button4, button5]
        keyboard = InlineKeyboardMarkup([row2])
        context.bot.send_message(chat_id=chat_id, reply_markup=keyboard, text=text, parse_mode=ParseMode.HTML)
        context.bot.restrict_chat_member(
            chat_id,
            c_user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
            until_date=time.time() + 300  # 设置禁言时间
        )

        dispatcher.add_handler(
            CallbackQueryHandler(adminyan, pattern='^admin_pass_%s' % c_user_id))
        dispatcher.add_handler(
            CallbackQueryHandler(adminyan, pattern='^admin_out_%s' % c_user_id))
        return
    if status == "pass":
        # 解除禁言
        context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
            ),
            until_date=0  # 将 until_date 设置为 0 表示解除禁言
        )

        try:
            # 删除最后的验证消息
            updater.bot.delete_message(chat_id, message_id=message_id)
        except Exception as e:
            print(e)

        with app.app_context():
            try:
                obj = Newone.query.filter_by(t_id=user_id, status=2, chat_id=chat_id).first()
                obj.status = 1
                content = "<b>验证通过！</b>\n欢迎您加入大家庭：<code>%s</code>" % obj.first_name
                context.bot.send_message(chat_id=chat_id, text=content, parse_mode=ParseMode.HTML)
                context.bot.delete_message(chat_id, message_id=message_id)
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
    else:
        try:
            # 踢出群组
            updater.bot.ban_chat_member(chat_id, user_id)
            # 删除最后的验证消息
            updater.bot.delete_message(chat_id, message_id=message_id)
        except Exception as e:
            print(e)
        with app.app_context():
            try:
                obj = Newone.query.filter_by(t_id=user_id, status=2, chat_id=chat_id).first()
            except Exception as e:
                obj = None
            if obj:
                try:
                    obj.status = 3
                    db.session.add(obj)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    db.session.rollback()
    query.answer("操作成功！", show_alert=True)


def welcome_new_member(update, context):
    chat_id = update.message.chat_id
    try:
        context.bot.delete_message(chat_id, update.message.message_id)
    except Exception as e:
        return
    # 发送验证信息
    name_li = ["大象", "羊", "鸡", "老虎"]
    for user in update.message.new_chat_members:
        user_id = user["id"]
        first_name = user["first_name"]
        answer = name_li[random.randint(0, len(name_li) - 1)]
        print(update.message.date)
        # 对该用户进行禁言
        context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
            until_date=update.message.date.timestamp() + 99999999  # 设置禁言时间
        )

        content = "亲爱的用户：<code>%s</code>\n请点击 <code>%s</code> 按钮完成入群验证！(限两分钟内)" % (
            first_name, answer)
        button = InlineKeyboardButton("🐏", callback_data="羊_%s_%s_3" % (answer, user_id))
        button1 = InlineKeyboardButton("🐓", callback_data="鸡_%s_%s_3" % (answer, user_id))
        button2 = InlineKeyboardButton("🐅", callback_data="老虎_%s_%s_3" % (answer, user_id))
        button3 = InlineKeyboardButton("🐘", callback_data="大象_%s_%s_3" % (answer, user_id))

        buttons_row = [button, button1, button2, button3]
        button4 = InlineKeyboardButton("解禁✅", callback_data="admin_pass_%s" % user_id)
        button5 = InlineKeyboardButton("踢出🦶", callback_data="admin_out_%s" % user_id)

        row2 = [button4, button5]
        keyboard = InlineKeyboardMarkup([buttons_row, row2])
        message = context.bot.send_message(chat_id=chat_id, text=content, reply_markup=keyboard,
                                           parse_mode=ParseMode.HTML)
        with app.app_context():
            obj = Newone(create_time=datetime.now(), first_name=first_name, t_id=user_id, status=2, chat_id=chat_id,
                         message_id=message.message_id)
            try:
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^羊_%s_%s_3' % (answer, user_id)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^鸡_%s_%s_3' % (answer, user_id)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^老虎_%s_%s_3' % (answer, user_id)))
        dispatcher.add_handler(CallbackQueryHandler(yan, pattern='^大象_%s_%s_3' % (answer, user_id)))
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_pass_%s' % user_id))
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_out_%s' % user_id))


def handle_left_chat_member(update, context):
    context.bot.delete_message(update.message.chat_id, update.message.message_id)


def op_chat_title(update, context):
    context.bot.delete_message(update.message.chat_id, update.message.message_id)


def op_chat_photo(update, context):
    context.bot.delete_message(update.message.chat_id, update.message.message_id)


def filter_chinese(text):
    # 使用正则表达式匹配中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fa5]')
    # 使用 join() 方法将匹配到的中文字符拼接成字符串
    chinese_text = ''.join(re.findall(chinese_pattern, text))
    return chinese_text


def keyword_counter(update, context):
    text = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user["id"]
    first_name = update.message.from_user["first_name"]
    filtertext = filter_chinese(text)
    message_id = update.message.message_id
    words = jieba.lcut(filtertext, cut_all=False)
    if str(user_id) in Admin_li:
        return

    # 过滤不必要的关键词匹配 TODO

    if any(word in banned_words_filter for word in words):
        # 用户发送了包含关键词的消息，进行禁言操作
        try:
            context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                ),
                until_date=time.time() + 300  # 设置禁言时间
            )
        except Exception as e:
            print(e)
            return
        context.bot.delete_message(chat_id, message_id)
        button4 = InlineKeyboardButton("解禁✅", callback_data="admin_pass_%s" % user_id)
        button5 = InlineKeyboardButton("踢出🦶", callback_data="admin_out_%s" % user_id)

        row2 = [button4, button5]
        keyboard = InlineKeyboardMarkup([row2])
        context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.HTML, reply_markup=keyboard,
                                 text="<code>%s</code> 发送的消息包含敏感词汇，已被禁言5分钟。" % first_name
                                 )
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_pass_%s' % user_id))
        dispatcher.add_handler(CallbackQueryHandler(adminyan, pattern='^admin_out_%s' % user_id))

    with app.app_context():
        # 精准关键词回复
        try:
            w_obj = Word_reply.query.filter_by(word=text).first()
        except Exception as e:
            print(e)
            w_obj = None
        if w_obj:
            r_text = w_obj.reply_text
            context.bot.send_message(chat_id=chat_id, text=r_text, reply_to_message_id=message_id,
                                     parse_mode=ParseMode.HTML)

        # 包含关键词回复
        for word in words:
            try:
                w_obj = Word_h_reply.query.filter(Word_h_reply.word.ilike('%' + word + '%')).first()
            except Exception as e:
                print(e)
                continue
            if not w_obj:
                continue
            r_text = w_obj.reply_text
            context.bot.send_message(chat_id=chat_id, text=r_text, reply_to_message_id=message_id,
                                     parse_mode=ParseMode.HTML)
            break

        print(words)
        # 关键词统计
        for word in words:
            try:
                obj = Keywords(id=str(int(time.time() * 100000)), word=word, create_time=datetime.now(),
                               t_id=user_id)
            except Exception as e:
                print(e)
                continue
            try:
                db.session.add(obj)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
                continue

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, keyword_counter))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, op_chat_title))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_photo, op_chat_photo))
dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, handle_left_chat_member))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))
# 用户命令功能
dispatcher.add_handler(CommandHandler('id', get_id))
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('recharge', recharge))
dispatcher.add_handler(CommandHandler('add_reply_word', add_reply_word))
dispatcher.add_handler(CommandHandler('add_ban_word', add_ban_word))
dispatcher.add_handler(CommandHandler('add_hword', add_hword))
dispatcher.add_handler(CommandHandler('del_reply_word', del_reply_word))
dispatcher.add_handler(CommandHandler('del_ban_word', del_ban_word))
dispatcher.add_handler(CommandHandler('del_hword', del_hword))
dispatcher.add_handler(CommandHandler('words', words))
dispatcher.add_handler(CommandHandler('ban_words', ban_words))
dispatcher.add_handler(CommandHandler('hwords', hwords))

# 功能分析
# 3.关键词统计(今日排行，今月排行，7天排行)
# 4.用户发送聊天内容计数统计(今日排行，今月排行，7天排行)


t1 = threading.Thread(target=update_yan_task)
t1.start()

t2 = threading.Thread(target=update_wallet_task)
t2.start()

try:
    print("机器人开始工作中！")
    updater.start_polling()
    updater.idle()
except Exception:
    updater.stop()

if __name__ == '__main__':
    manager.run()
