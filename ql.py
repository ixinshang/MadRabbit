import json
import time

import requests


class RemoteQL:

    def __init__(self, secretId="", secretKey="", host="127.0.0.1", port="5700"):
        self.sess = requests.session()
        if secretId and secretKey:
            self.url = f"http://{host}:{port}/open"
            auth_url = f"http://{host}:{port}/open/auth/token?client_id={secretId}&client_secret={secretKey}"
            ql_token = self.sess.get(auth_url).json()
            self.sess.headers.update({"Authorization": f"Bearer " + ql_token["data"]["token"]})
        else:
            self.url = f"http://{host}:{port}/api"
            f = open("/ql/config/auth.json")
            auth = f.read()
            auth = json.loads(auth)
            username = auth["username"]
            password = auth["password"]
            ql_token = auth["token"]
            f.close()
            if ql_token == "":
                url = f"{self.url}/login?t=%s" % gettimestamp()
                data = {"username": username, "password": password}
                self.sess.get(url, data=data)
            else:
                self.sess.headers.update({"authorization": f"Bearer {ql_token}"})

    async def get_item_by_pin(self, pt_pin):
        t = await gettimestamp()
        url = f"{self.url}/envs?searchValue=%s&t=%s" % (pt_pin, t)
        r = self.sess.get(url)
        item = json.loads(r.text)["data"]
        if item:
            return item[0]
        else:
            return None

    async def get_item_by_qlid(self, qlid):
        t = await gettimestamp()
        url = f"{self.url}/envs?searchValue=%s&t=%s" % ("JD_COOKIE", t)
        r = self.sess.get(url)
        item_list = json.loads(r.text)["data"]
        for item in item_list:
            if item["_id"] == qlid:
                return item
        else:
            return None

    async def getitem(self, key):
        url = f"{self.url}/envs?searchValue=%s&t=%s" % (key, await gettimestamp())
        r = self.sess.get(url)
        item = json.loads(r.text)["data"]
        return item

    async def insert(self, data, name="DPQDTK"):
        t = await gettimestamp()
        url = f"{self.url}/envs?t=%s" % t
        self.sess.headers.update({"Content-Type": "application/json;charset=UTF-8"})
        data = generate_data(data, name)
        r = self.sess.post(url, json.dumps(data))
        if json.loads(r.text)["code"] == 200:
            return True
        else:
            return False

    async def update_by_all(self, name, value, remarks, qlid):
        item = {
            "name": name,
            "value": value,
            "remarks": remarks,
            "_id": qlid
        }
        t = await gettimestamp()
        url = f"{self.url}/envs?t=%s" % t
        self.sess.headers.update({"Content-Type": "application/json;charset=UTF-8"})
        r = self.sess.put(url, json=item)
        if json.loads(r.text)["code"] == 200:
            return True
        else:
            return False

    async def get_ck_num(self):
        return len(await self.getitem("JD_COOKIE"))

    async def update(self, data):
        t = await gettimestamp()
        url = f"{self.url}/envs?t=%s" % t
        self.sess.headers.update({"Content-Type": "application/json;charset=UTF-8"})
        r = self.sess.post(url, json.dumps(data))
        if json.loads(r.text)["code"] == 200:
            return True
        else:
            return False

    async def delete(self, data):
        t = await gettimestamp()
        url = f"{self.url}/envs?t=%s" % t
        self.sess.headers.update({"Content-Type": "application/json;charset=UTF-8"})
        r = self.sess.delete(url, json=data)
        if json.loads(r.text)["code"] == 200:
            return True
        else:
            return False


async def generate_data(data_list: list, name):
    data = []
    for one in data_list:
        data_json = {
            "value": one,
            "name": name
        }
        data.append(data_json)
    return data


async def gettimestamp():
    return str(int(time.time() * 1000))


async def get_token_and_id(items):
    return [item["value"] for item in items], [item["_id"] for item in items]


if __name__ == '__main__':
    pass
