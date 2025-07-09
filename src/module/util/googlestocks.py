import datetime
import json
import random
import re

import pandas as pd
import requests

__base_path = "https://www.google.com/finance/_/GoogleFinanceUi/data/batchexecute?"
__session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko)",
}
timeout = 10.0


dump_json = lambda o: json.dumps(o, separators=(",", ":"))
rand_num_str = lambda l: str(int(random.random() * (10**l)))
out_array = lambda a: a if len(a) > 1 else out_array(a[0])


def __batch_exec(envelopes):
    envs = envelopes if isinstance(envelopes, list) else [envelopes]
    rpcids = "%2C".join(list(dict.fromkeys([e["id"] for e in envs])))
    if len(envs) == 0:
        return
    elif len(envs) == 1:
        payload = dump_json(
            [[[envs[0]["id"], dump_json(envs[0]["data"]), None, "generic"]]]
        )
    else:
        payload = dump_json(
            [
                [
                    [e["id"], dump_json(e["data"]), None, str(i + 1)]
                    for i, e in enumerate(envs)
                ]
            ]
        )
    path = f"rpcids={rpcids}&f.sid=-{rand_num_str(19)}&bl=boq_finance-ui_20211101.11_p0&hl=en&_reqid={rand_num_str(8)}"
    rsp = __session.post(
        __base_path + path,
        params={"f.req": payload},
        headers=headers,
        timeout=timeout,
    )
    if rsp.status_code != 200:
        raise Exception("网络错误: {}".format(rsp.status_code))
    rsps = json.loads(rsp.text.split("\n")[2])
    datas = []
    for r in rsps:
        if r[0] == "er":
            raise Exception("请求错误: {}".format(r[5]))
        elif r[0] == "wrb.fr":
            cur = json.loads(r[2])
            datas.insert(
                int(r[6] if r[6] != "generic" else 1) - 1, cur if len(cur) > 0 else []
            )
    return datas if len(datas) > 1 else datas[0]


def parse_trading(i):
    if i is None:
        return None
    return {
        "last": i[0],
        "change": i[1],
        "change_percent": i[2],
    }


def parse_datetime(i):
    arr = []
    for item in i:
        if isinstance(item, int):
            arr.append(item)
        elif item is None:
            arr.append(0)
        elif isinstance(item, list):
            arr.append(
                datetime.timezone(
                    datetime.timedelta(seconds=0 if len(item) == 0 else item[0])
                )
            )
    return datetime.datetime(*arr)


def parse_detail(i):
    if i is None or len(i) < 5 or i[4] is None:
        return None
    return {
        "inner_id": i[0],
        "code": i[1][0],
        "market": i[1][1] if len(i[1]) > 1 else None,
        "name": i[2],
        "currency": i[4],
        "trading": parse_trading(i[5]),
        "last_close": i[7],
        "region": i[9],
        # 10?
        "update_timestamp": i[11][0],
        "timezone": i[12],
        "timezone_offset": i[13],
        "extended_trading": parse_trading(i[16]),
        "last_timestamp": i[17][0],
        "extended_timestamp": None if i[18] is None else i[18][0],
        "start_trading_dt": None if i[19] is None else parse_datetime(i[19][0][1]),
        "end_trading_dt": None if i[19] is None else parse_datetime(i[19][0][2]),
        "full_ticker": i[21],
    }


def search(kw):
    rsp = __batch_exec({"id": "mKsvE", "data": [kw, [], True, True]})
    list = [parse_detail(e[3]) for e in rsp[0]] if len(rsp) > 0 else []
    return filter(lambda i: i is not None, list)


def is_probably_stock(code, market):
    if market.upper() not in {"NASDAQ", "NYSE", "AMEX"}:
        return False
    if re.search(r"\d$", code) or "W00" in code:
        return False
    return True


def search_list(kw):
    rsp = __batch_exec({"id": "mKsvE", "data": [kw, [], True, True]})
    seen = set()
    results = []

    for group in rsp:
        if not group or not isinstance(group, list):
            continue
        for item in group:
            if len(item) > 3:
                parsed = parse_detail(item[3])
                if parsed:
                    code = parsed.get("code", "")
                    market = parsed.get("market", "")
                    key = f"{code}:{market}"
                    if key in seen:
                        continue
                    if is_probably_stock(code, market):
                        seen.add(key)
                        results.append(parsed)

    return results


# range: 1: 1d(/min), 2: 5d(/30min), 3: 1m(/day), 4: 6m(/day), 5: ytd(/day), 6: 1y(/day), 7: 5y(/week), 8:max
def history(_id, _range):
    rsp = __batch_exec({"id": "AiCwsd", "data": [[[None, _id.split(":")]], _range]})
    return [
        {
            "datetime": parse_datetime(i[0]),
            "trading": parse_trading(i[1]),
            "volume": i[2],
        }
        for i in out_array(rsp)[3][0][1]
    ]


def history_df(_id, _range):
    data = history(_id, _range)
    df = pd.DataFrame(data)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["last"] = df["trading"].apply(lambda t: t["last"] if t else None)
    df["change"] = df["trading"].apply(lambda t: t["change"] if t else None)
    df["change_percent"] = df["trading"].apply(
        lambda t: t["change_percent"] if t else None
    )
    return df.drop(columns=["trading"])
