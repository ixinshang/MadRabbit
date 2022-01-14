import re
import subprocess
from jinja2 import Environment, PackageLoader, select_autoescape
from sanic import Blueprint, json

import sanic.request

from App.config.Config import config, get_ql_config
from App.ext import jd_browser
from App.utils import get_img_base64, get_nickname
from ql import RemoteQL

Api_bp = Blueprint('apis', url_prefix='/api')
Api_bp.static("/", "./App/static2")

env = Environment(
    loader=PackageLoader('App', 'templates'),
    autoescape=select_autoescape(['html', 'xml', 'tpl']))


@Api_bp.route("/Title", methods=["POST", "GET"])
def Title(requests: sanic.Request):
    return json({"success": True, "message": "", "data": {"title": config.get("Title")}})


@Api_bp.route("/Config", methods=["POST", "GET"])
async def Config(requests):
    ql_list = []
    for ql in config.get("Config"):
        ql_dict = {
            "qLkey": ql.get("QLkey"),
            "qlName": ql.get("QLName"),
            "qL_CAPACITY": ql.get("QL_CAPACITY")
        }
        ql_list.append(ql_dict)
    ql_config = get_ql_config(1)
    ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
    data = {
        "success": True,
        "message": "",
        "data": {
            "type": "ql",
            "list": ql_list,
            "closetime": config.get("Closetime", 5),
            "autocount": config.get("AutoCaptchaCount", 5),
            "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
            "tabcount": config.get("MaxTab", 4),
            "announcement": config.get("Announcement"),
            "wskeycount": 30
        }
    }
    return json(data)


@Api_bp.route("SendSMS", methods=["POST"])
async def SendSMS(request: sanic.Request):
    data = request.json
    qlkey = data.get("qlkey")
    try:
        if await jd_browser.get_page_by_phone(int(data["Phone"])):
            await jd_browser.destroy_browser(int(data["Phone"]))
        if not await jd_browser.creat_page(int(data["Phone"])):
            res = {
                "success": False,
                "message": "代理出错",
                "data": {
                }
            }
            return json(res)
        subprocess.Popen(['python', 'destroy_browser.py', str(data["Phone"]), str(config.get("Closetime", "5"))])
    except Exception as e:
        print(e)
        await jd_browser.destroy_browser(int(data["Phone"]))
        res = {
            "success": False,
            "message": "代理出错",
            "data": {
            }
        }
        return json(res)
    try:
        state, small_img_base64, cpc_img_base64, message = await jd_browser.sendSMS(int(data["Phone"]))
    except Exception as e:
        print(e)
        await jd_browser.destroy_browser(int(data["Phone"]))
        res = {
            "success": False,
            "message": "代理出错",
            "data": {
            }
        }
        return json(res)
    ql_config = get_ql_config(int(qlkey))
    ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
    print("send_message", state, message, cpc_img_base64)
    if state and not cpc_img_base64 and not message:
        res = {
            "success": True,
            "message": "",
            "data": {
                "status": 666,
                "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
                "tabcount": 3,
                "big": "",
                "small": ""
            }
        }

    elif not state and message:
        res = {
            "success": False,
            "message": message,
            "data": {
                "status": 505,
                "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
            }
        }
    else:
        res = {
            "success": False,
            "message": "出现安全验证,",
            "data": {
                "status": 666,
                "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
                "tabcount": 3,
                "big": get_img_base64(small_img_base64),
                "small": get_img_base64(cpc_img_base64)
            }
        }
    return json(res)


@Api_bp.route("AutoCaptcha", methods=["POST"])
async def AutoCaptcha(request):
    data = request.json
    phone = data.get("Phone")
    msg = await jd_browser.AutoCaptcha(int(phone))
    if type(msg) == bool:
        if msg:
            response_data = {
                "success": True,
                "message": "",
                "data": {}
            }
        else:
            status, page = await jd_browser.get_page_by_phone(int(phone))
            small_img_base64, cpc_img_base64 = await jd_browser.get_captcha_img(page)
            response_data = {
                "success": False,
                "message": "验证失败",
                "data": {
                    "status": 666,
                    "big": get_img_base64(small_img_base64),
                    "small": get_img_base64(cpc_img_base64)
                }
            }
    else:
        response_data = {
            "success": False,
            "message": msg,
            "data": {
                "status": 505
            }
        }
    return json(response_data)


