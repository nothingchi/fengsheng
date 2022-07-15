import random

def get_roles(msg, rooms, rooms_role_flag, config):
    if msg in rooms and msg not in rooms_role_flag:
        role = rooms[msg]
        role_0 = role.split(' ')[0]
        addition = ""
        if role_0 == "恶魔":
            emo_choice = rooms[msg[:4]+"no"]
            random.shuffle(emo_choice)
            minion_ind = []
            for ind, rolea in rooms[msg[:4]]:
                if rolea[0] == "爪牙":
                    minion_ind.append(str(ind))
            addition = "\n三个不在场的角色有: {}\n你的爪牙是: {}\n".format(" ".join(emo_choice[0:3]), " ".join(minion_ind))
        if role_0 == "爪牙":
            emo_ind = "0"
            minion_ind = []
            for ind, rolea in rooms[msg[:4]]:
                if rolea[0] == "恶魔":
                    emo_ind = ind
                if rolea[0] == "爪牙" and msg[4:] != str(ind):
                    minion_ind.append(str(ind))
            addition = "\n你的恶魔是: {}\n你的爪牙同伴是: {}".format(emo_ind, " ".join(minion_ind))
            if "间谍" in role:
                rep_roles = "\n"
                for indt, rolet in rooms[msg[:4]]:
                    rep_roles += "{}号: {} {}\n".format(indt, rolet[0], rolet[1])
                addition += rep_roles
        if "(" in role:
            role = role.split("(")[0]
        clear_role = role.split(" ")[1]
        word = config.get(clear_role, "word")
        ability = config.get(clear_role, "ability")
        prompt = config.get(clear_role, "prompt")
        rep_text = "{}\n\n你的角色是: {}\n{}\n你的技能是: {}\n\n提示: {}\n".format(word, role, addition, ability, prompt)
        #rep_text = "你的角色是：" + role + addition
        rooms_role_flag[msg] = 1
    elif msg in rooms_role_flag:
        rep_text = "这个号码已经被人抽走啦，请确认下号码"
    else:
        rep_text = "房间号输错了，请重新确认房间号"

    return rep_text
