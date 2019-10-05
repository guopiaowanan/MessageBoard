#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime, re, os, random, json, urllib.parse, urllib.request
from flask import Flask, render_template, request, jsonify, session, abort, redirect, url_for, Response
import pymysql

app = Flask(__name__)
app.secret_key = b'\xa3P\x05\x1a\xf8\xc6\xff\xa4!\xd2\xb5\n\x96\x05\xed\xc3\xc90=\x07\x8d>\x8e\xeb'
# app.secret_key = os.urandom(24)  # 在多进程环境下有问题，session获取不了，因为每个进程的secret_key不一样，无法解密cookie

db = pymysql.connect(host="localhost", user="message_board", password="******", database="message_board", charset="utf8")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reg", methods=["GET", "POST"])
def reg_handle():
    if request.method == "GET":
        return render_template("reg.html")
    elif request.method == "POST":
        uname = request.form.get("uname")
        upass = request.form.get("upass")
        upass2 = request.form.get("upass2")
        phone = request.form.get("phone")
        verify_code = request.form.get("verify_code")
        email = request.form.get("email")

        if not (uname and uname.strip() and upass and upass2 and phone and verify_code and email):
            abort(500)

        # if re.search(r"[\u4E00-\u9FFF]", uname):
        #     abort(Response("用户名含有中文汉字！"))

        if not re.fullmatch("[a-zA-Z0-9_]{4,20}", uname):
            abort(Response("用户名不合法！"))
        
        cur = db.cursor()
        cur.execute("SELECT uid FROM mb_user WHERE uname=%s", (uname,))
        res = cur.rowcount
        cur.close()      
        if res != 0:
            abort(Response("用户名已被注册！"))

        # 密码长度介于6-15
        if not (len(upass) >= 6 and len(upass) <= 15 and upass == upass2):
            abort(Response("密码错误！"))

        if session.get(phone) != verify_code:
            abort(Response("短信验证码错误！"))

        if not re.fullmatch(r"[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+", email):
            abort(Response("邮箱格式错误！"))

        try:
            cur = db.cursor()
            cur.execute("INSERT INTO mb_user VALUES (default, %s, md5(%s), %s, %s, sysdate(), sysdate(), '1', '1')", (uname, uname + upass, phone, email))
            cur.close()
            db.commit()
        except:
            abort(Response("用户注册失败！"))

        session.pop(phone)
        # 注册成功就跳转到登录页面
        return redirect(url_for("login_handle"))

@app.route("/user_center")
def user_center():
    user_info = session.get("user_info")
    
    print(user_info)
    print(session)

    if user_info:
        return render_template("user_center.html", uname=user_info.get("uname"))
    else:
        return redirect(url_for("login_handle"))

@app.route("/logout")
def logout_handle():
    res = {"err": 1, "desc": "未登录！"}
    if session.get("user_info"):
        session.pop("user_info")
        res["err"] = 0
        res["desc"] = "注销成功！"
    
    return jsonify(res)

@app.route("/message_board", methods=["GET", "POST"])
def message_board_handle():
    if request.method == "GET":
        cur = db.cursor()
        cur.execute("SELECT uname, pub_time, content, cid FROM mb_user, mb_message WHERE mb_user.uid = mb_message.uid")
        res = cur.fetchall()
        cur.close()        
        return render_template("message_board.html", messages=res)
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            abort(Response("未登录！"))

        content = request.form.get("content")
        if content:
            content = content.strip()
            if 0 < len(content) <= 200:
                # 将留言保存到数据库
                uid = user_info.get("uid")
                pub_time = datetime.datetime.now()
                from_ip = request.remote_addr

                try:
                    cur = db.cursor()
                    cur.execute("INSERT INTO mb_message (uid, content, pub_time, from_ip) VALUES (%s, %s, %s, %s)", (uid, content, pub_time, from_ip))
                    cur.close()
                    db.commit()
                    return "留言成功！"
                except Exception as e:
                    print(e)
                    
        abort(Response("留言失败！"))

@app.route("/login", methods=["GET", "POST"])
def login_handle():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        uname = request.form.get("uname")
        upass = request.form.get("upass")

        print(uname, upass)

        if not (uname and uname.strip() and upass and upass.strip()):
            abort(Response("登录失败！"))

        if not re.fullmatch("[a-zA-Z0-9_]{4,20}", uname):
            abort(Response("用户名不合法！"))

        # 密码长度介于6-15
        if not (len(upass) >= 6 and len(upass) <= 15):
            abort(Response("密码不合法！"))    
        
        cur = db.cursor()
        cur.execute("SELECT * FROM mb_user WHERE uname=%s AND upass=MD5(%s)", (uname, uname + upass))
        res = cur.fetchone()
        cur.close()
              
        if res:
            # 登录成功就跳转到用户个人中心
            cur_login_time = datetime.datetime.now()

            session["user_info"] = {
                "uid": res[0],
                "uname": res[1],
                "upass": res[2],
                "phone": res[3],
                "email": res[4],
                "reg_time": res[5],
                "last_login_time": res[6],
                "priv": res[7],
                "state": res[8],
                "cur_login_time": cur_login_time
            }

            try:
                cur = db.cursor()
                cur.execute("UPDATE mb_user SET last_login_time=%s WHERE uid=%s", (cur_login_time, res[0]))
                cur.close()
                db.commit()
            except Exception as e:
                print(e)
            
            print("登录成功！", session)
            # return redirect(url_for("user_center"))
            return redirect("/user_center")
        else:
            # 登录失败
            print("登录失败！")
            return render_template("login.html", login_fail=1)

@app.route("/check_uname")
def check_uname():
    uname = request.args.get("uname")
    if not uname:
        abort(500)

    res = {"err": 1, "desc": "用户名已被注册！"}

    cur = db.cursor()
    cur.execute("SELECT uid FROM mb_user WHERE uname=%s", (uname,))
    if cur.rowcount == 0:
        # 用户名没有被注册
        res["err"] = 0
        res["desc"] = "用户名没有被注册！"
    cur.close()

    return jsonify(res)


@app.route("/send_sms_code")
def send_sms_code_handle():
    phone = request.args.get("phone")

    result = {"err": 1, "desc": "内部错误！"}
    verify_code = send_sms_code(phone)
    if verify_code:
        # 发送短信验证码成功
        session[phone] = verify_code
        result["err"] = 0
        result["desc"] = "发送短信验证码成功！"

    return jsonify(result)

def send_sms_code(phone):
    '''
    函数功能：发送短信验证码（6位随机数字）
    函数参数：
    phone 接收短信验证码的手机号
    返回值：发送成功返回验证码，失败返回False
    '''
    verify_code = str(random.randint(100000, 999999))

    try:
        url = "http://v.juhe.cn/sms/send"
        params = {
            "mobile": phone,  # 接受短信的用户手机号码
            "tpl_id": "162901",  # 您申请的短信模板ID，根据实际情况修改
            "tpl_value": "#code#=%s" % verify_code,  # 您设置的模板变量，根据实际情况修改
            "key": "*********",  # 应用APPKEY(应用详细页查询)
        }
        params = urllib.parse.urlencode(params).encode()

        f = urllib.request.urlopen(url, params)
        content = f.read()
        res = json.loads(content)
        
        print(res)

        if res and res['error_code'] == 0:
            return verify_code
        else:
            return False
    except:
        return False   


if __name__ == "__main__":
    app.run(port=80, debug=True)