@Api_bp.route("VerifyCode", methods=["POST"])
async def VerifyCode(request):
    data = request.json
    phone = data.get("Phone")
    code = data.get("Code")
    qlkey = data.get("qlkey")
    ql_config = get_ql_config(int(qlkey))
    status = await jd_browser.login(int(phone), str(code))
    if not status:
        res = {"success": False, "message": "未找到当前号码的网页请稍候再试,或者网页超过5分钟已被回收", "data": {"status": 404}}
    else:
        cookies = await jd_browser.get_cookie(int(phone))
        await jd_browser.destroy_browser(int(phone))
        if cookies:
            pin = re.findall("pt_pin=.*?;", cookies)[0]
            ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
            item = await ql.get_item_by_pin(pt_pin=pin)
            if item:
                # 青龙已存在ck
                if await ql.update_by_all(item["name"], cookies, item["remarks"], item["_id"]):
                    # 更新成功
                    item = await ql.get_item_by_pin(pt_pin=pin)
                    res = {
                        "success": True,
                        "message": "",
                        "data": {
                            "qlid": item["_id"],
                            "nickname": f"{pin}",
                            "timestamp": item["timestamp"],
                            "remarks": item["remarks"],
                            "qlkey": qlkey,
                            "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
                            "tabcount": config.get("MaxTab") - jd_browser.get_browser_num()
                        }
                    }
                else:
                    # 青龙更新失败
                    res = {
                        "success": False,
                        "message": "青龙更新失败，可能青龙配置有误",
                        "data": {}
                    }
            else:
                # 青龙不存在ck
                if await ql.insert(cookies, name="JD_COOKIE"):
                    # 上传cookie
                    item = await ql.get_item_by_pin(pin)
                    res = {
                        "success": True,
                        "message": "",
                        "data": {
                            "qlid": item["id"],
                            "nickname": f"{pin}",
                            "timestamp": item["id"],
                            "remarks": item["remarks"],
                            "qlkey": qlkey,
                            "ckcount": ql_config.get("QL_CAPACITY") - await ql.get_ck_num(),
                            "tabcount": 4
                        }
                    }
                else:
                    # 上传失败
                    res = {
                        "success": False,
                        "message": "青龙上传失败，可能青龙配置有误",
                        "data": {}
                    }
        else:
            # 登陆失败
            res = {
                "success": False,
                "message": "获取cookie失败",
                "data": {}
            }
    return json(res)


@Api_bp.route("DestroyPage", methods=["POST"])
async def DestroyPage(request):
    data = request.json
    phone = data.get("phone")
    status, page = await jd_browser.get_page_by_phone(phone)
    if not status:
        return json({"success": True})
    await jd_browser.destroy_browser(int(phone))
    return json({"success": True})


@Api_bp.route("User")
async def GetUser(request):
    data = request.get_args()
    qlid = data.get("qlid")
    qlkey = data.get("qlkey")
    ql_config = get_ql_config(int(qlkey))
    ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
    item = await ql.get_item_by_qlid(qlid)
    if item:
        res = {
            "success": True,
            "message": "",
            "data": {
                "qlid": qlid,
                "qlkey": 1,
                "ck": item["value"],
                "timestamp": item["timestamp"],
                "remarks": item["remarks"],
                "nickname": await get_nickname(item["value"]),
                "qrurl": ql_config.get("QRurl")
            }
        }
    else:
        res = {
            "success": False,
            "message": "该容器没找到该用户",
            "data": {}
        }
    return json(res)


@Api_bp.route("Upremarks", methods=["POST"])
async def Up_remarks(request):
    data = request.json
    qlid = data.get("qlid")
    qlkey = data.get("qlkey")
    remarks = data.get("remarks")
    ql_config = get_ql_config(int(qlkey))
    ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
    item = await ql.get_item_by_qlid(qlid)
    if item:
        try:
            if await ql.update_by_all("JD_COOKIE", item["value"], remarks, qlid):
                res = {
                    "success": True,
                    "message": "",
                    "data": {}
                }
            else:
                res = {
                    "success": False,
                    "message": "更新失败",
                    "data": {}
                }
        except Exception as e:
            res = {
                "success": False,
                "message": str(e),
                "data": {}
            }
    else:
        res = {
            "success": False,
            "message": "该容器没找到该用户",
            "data": {}
        }
    return json(res)


@Api_bp.route("del", methods=["POST"])
async def Delete_ck(request):
    data = request.json
    qlid = data.get("qlid")
    qlkey = data.get("qlkey")
    ql_config = get_ql_config(int(qlkey))
    ql = RemoteQL(ql_config["QL_CLIENTID"], ql_config["QL_SECRET"], ql_config["QLhost"], ql_config["QLport"])
    try:
        if await ql.delete([qlid]):
            res = {
                "success": True,
                "message": "",
                "data": {}
            }
        else:
            res = {
                "success": False,
                "message": "删除失败",
                "data": {}
            }
    except Exception as e:
        res = {
            "success": False,
            "message": str(e),
            "data": {}
        }
    return json(res)


@Api_bp.route("RefreshPage", methods=["POST"])
async def RefreshPage(request):
    data = request.json
    print(data)
    now = data.get("schedule", True)
    await jd_browser.refresh_page(now)
    return json({"success": True})
