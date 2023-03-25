import argparse
import datetime
import functools
import logging
import random
import time
from typing import Any, Dict, List

import requests
import schedule
from rich import print as rprint
from rich.logging import RichHandler

from private_data import *

logging.basicConfig(
    level="INFO",
    format="%(asctime)s.%(msecs)04d\t%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[RichHandler()],
)

log = logging.getLogger(__name__)


def order(
    areas: Dict[str, Any],
    area_names: List[int],
    site_id: str,
    bookdate: str,
):
    time_span = areas["startTime"] + "~" + areas["endTime"]
    for area_name in area_names:
        item = areas["listAreaPrice"][area_name - 1]  
        if not item["use"] and item["price"] != -1:
            data = {
                "areaRecordList": [{
                    "areaId": item["areaId"],
                    "areaName": item["areaName"],
                    "bookingType": "null",
                    "bookingDate": bookdate,
                    "timeId": item["timeId"],
                    "time": time_span,
                    "userType": "1",
                    "price": item["price"],
                    "areaPriceId": item["areaPriceId"],
                }],
                "bookTimes": 1,
                "payAmount": item["price"],
                "payDuration": 0,
                "siteId": site_id,
            }
            r1 = requests.post(url=URL.submitAreaOrder, json=data)
            r2 = r1.json()
            if r1.status_code == 200 and r2["status"] == 0:
                log.info(f"Success! \ttime: {time_span} \tArea: {area_name} \tDate: {bookdate}")
                return True
            else:
                log.info(f"Oh, Failed! {r2['message']} \ttime: {time_span} \tArea: {area_name} \tDate: {bookdate}")
        else:
            log.info(f"Already in use! \ttime: {time_span} \tArea: {area_name} \tDate: {bookdate}")

    log.info(f"All Failed at {time_span}!\n\n")
    return False


def get_areas(bookdate, site_id, order_time, area_names):
    rprint("\nTime is up!\n")
    data = { "bookDate": bookdate, "siteId": site_id }
    for _ in range(20):
        time.sleep(0.2)
        r0 = requests.post(url=URL.listAreaPriceBySiteIdAndTime, json=data)
        r1 = r0.json()
        if r0.status_code == 200 and r1["status"] == 0:
            log.info(f"Get area price list: {r1['message']}")
            areas = r1["data"][order_time - 8]
            if order(areas, area_names, site_id, bookdate):
                break
        else:
            log.info(f"Request failed! {r1['message']}")

    confirm()


def confirm():
    """
    自动确认
    """
    data = {"orderStatus":"", "createMouth":"", "pager":{"pageNum":1,"pageSize":10}}
    orders = requests.post(url=URL.listMineAreaOrderAndStatus, json=data)
    order_list = orders.json()['data']
    for order in order_list:
        if order['orderStatusName'] == '未支付' and order['orderStatus'] == 2:
            order_id = order['id']
            data = {"id": order_id}
            order_info = requests.post(url=URL.getAreaOrderAndRecordByOrderId, json=data)
            order_info_data = order_info.json()['data']
            pay_type = requests.post(url=URL.getGymReservePayType, json=data)
            pay_type_data = pay_type.json()['data'][0]
            if pay_type_data['jump'] == 'freePayPlatform':
                data = {
                    "orderId": order_id,
                    "payTypeId": pay_type_data['payId'],
                    "payType": pay_type_data['payName'],
                    "gymId": order_info_data['gymId'],
                    "goodsId": order_info_data['goodsId'],
                    "goodsCode": order_info_data['goodsCode'],
                    "clientType":"WXQY",
                }
                res = requests.post(url=URL.freePayPlatform, json=data)
                log.info("Confirm: " + res.json()["message"])
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser("订票程序")
    parser.add_argument("-s", "--site", type=str, choices=[*site_ids.keys()], default='site')
    parser.add_argument("-u", "--user", type=str, choices=[*user_ids.keys()], default='someone')
    parser.add_argument("-t", "--time", type=int, help="order time", default=19)
    parser.add_argument("-d", "--date", type=str, default=None, help="订票日期, e.g. '2022-11-01'")
    parser.add_argument("-a", "--areas", type=int, default=None, nargs='+', help='list, 场地号')
    parser.add_argument("--start_time", type=str, default='12:00:00', help='开始订票的时间')
    parser.add_argument("-q", action='store_true', help='修仙模式')
    parser.add_argument("--now", action="store_true", help="立刻订票, for debug")
    args = parser.parse_args()

    # 默认在第二天订第三天的场，e.g. 8号运行本程序，9号订10号的场地
    if args.date is None:
        args.date = str(datetime.date.today() + datetime.timedelta(days=2 if not args.q else 1))

    # 如果场地为空，则随机打乱下列列表，按打乱后的顺序依次订票
    if args.areas is None:
        args.areas = [6, 5, 4, 3, 2, 9, 10, 11, 12, 13, 8]
        random.shuffle(args.areas)

    rprint(f"预订日期: {args.date} 时间: {args.time}:00 种类: {args.site}  用户名: {args.user}  场地：{args.areas}")

    requests.post = functools.partial(
        requests.post,
        headers=header(user_id=user_ids[args.user]),
    )
    requests.get = functools.partial(
        requests.get,
        headers=header(user_id=user_ids[args.user]),
    )

    run = functools.partial(
        get_areas,
        bookdate=args.date,
        site_id=site_ids[args.site],
        order_time=args.time,
        area_names=args.areas,
    )

    def print_time():
        print(f"\r{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", end="")

    if not args.now:
        rprint("正在等待订票")
        schedule.every().day.at(args.start_time).do(run)
        schedule.every().seconds.do(print_time)
        while True:
            schedule.run_pending()
            time.sleep(0.01)
    else:
        run()
