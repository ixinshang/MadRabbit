import json

import aiohttp


def get_img_base64(img_base64):
    img_base64 = img_base64.replace("data:image/jpg;base64,", "")
    img_base64 = img_base64.replace("data:image/png;base64,", "")
    return img_base64


def get_odd_ck_num():
    pass


async def get_nickname(cookie):
    url = "https://wq.jd.com/user/info/QueryJDUserInfo?sceneval=2"
    headers = {
        "Accept": "application/json,text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-cn",
        "Connection": "keep-alive",
        "Cookie": cookie,
        "Referer": "https://wqs.jd.com/my/jingdou/my.shtml?sceneval=2",
        "User-Agent": "jdapp;iPhone;9.4.4;14.3;network/4g;Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148;supportJDSHWK/1"
    }
    async with aiohttp.ClientSession() as session:
        session.headers.update(headers)
        async with session.post(url, json={}) as res:
            text = await res.text()
            res_json = json.loads(text)
            # res_json = await res.json()
            if res_json['retcode'] == 13:
                return "账号已过期"
            elif res_json['retcode'] == 0:
                nickname = res_json['base']["nickname"]
                return nickname
            else:
                print("京东服务器返回空数据")
                return "未知"
