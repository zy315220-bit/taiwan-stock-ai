import math


# ==================================================
# 共用工具
# ==================================================

def clamp(value, minimum, maximum):
    """
    將 value 限制在 minimum 到 maximum 之間。
    """
    return max(minimum, min(value, maximum))


def add_result(total_score, all_reasons, result):
    """
    將各個評分函式回傳的分數與原因加入總結果。
    """
    part_score, part_reasons = result

    total_score += part_score
    all_reasons.extend(part_reasons)

    return total_score, all_reasons


# ==================================================
# 1. 均線趨勢評分：30 分
# ==================================================

def score_trend(close, ma5, ma20, ma60):

    score = 0.0
    reasons = []

    close_ma5_pct = (close - ma5) / ma5 * 100
    ma5_ma20_pct = (ma5 - ma20) / ma20 * 100
    ma20_ma60_pct = (ma20 - ma60) / ma60 * 100

    close_ma5_score = clamp(
        (close_ma5_pct + 2) / 4 * 10,
        0,
        10
    )

    ma5_ma20_score = clamp(
        (ma5_ma20_pct + 2) / 4 * 10,
        0,
        10
    )

    ma20_ma60_score = clamp(
        (ma20_ma60_pct + 3) / 6 * 10,
        0,
        10
    )

    score += close_ma5_score
    score += ma5_ma20_score
    score += ma20_ma60_score

    if close_ma5_pct >= 0:
        reasons.append(
            f"股價高於 MA5 {close_ma5_pct:.2f}% "
            f"(+{close_ma5_score:.1f})"
        )
    else:
        reasons.append(
            f"股價低於 MA5 {abs(close_ma5_pct):.2f}% "
            f"(+{close_ma5_score:.1f})"
        )

    if ma5_ma20_pct >= 0:
        reasons.append(
            f"MA5 高於 MA20 {ma5_ma20_pct:.2f}% "
            f"(+{ma5_ma20_score:.1f})"
        )
    else:
        reasons.append(
            f"MA5 低於 MA20 {abs(ma5_ma20_pct):.2f}% "
            f"(+{ma5_ma20_score:.1f})"
        )

    if ma20_ma60_pct >= 0:
        reasons.append(
            f"MA20 高於 MA60 {ma20_ma60_pct:.2f}% "
            f"(+{ma20_ma60_score:.1f})"
        )
    else:
        reasons.append(
            f"MA20 低於 MA60 {abs(ma20_ma60_pct):.2f}% "
            f"(+{ma20_ma60_score:.1f})"
        )

    return score, reasons


# ==================================================
# 2. RSI 評分：10 分
# ==================================================

