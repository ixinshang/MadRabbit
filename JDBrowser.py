import re
import subprocess

import aiohttp
import nest_asyncio
import requests

nest_asyncio.apply()

import asyncio
import base64
import random
import threading
import time

import numpy as np

import cv2

from pyppeteer import launch
from pyppeteer.browser import BrowserContext, Browser
from pyppeteer.page import Page


def input_time_random():
    return random.randint(100, 151)


def get_captcha_offset(slide, backpg):
    slide = slide.replace("data:image/jpg;base64,", "")
    slide = slide.replace("data:image/png;base64,", "")
    backpg = backpg.replace("data:image/jpg;base64,", "")
    backpg = backpg.replace("data:image/png;base64,", "")

    slide_np = np.fromstring(base64.b64decode(slide), np.uint8)
    # slide_image = cv2.imdecode(slide_np, cv2.IMREAD_COLOR)
    slide_image = cv2.imdecode(slide_np, cv2.INTER_AREA)
    backpg_np = np.frombuffer(base64.b64decode(backpg), np.uint8)
    # template = cv2.imdecode(backpg_np, cv2.IMREAD_COLOR)
    template = cv2.imdecode(backpg_np, cv2.INTER_AREA)

    slide_image_tran_canny = cv2.GaussianBlur(slide_image, (3, 3), 0)
    slide_image_tran_canny = cv2.Canny(slide_image_tran_canny, 50, 150)

    template_tran_canny = cv2.GaussianBlur(template, (3, 3), 0)
    template_tran_canny = cv2.Canny(template_tran_canny, 50, 150)

    res = cv2.matchTemplate(slide_image_tran_canny, template_tran_canny, cv2.TM_CCOEFF_NORMED)

    min_val = np.argmax(res)

    _, x = np.unravel_index(min_val, res.shape)
    w, _ = res.shape[::-1]

    # return int(x) + 51, w
    return (int(x) + 54 / 2) * 290 / 275, w

    # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #
    # offset = max_loc[0]
    # _, w, h = slide_image.shape[::-1]
    # offset = offset*290/270
    # if offset/270 > 0.66:
    #     offset += 28
    # elif offset/270 > 0.33:
    #     offset += 28
    # else:
    #     offset += 28
    # return offset, w


async def match_cookie(cookie_list: list) -> str:
    ck = {}
    for item in cookie_list:
        name = item.get("name")
        if "pt_key" == name:
            ck["pt_key"] = item["value"]
        elif "pt_pin" == name:
            ck["pt_pin"] = item["value"]
        if ck.get("pt_key") and ck.get("pt_pin"):
            return f"pt_key={ck.get('pt_key')};pt_pin={ck.get('pt_pin')};"
    else:
        return ""


async def test_proxy(proxy):
    url = "https://plogin.m.jd.com/login/nopassword?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport" \
          "%2FLoginRedirect%3Fstate%3D2215723087%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd" \
          "%252Fnewhome.action%253Fsceneval%253D2%2526ufc%253D%2526&source=wq_passport"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=f"http://{proxy}", timeout=2) as r:
            print(r.status)
            if r.status == 200:
                return True


async def get_proxy():
    proxy = config.get("proxy")
    proxy_pool = config.get('proxy_pool')
    if proxy:
        if not await test_proxy(proxy):
            exit()
        else:
            return proxy
    elif not proxy_pool:
        return None
    while True:
        url = f"http://{proxy_pool}/random"
        res = requests.get(url)
        print(res.text)
        try:
            if await test_proxy(res.text):
                return res.text
        except Exception as e:
            print(e)


