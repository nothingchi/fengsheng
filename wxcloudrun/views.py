from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import hashlib
import xmltodict
import time
import random

numPlayerConfig = [
[], #1
[], #2
[], #3
[], #4
[], #5
[], #6
[], #7
[5, 1, 1, 1], #8
[5, 2, 1, 1], #9
[7, 0, 2, 1], #10
[7, 1, 2, 1], #11
[7, 2, 2, 1], #12
[9, 0, 3, 1], #13
[9, 1, 3, 1], #14
[9, 2, 3, 1] #15
]

roles = {
"villagers": ["洗衣妇人", "图书管理员", "调查员", "厨师", "僧侣", "共情者", "占卜师", "守鸦人", "士兵", "市长", "杀手", "掘墓人", "圣女"],
"outsider": ["圣徒", "酒鬼", "隐士", "管家"],
"minions": ["荡妇", "男爵", "间谍", "下毒者"],
"demon": ["小恶魔"]
}

rooms = {}

@app.route('/', methods=['POST', 'GET'])
def index():
    """
    :return: 返回index页面
    """
    results = []
    if request.method == "POST":
        form_data = request.form
        NumPlayer = int(form_data.get("NumPlayer"))
        if NumPlayer > 15 or NumPlayer < 8:
            return "fake news"
        NumIndex = NumPlayer - 1
        numConfig = numPlayerConfig[NumIndex]
        villagersNum = numConfig[0]
        outsiderNum = numConfig[1]
        minionsNum = numConfig[2]
        demonNum = numConfig[3]
        # 首先抽取爪牙看是否有男爵
        random.shuffle(roles["minions"])
        minions = roles["minions"][0: minionsNum]
        if "男爵" in minions:
            villagersNum -= 2
            outsiderNum += 2
        # 抽取外来者看是否有酒鬼
        random.shuffle(roles["outsider"])
        outsider = roles["outsider"][0: outsiderNum]
        if "酒鬼" in outsider:
            villagersNum += 1 #内置一张酒鬼牌
        random.shuffle(roles["villagers"])
        villagers = roles["villagers"][0: villagersNum]

        # 如果有酒鬼，在村名中随机标记一个
        if "酒鬼" in outsider:
            ran_ind = random.randint(0, len(villagers) - 1)
            villagers[ran_ind] = villagers[ran_ind] + "(酒鬼)"

        for role in villagers:
            results.append(("村民", role))

        for role in outsider:
            if "酒鬼" == role:
                continue
            # 如果有隐士，在恶魔，爪牙，隐士中随机内置一个身份
            if "隐士" == role:
                random_inside_role = random.choice(["恶魔", "间谍", "荡妇", "男爵", "下毒者", "隐士"])
                role = role + "({})".format(random_inside_role)
            results.append(("外来者", role))
        for role in minions:
            # 如果有间谍，在村民，外来者，间谍中随机内置一个身份
            # 为了避免套娃逻辑，间谍不会被内置为隐士和酒鬼
            if "间谍" == role:
                tmpRoles = ["管家", "圣徒", "间谍"]
                tmpRoles.extend(roles["villagers"])
                random_inside_role = random.choice(tmpRoles)
                role = role + "({})".format(random_inside_role)
            results.append(("爪牙", role))
        results.append(("恶魔", "小恶魔"))

        roomid = str(random.randint(1000, 9999))
        while roomid in rooms:
            roomid = str(random.randint(1000, 9999))
        rooms[roomid] = results
        ind = 1
        for role in results:
            role_roomid = roomid + str(ind)
            rooms[role_roomid] = role
            ind += 1

    return render_template('index.html', results=results)


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()
    print(request)
    print(params) 
    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        result = random.choice(roles)
        '''
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)
        '''
        return make_succ_response(result)
    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/wechatinterface', methods=['GET', 'POST'])
