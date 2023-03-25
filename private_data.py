from dataclasses import dataclass

site_ids = {
    "a": "b",
}

user_ids = {
    "user_name": "user_id",
}


@dataclass(frozen=True)
class URL:
    listAreas = ""
    submitOrder = ""
    getUserInfo = ""
    # other urls...


def header(user_id):
    return {
        "Host": "",
        "Connection": "keep-alive",
        # "Content-Length": TODO,
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6309020f) XWEB/6500",
        "Content-Type": "application/json",
        "Origin": "",
        "Referer": "",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh",
        "Cookie": f"lxwxuserid={user_id}",
    }