class JDBrowser:

    def __init__(self):
        self.iPhone = {
            'name': 'iPhone 6',
            'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
            # noqa: E501
            'viewport': {
                'width': 375,
                'height': 667,
                'deviceScaleFactor': 2,
                'isMobile': True,
                'hasTouch': True,
                'isLandscape': False,
            }
        }
        self.UA = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) " \
                  "Chrome/93.0.4577.82 Mobile Safari/537.36 "
        self.page_dict = {}
        self.un_user_browser = None
        self.un_use_page = None

    @staticmethod
    async def open_browser() -> Browser:
        args = {
                '--no-sandbox',
                '--disable-gpu',
                '--disable-setuid-sandbox',
            }
        proxy = await get_proxy()
        if proxy:
            args.add('--proxy-server=' + proxy)
        browser = await launch(
            args= args,
            viewport={"width": 0, "height": 0, "isMobile": True},
            dumpio=True,
            autoClose=True
        )
        return browser

    def get_browser_num(self):
        return len(self.page_dict)

    async def creat_page(self, phone: int):
        if len(self.page_dict) >= 10:
            return False
        browser = await self.open_browser()
        # browser = await browser.createIncognitoBrowserContext()
        new_page = await browser.newPage()
        await new_page.emulate(self.iPhone)
        url = "https://plogin.m.jd.com/login/nopassword?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport" \
              "%2FLoginRedirect%3Fstate%3D2215723087%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd" \
              "%252Fnewhome.action%253Fsceneval%253D2%2526ufc%253D%2526&source=wq_passport"
        try:
            await new_page.goto(url, timeout=5000)
        except Exception as e:
            print(e)
            await browser.close()
            return False
        self.page_dict[phone] = {
            "browser": browser,
            "page": new_page,
            "timestamp": int(time.time())
        }
        return True

    async def get_page_by_phone(self, phone: int) -> (bool, Page):
        if self.page_dict.get(phone):
            return True, self.page_dict[phone]["page"]
        else:
            return False, Page

    async def destroy_browser(self, phone: int):
        """
        销毁浏览器

        :param phone:
        :return:
        """
        data = self.page_dict.get(phone)
        if data:
            await data["browser"].close()
            del self.page_dict[phone]

    async def get_captcha_img(self, page):
        cpc_img = await page.Jx('html/body/div/div/div/div/div/img[@id="cpc_img"]')
        cpc_img_base64 = await (await cpc_img[0].getProperty("src")).jsonValue()
        small_img = await page.Jx('html/body/div/div/div/div/div/img[@id="small_img"]')
        small_img_base64 = await (await small_img[0].getProperty("src")).jsonValue()
        return small_img_base64, cpc_img_base64

    async def validate(self, page: Page) -> bool:
        """
        滑块验证

        :param page:
        :return:
        """
        cpc_img_base64, small_img_base64 = await self.get_captcha_img(page)

        offset, _ = get_captcha_offset(small_img_base64, cpc_img_base64)

        silder = await page.querySelector(".sp_msg > img")
        box = await silder.boundingBox()

        await page.hover('.sp_msg > img')
        await page.mouse.down()

        cur_x = box['x']
        cur_y = box['y']
        first = True
        total_delay = 0
        shake_times = 2  # 左右抖动的最大次数

        while offset > 0:
            if first:
                # 第一次先随机移动偏移量的%60~80%
                x = int(random.randint(6, 8) / 10 * offset)
                first = False
            # elif total_delay >= 2000:  # 时间大于2s了， 直接拉满
            elif total_delay >= 1500:  # 时间大于2s了， 直接拉满
                x = offset
            else:  # 随机滑动5~30px
                x = random.randint(5, 30)

            if x > offset:
                offset = 0
                x = offset
            else:
                offset -= x

            cur_x += x

            delay = random.randint(100, 250)
            steps = random.randint(5, 12)
            total_delay += delay
            # println('{}, 拼图offset:{}, delay:{}, steps:{}'.format(self.account, cur_x, delay, steps))
            await page.mouse.move(cur_x, cur_y,
                                  {'delay': delay, 'steps': steps})

            if shake_times <= 0:
                continue

            # if total_delay >= 2000:
            if total_delay >= 1500:
                continue

            num = random.randint(1, 10)  # 随机选择是否抖动
            if num % 2 == 1:
                continue

            shake_times -= 1
            px = random.randint(1, 10)  # 随机选择抖动偏移量
            delay = random.randint(100, 500)
            steps = random.randint(5, 15)
            total_delay += delay
            # 往右拉
            cur_x += px
            # println('{}, 拼图向右滑动:offset:{}, delay:{}, steps:{}'.format(self.account, px, delay, steps))
            await page.mouse.move(cur_x, cur_y,
                                  {'delay': delay, 'steps': steps})

            delay = random.randint(100, 250)
            steps = random.randint(5, 15)
            total_delay += delay

            # 往左拉
            cur_x -= px
            # println('{}, 拼图向左滑动:offset:{}, delay:{}, steps:{}'.format(self.account, px, delay, steps))
            await page.mouse.move(cur_x, cur_y,
                                  {'delay': delay, 'steps': steps})

        await page.mouse.move(offset, box["y"])
        await page.mouse.up()
        await page.waitFor(2500)
        success_key = await page.Jx('html/body/div/div/div/div/div/img[@id="small_img"]')
        if success_key:
            return False
        else:
            return True

    @staticmethod
    async def judge_success(page: Page) -> str:
        content = await page.content()
        if "短信已经发送，请勿重复提交" in content:
            return "短信已经发送，请勿重复提交"
        elif "短信验证码发送次数已达上限" in content:
            return "短信验证码发送次数已达上限"
        elif "该手机号未注册，将为您直接注册。" in content:
            return "该手机号未注册"
        elif "获取验证" in content:
            return "网络问题，获取验证码失败"
        elif "您的账号存在风险" in content:
            return "您的账号存在风险"
        else:
            return ""

    async def sendSMS(self, phone: int):
        status, page = await self.get_page_by_phone(phone)
        if not status:
            return False, None, None
        phone_login = await page.waitForSelector('input.acc-input.mobile.J_ping')
        await phone_login.click()
        await page.type('input.acc-input.mobile.J_ping', str(phone), {'delay': random.randint(10, 40)})
        sms_code = await page.querySelector("button.getMsg-btn.text-btn.J_ping.timer")
        await sms_code.click()
        now_time = time.time()
        while True:
            await page.waitFor(100)
            content = await page.content()
            if re.search(r"重新获取\(\d+s\)", content):
                return True, None, None, ""
            if time.time() - now_time >= 5:
                message = await self.judge_success(page)
                if message:
                    return False, None, None, message
            cpc_img = await page.Jx('html/body/div/div/div/div/div/img[@id="cpc_img"]')
            if cpc_img:
                cpc_img_base64, small_img_base64 = await self.get_captcha_img(page)
                return False, small_img_base64, cpc_img_base64, ""

    async def AutoCaptcha(self, phone: int):
        """
        发送短信验证码

        :param phone: int
        :return: bool
        """
        status, page = await self.get_page_by_phone(phone)
        if not status:
            return "页面已被回收"
        cpc_img = await page.Jx('html/body/div/div/div/div/div/img[@id="cpc_img"]')
        if cpc_img:
            if await self.validate(page):
                now_time = time.time()
                while True:
                    await page.waitFor(100)
                    content = await page.content()
                    if re.search(r"重新获取\(\d+s\)", content):
                        policy_page = await page.querySelector("input.policy_tip-checkbox")
                        await policy_page.click()
                        print("验证成功")
                        return True
                    if time.time() - now_time >= 2:
                        message = await self.judge_success(page)
                        if message:
                            return message
            else:
                print("验证失败")
                return False
        return True

    async def get_cookie(self, phone: int) -> str:
        """
        从浏览器中读取cookie

        :param phone:
        :return:
        """
        status, page = await self.get_page_by_phone(phone)
        if not status:
            return ""
        if page:
            await page.goto("https://home.m.jd.com/myJd/newhome.action")
            await page.waitFor(3000)
            cookies = await page.cookies()
            ck = await match_cookie(cookies)
            return ck

    async def login(self, phone: int, code: str):
        """
        点击登录

        :param phone:
        :param code:
        :return:
        """
        status, page = await self.get_page_by_phone(phone)
        if not status:
            return False
        code_page = await page.querySelector("#authcode")
        if code_page:
            await code_page.click()
            await page.type("#authcode", code, {'delay': input_time_random() - 100})
            login_page = await page.querySelector("a.btn.J_ping.btn-active")
            await login_page.click()
            return True

    async def get_page(self) -> (BrowserContext, Page):
        browser = await self.open_browser()
        # browser = await browser.createIncognitoBrowserContext()
        new_page = await browser.newPage()
        await new_page.emulate(self.iPhone)
        url = "https://plogin.m.jd.com/login/nopassword?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport" \
              "%2FLoginRedirect%3Fstate%3D2215723087%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd" \
              "%252Fnewhome.action%253Fsceneval%253D2%2526ufc%253D%2526&source=wq_passport"
        await new_page.goto(url, timeout=5000)

        return browser, new_page


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(get_proxy())
    # asyncio.get_event_loop().run_until_complete(main())
