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
@app.route('/', methods=['POST'])
def index():
    """
    :return: 返回index页面
    """
    if request.method == "POST":
        form_data = request.form
        NumPlayer = int(form_data.get("NumPlayer"))
        results = []
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

        for role in villagers:
            results.append(("村民", role))
        for role in outsider:
            if "酒鬼" == role:
                continue
            results.append(("外来者", role))
        for role in minions:
            results.append(("爪牙", role))
        results.append(("恶魔", "小恶魔"))

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