def score_rsi(rsi):

    reasons = []

    if 45 <= rsi <= 60:
        score = 10
        text = "RSI 位於健康區間"

    elif 40 <= rsi < 45:
        score = 8
        text = "RSI 動能略弱"

    elif 30 <= rsi < 40:
        score = 6
        text = "RSI 動能偏弱"

    elif 60 < rsi <= 65:
        score = 8
        text = "RSI 動能偏強"

    elif 65 < rsi <= 70:
        score = 6
        text = "RSI 接近過熱區"

    elif 25 <= rsi < 30:
        score = 4
        text = "RSI 位於超賣區附近"

    elif 70 < rsi <= 80:
        score = 3
        text = "RSI 位於過熱區"

    elif rsi < 25:
        score = 1
        text = "RSI 嚴重超賣"

    else:
        score = 1
        text = "RSI 嚴重過熱"

    reasons.append(
        f"{text}，數值 {rsi:.1f} (+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 3. MACD 評分：15 分
# ==================================================

def score_macd(close, macd, signal):

    reasons = []

    histogram = macd - signal

    histogram_pct = histogram / close * 100
    zero_pct = macd / close * 100

    histogram_score = clamp(
        (histogram_pct + 0.8) / 1.6 * 10,
        0,
        10
    )

    zero_score = clamp(
        (zero_pct + 0.8) / 1.6 * 5,
        0,
        5
    )

    score = histogram_score + zero_score

    if macd > signal and macd > 0:
        text = "MACD 位於訊號線及零軸上方"

    elif macd > signal:
        text = "MACD 高於訊號線，但仍在零軸下方"

    elif macd > 0:
        text = "MACD 低於訊號線，但仍在零軸上方"

    else:
        text = "MACD 低於訊號線且位於零軸下方"

    reasons.append(
        f"{text}，柱狀體 {histogram:.4f} "
        f"(+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 4. KD 評分：10 分
# ==================================================

def score_kd(k, d):

    reasons = []

    difference = k - d

    cross_score = clamp(
        (difference + 10) / 20 * 7,
        0,
        7
    )

    if 20 <= k <= 70:
        position_score = 3

    elif 10 <= k < 20 or 70 < k <= 80:
        position_score = 2

    else:
        position_score = 1

    score = clamp(
        cross_score + position_score,
        0,
        10
    )

    if k > d:
        text = "KD 動能偏多"

    elif abs(k - d) <= 3:
        text = "K 與 D 接近，動能接近中性"

    elif k < 20 and d < 20:
        text = "KD 位於低檔區"

    else:
        text = "KD 動能偏弱"

    reasons.append(
        f"{text}，K={k:.1f}、D={d:.1f} "
        f"(+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 5. 布林通道評分：10 分
# ==================================================

def score_bollinger(close, ma20, upper, lower):

    reasons = []

    band_width_price = upper - lower

    if band_width_price <= 0:
        position = 0.5
        score = 5

    else:
        position = (
            (close - lower)
            / band_width_price
        )

        if 0.50 <= position <= 0.80:
            score = 10

        elif 0.35 <= position < 0.50:
            score = 8

        elif 0.80 < position <= 1.00:
            score = 7

        elif 0.15 <= position < 0.35:
            score = 5

        elif position < 0:
            score = 3

        else:
            score = 4

    if close > upper:
        text = "股價突破布林上軌，短線可能過熱"

    elif close >= ma20:
        text = "股價位於布林中軌上方"

    elif close >= lower:
        text = "股價位於布林中軌下方"

    else:
        text = "股價跌破布林下軌，可能超賣"

    reasons.append(
        f"{text}，帶內位置 "
        f"{position * 100:.1f}% "
        f"(+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 6. 成交量評分：10 分
# ==================================================

def score_volume(close, ma5, today_volume, vma20):

    reasons = []

    if vma20 > 0:
        volume_ratio = today_volume / vma20
    else:
        volume_ratio = 1.0

    if close >= ma5:

        if volume_ratio >= 1.5:
            score = 10

        elif volume_ratio >= 1.2:
            score = 9

        elif volume_ratio >= 0.8:
            score = 7

        elif volume_ratio >= 0.5:
            score = 5

        else:
            score = 3

    else:

        if volume_ratio >= 1.5:
            score = 2

        elif volume_ratio >= 1.2:
            score = 3

        elif volume_ratio >= 0.8:
            score = 5

        elif volume_ratio >= 0.5:
            score = 4

        else:
            score = 3

    if close >= ma5 and volume_ratio >= 1.2:
        text = "股價偏強且成交量放大"

    elif close < ma5 and volume_ratio >= 1.2:
        text = "股價偏弱且成交量放大"

    elif volume_ratio < 0.8:
        text = "成交量偏低"

    else:
        text = "成交量正常"

    reasons.append(
        f"{text}，為20日均量的 "
        f"{volume_ratio:.2f} 倍 (+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 7. ATR 評分：10 分
# ==================================================

def score_atr(close, atr):

    reasons = []

    atr_percent = atr / close * 100

    if atr_percent <= 1.5:
        score = 10
        text = "ATR 波動率低"

    elif atr_percent <= 2.0:
        score = 9
        text = "ATR 波動率偏低"

    elif atr_percent <= 3.0:
        score = 7
        text = "ATR 波動率正常"

    elif atr_percent <= 4.0:
        score = 4
        text = "ATR 波動率偏高"

    elif atr_percent <= 5.0:
        score = 2
        text = "ATR 波動率很高"

    else:
        score = 1
        text = "ATR 波動率過高"

    reasons.append(
        f"{text}，約為 {atr_percent:.2f}% "
        f"(+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 8. 布林帶寬評分：5 分
# ==================================================

def score_bbwidth(bbwidth):

    reasons = []

    if 5 <= bbwidth <= 15:
        score = 5
        text = "布林帶寬正常"

    elif 3 <= bbwidth < 5:
        score = 4
        text = "布林通道略為收斂"

    elif bbwidth < 3:
        score = 3
        text = "布林通道明顯收斂"

    elif 15 < bbwidth <= 20:
        score = 3
        text = "布林通道開始擴張"

    else:
        score = 2
        text = "布林通道明顯擴張"

    reasons.append(
        f"{text}，數值 {bbwidth:.2f}% "
        f"(+{score:.1f})"
    )

    return score, reasons


# ==================================================
# 主評分函式
# ==================================================

def calculate_score(df, current_price=None):

    if df is None or df.empty:
        raise ValueError("沒有可供評分的股票資料。")

    latest = df.iloc[-1]

    required_columns = [
        "Close",
        "MA5",
        "MA20",
        "MA60",
        "RSI",
        "MACD",
        "Signal",
        "K",
        "D",
        "Upper",
        "Lower",
        "ATR",
        "BBWidth",
        "Volume",
        "VMA20"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "缺少評分欄位："
            + ", ".join(missing_columns)
        )

    values = {
        column: float(latest[column])
        for column in required_columns
    }

    invalid_columns = [
        column
        for column, value in values.items()
        if not math.isfinite(value)
    ]

    if invalid_columns:
        raise ValueError(
            "最新資料的指標尚未計算完成："
            + ", ".join(invalid_columns)
        )

    historical_close = values["Close"]

    if current_price is not None:
        close = float(current_price)
    else:
        close = historical_close

    if not math.isfinite(close) or close <= 0:
        raise ValueError("分析價格必須是大於 0 的有效數字。")

    ma5 = values["MA5"]
    ma20 = values["MA20"]
    ma60 = values["MA60"]

    rsi = values["RSI"]
    macd = values["MACD"]
    signal = values["Signal"]

    k = values["K"]
    d = values["D"]

    upper = values["Upper"]
    lower = values["Lower"]

    atr = values["ATR"]
    bbwidth = values["BBWidth"]

    today_volume = values["Volume"]
    vma20 = values["VMA20"]

    total_score = 0.0
    reasons = []

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_trend(
            close,
            ma5,
            ma20,
            ma60
        )
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_rsi(rsi)
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_macd(
            close,
            macd,
            signal
        )
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_kd(k, d)
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_bollinger(
            close,
            ma20,
            upper,
            lower
        )
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_volume(
            close,
            ma5,
            today_volume,
            vma20
        )
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_atr(
            close,
            atr
        )
    )

    total_score, reasons = add_result(
        total_score,
        reasons,
        score_bbwidth(bbwidth)
    )

    total_score = round(
        clamp(total_score, 0, 100)
    )

    return total_score, reasons