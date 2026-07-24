import numpy as np
import pandas as pd


def add_indicators(df):

    # 建立副本，避免修改原始資料
    df = df.copy()

    # ===== 處理新版 yfinance 雙層欄位 =====
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 去除可能重複的欄位
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # 檢查必要欄位
    required_columns = ["Close", "High", "Low", "Volume"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"缺少必要欄位：{', '.join(missing_columns)}"
        )

    # 強制轉成數字，無法轉換的內容改為 NaN
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # ===== 均線 =====
    df["MA5"] = close.rolling(
        window=5,
        min_periods=5
    ).mean()

    df["MA20"] = close.rolling(
        window=20,
        min_periods=20
    ).mean()

    df["MA60"] = close.rolling(
        window=60,
        min_periods=60
    ).mean()

    # ===== RSI 14 =====
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # 使用 Wilder RSI，較接近一般看盤軟體
    avg_gain = gain.ewm(
        alpha=1 / 14,
        adjust=False,
        min_periods=14
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14,
        adjust=False,
        min_periods=14
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["RSI"] = 100 - (100 / (1 + rs))

    # 完全沒有下跌時，RSI 設為 100
    df.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI"
    ] = 100

    # 完全沒有漲跌時，RSI 設為 50
    df.loc[
        (avg_loss == 0) & (avg_gain == 0),
        "RSI"
    ] = 50

    # ===== MACD =====
    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = ema12 - ema26

    df["Signal"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["MACD_Hist"] = (
        df["MACD"] - df["Signal"]
    )

    # ===== KD 隨機指標 =====
    low14 = low.rolling(
        window=14,
        min_periods=14
    ).min()

    high14 = high.rolling(
        window=14,
        min_periods=14
    ).max()

    price_range = high14 - low14
    price_range = price_range.replace(0, np.nan)

    rsv = (
        (close - low14)
        / price_range
        * 100
    )

    df["K"] = rsv.ewm(
        alpha=1 / 3,
        adjust=False
    ).mean()

    df["D"] = df["K"].ewm(
        alpha=1 / 3,
        adjust=False
    ).mean()

    # 限制 KD 在 0～100
    df["K"] = df["K"].clip(0, 100)
    df["D"] = df["D"].clip(0, 100)

    # ===== 布林通道 =====
    std20 = close.rolling(
        window=20,
        min_periods=20
    ).std()

    df["Upper"] = df["MA20"] + 2 * std20
    df["Lower"] = df["MA20"] - 2 * std20

    # ===== 布林帶寬，單位為百分比 =====
    safe_ma20 = df["MA20"].replace(0, np.nan)

    df["BBWidth"] = (
        (df["Upper"] - df["Lower"])
        / safe_ma20
        * 100
    )

    # ===== ATR 14 =====
    previous_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - previous_close).abs()
    tr3 = (low - previous_close).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    # 使用 Wilder ATR
    df["ATR"] = true_range.ewm(
        alpha=1 / 14,
        adjust=False,
        min_periods=14
    ).mean()

    # ATR 相對於股價的百分比
    df["ATRPercent"] = (
        df["ATR"]
        / close.replace(0, np.nan)
        * 100
    )

    # ===== 20 日平均成交量 =====
    df["VMA20"] = volume.rolling(
        window=20,
        min_periods=20
    ).mean()

    # 今日成交量相對於 20 日平均量
    df["VolumeRatio"] = (
        volume
        / df["VMA20"].replace(0, np.nan)
    )

    # 將正負無限大轉成空值
    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return df