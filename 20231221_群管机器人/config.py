import redis

# 管理员ID
Admin_li = ["1707841429"]
# 通知群聊ID
Group_li = ["1707841429"]

TOKEN = ""
Bot_name = "manager120Bot"

# 创建一个代理配置字典
proxy_config = {
    'proxy_url': 'https://127.0.0.1:7890',
}


class Config(object):
    """配置信息"""
    DEBUG = True
    SECRET_KEY = "ASDSADSADUIHXC*&#*&"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@127.0.0.1:3306/managerbot"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask-session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # 一天过期


Text_data = {
    "cn": {
        "withdraw_arrival": "亲爱的用户：%s\n您的下分订单已完成\n金额<b>%s</b> USDT已到账，请查收",
        "start_com": "开始使用机器人",
        "create_invite": "创建邀请链接",
        "help_com": "帮助信息",
        "auto_recharge_btn": "自动充值",
        "turn_order_false": "取消订单失败，请联系客服：@%s",
        "create_order_false": "创建订单失败，请联系客服：@%s",
        "order_not_found": "取消失败，订单不存在！请联系客服：@%s",
        "order_move_info": "<b>亲爱的客户：%s\n您的订单id为：%s\n已被取消</b>\n\n➖➖➖➖➖➖➖➖➖➖\n订单创建时间：%s\n转账金额: %s USDT\n➖➖➖➖➖➖➖➖➖➖\n",
        "close": "关闭",
        "move_order": "取消订单",
        "contact_customer": "联系客服",
        "remain_pack": "🧧抢红包[%s/0]总%sU 雷%s",
        "rob_false": "抢包失败！",
        "user_send_pack": "[ <code>%s</code> ] 发了个%s U红包,快来抢!",
        "settle_rob_order": "[ <code>%s</code> ]的红包已被领完!.\n🧧红包金额: %sU\n🛎红包包数: %s\n💥红包倍数: %s\n💥中雷数字: %s\n\n--------领取详情--------\n",
        "had_rob": "您已抢过该红包了！",
        "rob_packet_body": "\n\n💹 中雷盈利： %s\n💹 发包成本： -%s\n💹 包主实收： %s\n",
        "lei": "中雷",
        "no_lei": "未中雷",
        "welcome_user": "👏👏 欢迎 ID: <code>%s</code>",
        "search_false": "查询出错!",
        "help_info": "【1】由玩家发送发包指令，红包机器人在群内按指令发包，指令为[10-5]（机器人发送金额为 10 的红包，雷值为 5，红包数量固定6个，抢包者抢到金额的尾数是5的即中雷；\n【2】用户中雷后需赔付发包者金额1.8倍即18\n【3】雷值可设置1-9的任意一个数；\n【4】平台抽发包者盈利的2.50%，下分提现秒到账。\n【5】平台方不参与玩家的游戏盈利，全力保障公平资金安全、公平的游戏环境！\n----------------------\n【5】玩家发送:发包10/5,10/5,发10-5都可以\n【6】玩家发送:余额、ye、查可以查看余额\n【7】财务可以引用别人的话发送上分下分+金额，进行手动上下分\n【8】群组将机器人设置为管理员才可以使用\n【9】群组设置隐藏,用户邀请人会自动返利并成为下级用户\n【10】发送/invite获取专属链接,用户通过链接加入会自动返利并成为下级用户",
        "official_group": "官方群组",
        "wanfa": "玩法",
        "recharge_tips": "🚫请移至机器人界面进行充值🚫",
        "recharge": "充值",
        "balance": "余额",
        "kefu": "客服",
        "tuiguang_search": "推广查询",
        "official_channel": "官方频道",
        "today_record_btn": "今日报表",
        "invite_link": "您的专属链接为: \n%s\n(用户加入自动成为您的下级用户)",
        "today_record": "今日报表: <code>%s</code>\n--------\n发包支出：<b>-%s USDT</b>\n发包盈利：<b>%s USDT</b>\n--------\n我发包玩家中雷上级代理抽成：<b>-%s USDT</b>\n我发包玩家中雷平台抽成：<b>-%s USDT</b>\n--------\n抢包收入：<b>%s USDT</b>\n抢包中雷赔付：<b>-%s USDT</b>\n--------\n邀请返利：<b>%s USDT</b>\n下级中雷返点: <b>%s USDT</b>\n--------\n豹子与顺子总奖励：<b>%s USDT</b>\n--------\n",
        "rob_button": "🧧抢红包[%s/%s]总%sU 雷%s",
        "wanfa_info": "📢红包扫雷 玩法说明\n🔺随机抢包，保证绝对公平！公正！\n🔺集团不参与玩家之间游戏盈利\n🔺全力保障游戏、资金公平环境\n🔺集团抽发包者玩家流水的的4%\n🔺代理可享受邀请下级会员发包盈利1.60%\n\n最新活动：\n邀请成员进群账户自动返现0.10U\n下级成员发包盈利，上级返现 1.60%",
        "snatch_line": "抢到: %s USDT\n%s\n余额: %s USDT",
        "account_error": "余额不足%s，或账号异常！",
        "red_envelope_empty": "红包已被抢完！",
        "big_shunzi": "👏👏 恭喜[ <code>%s</code> ] 抢到大顺，奖励58.88U已到账!",
        "small_shunzi": "👏👏 恭喜[ <code>%s</code> ] 抢到小顺，奖励5.88U已到账!",
        "big_baozi": "👏👏 恭喜[ <code>%s</code> ] 抢到大豹子，奖励58.88U已到账!",
        "small_baozi": "👏👏 恭喜[ <code>%s</code> ] 抢到小豹子，奖励5.88U已到账!",
        "again_recharge": "再次充值",
        "order_recharge_success": "订单充值成功！",
        "send_packet_range": "🚫发包失败，发包金额范围5-5000 USDT🚫",
        "send_false": "🚫发包失败🚫",
        "today_record_false": "查询今日报表，需要在机器人界面完整第一次交互。",
        "yue_not_enough": "🚫您的余额已不足发包,当前余额:%s",
        "search_time_out": "查询过期!",
        "search_time_out_sorry": '非常抱歉！您的请求已过期。',
        "my_money": "%s\n%s\n---------------------------------\nID号：%s\n余额：%sU\n",
        "recharge_info": "—————💰大发国际充值活动💰—————\n大发国际首充50u以上，赠送10%%\n——————————————\n优惠政策  可联系客服： @%s\n\n 更变日期： 2023.6.1  \n\n请选择充值金额👇",
        "order_time_out": "订单已超时！",
        "invite_info": "您的id为：%s\n累计邀请：%s\n----------\n显示最后十条邀请\n----------\n",
        "invite_line": "%s，用户ID：%s\n",
        "create_order_info": "<b>充值订单创建成功，订单有效期为10分钟，请立即支付！</b>\n\n➖➖➖➖➖➖➖➖➖➖\n转账地址: <code>%s</code> (TRC-20网络)\n转账金额: %s USDT 注意小数点！！！\n转账金额: %s USDT 注意小数点！！！\n转账金额: %s USDT 注意小数点！！！\n➖➖➖➖➖➖➖➖➖➖\n请注意转账金额务必与上方的转账金额一致，否则无法自动到账\n支付完成后, 请等待1分钟左右查询，自动到账。\n订单创建时间：%s",
        "today_text_info": "今日报表已发送至个人中心，请注意查收！",
        "user_not_found": "未查询到用户信息，请移步机器人中心进行注册使用！",
        "recharge_arrival": "亲爱的用户：%s\n您的充值订单已完成\n金额<b>%s</b> USDT已到账，请查收",
        "pic_name": "upic_cn.jpg",
    },
    "en": {
        "pic_name": "upic_en.jpg",
        "withdraw_arrival": "Dear user: <b>%s</b>\nyour sub order has been completed\nThe amount of <b>%s USDT</b> has been received. Please check your account!",
        "recharge_arrival": "Dear user：<b>%s</b>\nYour recharge order has been completed\nThe amount of <b>%s USDT</b> has been received, please check it",
        "user_not_found": "No user information found, please move to the robot center to register and use!",
        "start_com": "Start using robots",
        "create_invite": "Create invitation link",
        "help_com": "Help Information",
        "auto_recharge_btn": "Auto Recharge",
        "today_record_false": "Dear User: <code>%s</code>.To query today's report, it is necessary to have a complete first interaction on the robot interface.",
        "turn_order_false": "Cancel order failed, please contact customer service:@%s",
        "create_order_false": "Order creation failed, please contact customer service:@%s",
        "order_not_found": "Cancel failed, order does not exist! Please contact customer service:@%s",
        "order_move_info": "<b>Dear customer：%s\nyour order ID is：%s has been cancelled</b>\n\n➖➖➖➖➖➖➖➖➖➖\nOrder creation time：%s\nTransfer amount: %s USDT\n➖➖➖➖➖➖➖➖➖➖\n",
        "close": "Close",
        "remain_pack": "🎁Seizing red packets [%s/0] Total %sU Mine %s",
        "user_send_pack": "[ <code>%s</code> ] sent a %s U red envelope, come and grab it!",
        "move_order": "Cancellation Order",
        "contact_customer": "Contact Customer",
        "rob_false": "Failed to grab the package!",
        "settle_rob_order": "[ <code>%s</code> ]has been claimed!.\n🎁Red envelope amount: %sU\n🛎Number of red packets: %s\n💥Red envelope multiple: %s\n💥Mine Number: %s\n\n--------Claim Details--------\n",
        "had_rob": "You have already snatched the red envelope!",
        "rob_packet_body": "\n\n💹 Mine Profit： %s\n💹 Contract Cost： -%s\n💹 Owner's Actual Income： %s\n",
        "lei": "Mine",
        "today_text_info": "Today's report has been sent to the personal center, please check it carefully!",
        "recharge_tips": "🚫Please move to the robot interface to recharge!🚫",
        "no_lei": "No Mine",
        "welcome_user": "👏👏 Welcome ID: <code>%s</code>",
        "search_false": "Query error!",
        "help_info": "\n✈️【WG International】- USDT red envelope minesweeper TG group ✈️\n\n1️⃣ No registration required, just recharge USDT to start the game, send red envelopes or grab red envelopes\n\n2️⃣ Telegram group betting amount: 5U-5000U❤️\n\n3️⃣After the player sends any command in the group, the robot will distribute red envelopes on his behalf.\n\n4️⃣The thunder number can be set to any number from 0 to 9, such as 20-1 or 20/1.\n\n5️⃣The number of red envelopes is fixed at 6, and those who grab the red envelopes will pay a fixed compensation of 1.8 times the principal.\n\n6️⃣The gameplay of this group is for public welfare. Winning and losing are all gambling between players.\n\n7️⃣WG Group does not participate in the game, it is fair and just, WG takes 4% of the profits from those who make profit from the contract\n\n8️⃣Invite new members to the group and the inviter’s account will automatically receive 0.1U cash back. Cash can be withdrawn after reaching 10U. Note: There is one or more valid customers.",
        "official_group": "Official Group",
        "wanfa": "Playing Method",
        "recharge": "Recharge",
        "balance": "Balance",
        "kefu": "Customer Service",
        "tuiguang_search": "Promotion Query",
        "official_channel": "Official Channel",
        "today_record_btn": "Today Report",
        "invite_link": "Your exclusive link is: \n%s\n(users joining will automatically become your subordinate users)",
        "today_record": "Today's report: <code>%s</code>\nSend REDPACK Payout: <b>-%s USDT</b>\nSend REDPACK Profit: <b>%s USDT</b>\nAgent commission: <b>-%s USDT</b>\nPlatform commission: <b>-%s USDT</b>\nIncome from grabbing red envelopes: <b>%s USDT</b>\nLoss from grabbing red envelopes: <b>-%s USDT</b>\nInvitation Rebate: <b>%s USDT</b>\nLower-level Agent rebate: <b>%s USDT</b>\nLeopard and Shunzi Total Reward: <b>%s USDT</b>",
        "rob_button": "🎁Seizing red packets [%s/%s] Total %sU Mine %s",
        "wanfa_info": "✅Introduction to WG International Red Envelope Minesweeper Game Rules\n\n❤️The player sends the Red Envelope sending instructions in the group, and the red envelope robot distributes the Red Envelope according to the instructions in the group and deducts the corresponding amount (6 copies per Red Envelope)\nFor example: The command is to send 100-5 (the robot sends a red envelope with an amount of 100U, and the person who grabs the package if the amount ends in 5 will be struck)\n(After the user is hit by a mine, he needs to pay 1.8 times the amount of the contract sender, which is 180U)\n(The thunder value can be set to any number from 0 to 9)\n\n❤️The group leader takes a commission of 4% of the profit of the contract sender\n\n❤️Group owners are not immune to dead packs and do not participate in pack grabbing. The game is played between users (guaranteed fairness! Justice!)\n\n⭕️(When the balance is less than 1.8 times the amount of the package, you cannot grab the red envelope, but you can send the red envelope. It will be credited in seconds!)\n\n🔥Agent rebate mode, you can enjoy the rebate by bringing people into the group for official games",
        "snatch_line": "Caught: %s USDT\n%s\nBalance: %s USDT",
        "account_error": "The balance is less than %s, or the account is abnormal!",
        "red_envelope_empty": "The red envelope has been snatched!",
        "big_shunzi": "👏👏 Congratulations to [ <code>%s</code> ] for grabbing the Big Straight. The reward of 58.88U has been received!",
        "small_shunzi": "👏👏 Congratulations to [ <code>%s</code> ] for grabbing the Small Straight. The reward of 5.88U has been received!",
        "big_baozi": "👏👏 Congratulations to [ <code>%s</code> ] for grabbing the Big Leopard. The reward of 58.88U has been received!",
        "small_baozi": "👏👏 Congratulations to [ <code>%s</code> ] for grabbing the Small Leopard. The reward of 5.88U has been received!",
        "again_recharge": "Recharge Again",
        "order_recharge_success": "Order recharge successful!",
        "send_packet_range": "🚫Contract failure, contract amount range 5-5000 USDT🚫",
        "send_false": "🚫Contract failure🚫",
        "yue_not_enough": "🚫Your balance is insufficient for contracting, current balance:%s",
        "search_time_out": "Query expired!",
        "search_time_out_sorry": "I'm very sorry! Your request has expired.",
        "my_money": "%s\n%s\n---------------------------------\nID：%s\nBalance：%sU\n",
        "recharge_info": "—————💰WG International Recharge Activity💰—————\nWG International offers a 10%% bonus for first recharge of over 50u, which only requires double the amount of cash to withdraw.\n——————————————\nPreferential policies can be contacted by customer service at： @%s \n\nPlease select the recharge amount👇",
        "order_time_out": "Order has timed out!",
        "invite_info": "Your ID is：%s\nAccumulated invitations：%s\n----------\nDisplay the last ten invitations\n----------\n",
        "invite_line": "%s，User ID：%s\n",
        "create_order_info": "<b>The recharge order has been successfully created and is valid for 10 minutes. Please make the payment immediately!</b>\n\n➖➖➖➖➖➖➖➖➖➖\nTransfer address: <code>%s</code> (TRC-20 network)\nTransfer amount: %s USDT Pay attention to the decimal point！！！\nTransfer amount: %s USDT Pay attention to the decimal point！！！\nTransfer amount: %s USDT Pay attention to the decimal point！！！\n➖➖➖➖➖➖➖➖➖➖\nPlease note that the transfer amount must be consistent with the transfer amount above, otherwise it will not be automatically credited to the account\nAfter the payment is completed, please wait for about 1 minute for the query to be automatically credited.\nOrder creation time：%s",
    },
}