def msg_deal():
    if request.method == "GET":
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        if not echostr:
            return "404"
        return echostr
    if request.method == "POST":
        xml_str = request.data
        xml_dict = xmltodict.parse(xml_str)
        xml_dict = xml_dict.get("xml")
        FromUserName = xml_dict.get("FromUserName")
        ToUserName = xml_dict.get("ToUserName")
        msg_type = xml_dict.get("MsgType")
        msg = xml_dict.get("Content")
        if msg_type == "text":
            # 判断是否为房间号 + 座位号
            if (len(msg) == 5 or len(msg) == 6) and msg.isdigit():
                if msg in rooms:
                    rep_text = "你的角色是：" + rooms[msg]
                else:
                    rep_text = "房间号输错了，蠢0"
            elif "染" in msg:
                if msg.split("染")[1].isdigit():
                    numPlayer = int(msg.split("染")[1])
                    roomid = generate_roles(numPlayer)
                    if roomid != "-1":
                        rep_roomid = "房间号：{}\n".format(roomid)
                        rep_mod = "板子：灾祸滋生\n"
                        rep_numPlayers = "人数：{}\n".format(numPlayer)
                        rep_roles = "\n"
                        for ind, role in rooms[roomid]:
                            rep_roles += "{}号: {} {}\n".format(ind, role[0], role[1])
                        rep_text = rep_roomid + rep_mod + rep_numPlayers + rep_roles
                    else:
                        rep_text = "人数错了，8-15人"
                else:
                    rep_text = "格式错了，例子：染10"
            else:
                rep_text = "知道了，别发了"
            resp_dict = make_msg(ToUserName, FromUserName, rep_text)
        resp_xml_str = xmltodict.unparse(resp_dict)
        return resp_xml_str

def make_msg(ToUserName, FromUserName, text):
    resp_dict = {
        "xml": {
        "ToUserName": ToUserName,
        "FromUserName": FromUserName,
        "CreateTime": int(time.time()),
        "MsgType": "text",
        "Content": text
        }
    }

    return resp_dict

def generate_roles(numPlayers):
    results = []
    NumPlayer = numPlayers
    if NumPlayer > 15 or NumPlayer < 8:
        return "-1"
    NumIndex = NumPlayer - 1
    numConfig = numPlayerConfig[NumIndex]
    villagersNum = numConfig[0]
    outsiderNum = numConfig[1]
    minionsNum = numConfig[2]
    demonNum = numConfig[3]
    # 首先抽取爪牙看是否有男爵
    random.shuffle(roles["minions"])
    minions = roles["minions"][0: minionsNum]
    if "男爵" in minions:
        villagersNum -= 2
        outsiderNum += 2
    # 抽取外来者看是否有酒鬼
    random.shuffle(roles["outsider"])
    outsider = roles["outsider"][0: outsiderNum]
    if "酒鬼" in outsider:
        villagersNum += 1 #内置一张酒鬼牌
    random.shuffle(roles["villagers"])
    villagers = roles["villagers"][0: villagersNum]

    # 如果有酒鬼，在村名中随机标记一个
    if "酒鬼" in outsider:
        ran_ind = random.randint(0, len(villagers) - 1)
        villagers[ran_ind] = villagers[ran_ind] + "(酒鬼)"

    for role in villagers:
        results.append(("村民", role))

    for role in outsider:
        if "酒鬼" == role:
            continue
        # 如果有隐士，在恶魔，爪牙，隐士中随机内置一个身份
        if "隐士" == role:
            random_inside_role = random.choice(["恶魔", "间谍", "荡妇", "男爵", "下毒者", "隐士"])
            role = role + "({})".format(random_inside_role)
        results.append(("外来者", role))
    for role in minions:
        # 如果有间谍，在村民，外来者，间谍中随机内置一个身份
        # 为了避免套娃逻辑，间谍不会被内置为隐士和酒鬼
        if "间谍" == role:
            tmpRoles = ["管家", "圣徒", "间谍"]
            tmpRoles.extend(roles["villagers"])
            random_inside_role = random.choice(tmpRoles)
            role = role + "({})".format(random_inside_role)
        results.append(("爪牙", role))
    results.append(("恶魔", "小恶魔"))

    roomid = str(random.randint(1000, 9999))
    while roomid in rooms:
        roomid = str(random.randint(1000, 9999))
    rooms[roomid] = results
    ind = 1
    random.shuffle(results)
    final_results = []
    for role in results:
        role_roomid = roomid + str(ind)
        rooms[role_roomid] = role
        final_results.append((ind, role))
        ind += 1
    return roomid
