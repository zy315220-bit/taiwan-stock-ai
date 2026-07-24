import requests


def _to_float(value):
    if value is None:
        return None

    value = str(value).strip().replace(",", "")

    if value in ["", "-", "--"]:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def get_realtime_price(stock_code):

    stock_code = stock_code.strip().upper()

    stock_code = (
        stock_code
        .replace(".TW", "")
        .replace(".TWO", "")
    )

    if not stock_code:
        raise ValueError("股票代號不能空白。")

    # tse：上市
    # otc：上櫃
    channels = [
        f"tse_{stock_code}.tw",
        f"otc_{stock_code}.tw"
    ]

    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120 Safari/537.36"
        ),
        "Referer": "https://mis.twse.com.tw/"
    }

    for channel in channels:

        params = {
            "ex_ch": channel,
            "json": "1",
            "delay": "0"
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

        except Exception:
            continue

        messages = data.get("msgArray", [])

        if not messages:
            continue

        quote = messages[0]

        name = quote.get("n", "")
        code = quote.get("c", stock_code)

        current_price = _to_float(quote.get("z"))
        previous_close = _to_float(quote.get("y"))
        open_price = _to_float(quote.get("o"))
        high_price = _to_float(quote.get("h"))
        low_price = _to_float(quote.get("l"))

        # 無成交時 z 可能是 "-"
        # 這時退回使用昨收價
        if current_price is None:
            current_price = previous_close

        if current_price is None:
            continue

        market = "上市" if channel.startswith("tse_") else "上櫃"

        change = None
        change_percent = None

        if previous_close and previous_close > 0:
            change = current_price - previous_close
            change_percent = change / previous_close * 100

        return {
            "code": code,
            "name": name,
            "market": market,
            "price": current_price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "date": quote.get("d", ""),
            "time": quote.get("t", ""),
            "source": "TWSE MIS"
        }

    raise ValueError(
        f"無法取得 {stock_code} 的最新行情，"
        "請確認代號或稍後再試。"
    )