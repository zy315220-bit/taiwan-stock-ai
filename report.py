import re

from config import get_rating
from risk import risk_level


def print_report(
    stock,
    df,
    score,
    reasons,
    realtime=None
):

    if df is None or df.empty:
        raise ValueError("沒有可顯示的股票資料。")

    latest = df.iloc[-1]
    latest_date = df.index[-1]

    # ===== 取得歷史日線資料 =====
    historical_close = float(latest["Close"])

    ma5 = float(latest["MA5"])
    ma20 = float(latest["MA20"])
    ma60 = float(latest["MA60"])

    rsi = float(latest["RSI"])
    macd = float(latest["MACD"])
    signal = float(latest["Signal"])

    k = float(latest["K"])
    d = float(latest["D"])

    atr = float(latest["ATR"])
    volume = float(latest["Volume"])

    # ===== 決定分析使用價格 =====
    # 有最新成交價時，用最新成交價做即時判斷
    # 沒有即時資料時，退回使用最新日線收盤價
    if (
        realtime is not None
        and realtime.get("price") is not None
    ):
        analysis_price = float(realtime["price"])
        price_source = "最新成交價"
    else:
        analysis_price = historical_close
        price_source = "最新日線收盤價"

    if analysis_price <= 0:
        raise ValueError("分析價格必須大於 0。")

    # ===== 評分等級 =====
    grade, star, advice = get_rating(score)

    # ===== 風險 =====
    risk = risk_level(
        atr,
        analysis_price
    )

    # ===== 趨勢判斷 =====
    if analysis_price > ma5 > ma20 > ma60:
        trend = "Strong Bullish"

    elif ma5 > ma20 > ma60:
        trend = "Bullish"

    elif analysis_price < ma5 < ma20 < ma60:
        trend = "Strong Bearish"

    elif ma5 < ma20 < ma60:
        trend = "Bearish"

    elif ma20 > ma60:
        trend = "Sideways Bullish"

    elif ma20 < ma60:
        trend = "Sideways Bearish"

    else:
        trend = "Sideways"

    # ===== 訊號強度 =====
    # 不是勝率，只代表分數離中性 50 分的距離
    signal_strength = min(
        95,
        round(50 + abs(score - 50))
    )

    # ===== 標題 =====
    print("\n" + "=" * 60)
    print(f"              AI 股票分析報告 - {stock}")
    print("=" * 60)

    # ===== 最新行情 =====
    print("\n最新行情")
    print("-" * 60)

    print(
        f"歷史資料日期    : "
        f"{latest_date.strftime('%Y-%m-%d')}"
    )

    print(
        f"最新日線收盤價  : "
        f"{historical_close:.2f}"
    )

    if realtime is not None:

        realtime_price = realtime.get("price")

        if realtime_price is not None:
            print(
                f"最新成交價      : "
                f"{float(realtime_price):.2f}"
            )

        print(
            f"行情市場        : "
            f"{realtime.get('market', 'Unknown')}"
        )

        realtime_date = realtime.get("date", "")
        realtime_time = realtime.get("time", "")

        print(
            f"行情時間        : "
            f"{realtime_date} {realtime_time}"
        )

        change = realtime.get("change")
        change_percent = realtime.get("change_percent")

        if (
            change is not None
            and change_percent is not None
        ):
            print(
                f"漲跌            : "
                f"{float(change):+.2f} "
                f"({float(change_percent):+.2f}%)"
            )

        open_price = realtime.get("open")
        high_price = realtime.get("high")
        low_price = realtime.get("low")

        if open_price is not None:
            print(
                f"今日開盤        : "
                f"{float(open_price):.2f}"
            )

        if high_price is not None:
            print(
                f"今日最高        : "
                f"{float(high_price):.2f}"
            )

        if low_price is not None:
            print(
                f"今日最低        : "
                f"{float(low_price):.2f}"
            )

    else:
        print("最新成交價      : 無法取得")
        print("行情來源        : 僅使用歷史日線資料")

    # ===== 技術指標 =====
    print("\n技術指標")
    print("-" * 60)

    print(
        f"評分使用價格    : "
        f"{analysis_price:.2f}"
    )

    print(
        f"價格來源        : "
        f"{price_source}"
    )

    print(f"MA5             : {ma5:.2f}")
    print(f"MA20            : {ma20:.2f}")
    print(f"MA60            : {ma60:.2f}")
    print(f"RSI             : {rsi:.2f}")
    print(f"MACD            : {macd:.4f}")
    print(f"Signal          : {signal:.4f}")
    print(f"MACD Histogram  : {macd - signal:.4f}")
    print(f"K               : {k:.2f}")
    print(f"D               : {d:.2f}")
    print(f"ATR             : {atr:.2f}")

    print(
        f"ATR Percent     : "
        f"{atr / analysis_price * 100:.2f}%"
    )

    print(f"成交量          : {int(volume):,}")

    # ===== 綜合評分 =====
    print("\n" + "-" * 60)
    print("AI 綜合評分")
    print("-" * 60)

    print(f"AI Score        : {score}/100")
    print(f"Grade           : {grade}")
    print(f"Rating          : {star}")
    print(f"Recommendation  : {advice}")
    print(f"Signal Strength : {signal_strength}%")
    print(f"Risk            : {risk}")
    print(f"Trend           : {trend}")

    # ===== 分析原因 =====
    print("\n" + "-" * 60)
    print("分析原因")
    print("-" * 60)

    for reason in reasons:

        match = re.search(
            r"\(\+(-?\d+(?:\.\d+)?)\)",
            reason
        )

        if match:
            point = float(match.group(1))

            if point <= 0:
                icon = "🔴"

            elif point < 7:
                icon = "🟡"

            else:
                icon = "🟢"

        elif "(-" in reason:
            icon = "🔴"

        else:
            icon = "⚪"

        print(f"{icon} {reason}")

    print("\n" + "-" * 60)
    print(f"共分析 {len(reasons)} 項評分條件")

    # ===== AI 結論 =====
    print("\n" + "=" * 60)
    print("AI 結論")
    print("=" * 60)

    if score >= 85:
        print("目前技術面強勢，多項指標同步偏多。")
        print("可考慮等待拉回後分批布局，但應避免追高。")

    elif score >= 70:
        print("整體技術面偏多，但部分指標仍存在短線壓力。")
        print("可等待接近支撐、MA5 或 MA20 時再分批觀察。")

    elif score >= 55:
        print("多空訊號混合，目前尚未形成明確趨勢。")
        print("建議觀望，等待放量突破壓力或跌破支撐。")

    elif score >= 40:
        print("目前技術面偏弱，空方訊號略占優勢。")
        print("持股者可控制部位，並留意重要均線與支撐。")

    else:
        print("目前空方訊號較多，整體技術面明顯偏弱。")
        print("不建議只因超賣就搶反彈，應等待趨勢改善。")

    print(
        "\n注意：本報告為規則型技術分析，"
        "不代表未來報酬保證。"
    )

    print("=" * 60)