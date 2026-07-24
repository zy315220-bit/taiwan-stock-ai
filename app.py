import re

import pandas as pd
import streamlit as st

from stock import download_stock
from realtime import get_realtime_price
from indicators import add_indicators
from score import calculate_score
from config import get_rating
from risk import risk_level


# ==================================================
# 網頁基本設定
# ==================================================

st.set_page_config(
    page_title="AI 台股分析系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==================================================
# 共用函式
# ==================================================

@st.cache_data(ttl=300)
def load_history(stock_code):
    """
    下載並處理歷史股票資料。
    快取 300 秒，避免重複下載。
    """

    df = download_stock(stock_code)

    if df is None or df.empty:
        raise ValueError("找不到股票歷史資料。")

    if len(df) < 60:
        raise ValueError(
            f"資料只有 {len(df)} 個交易日，"
            "至少需要 60 個交易日。"
        )

    df = add_indicators(df)
    df = df.dropna().copy()

    if df.empty:
        raise ValueError(
            "技術指標計算後沒有可用資料。"
        )

    return df


def load_realtime(stock_code):
    """
    取得最新成交行情。
    失敗時回傳 None。
    """

    try:
        return get_realtime_price(stock_code)

    except Exception:
        return None


def determine_trend(
    current_price,
    ma5,
    ma20,
    ma60
):
    """
    判斷均線趨勢。
    """

    if current_price > ma5 > ma20 > ma60:
        return "Strong Bullish"

    if ma5 > ma20 > ma60:
        return "Bullish"

    if current_price < ma5 < ma20 < ma60:
        return "Strong Bearish"

    if ma5 < ma20 < ma60:
        return "Bearish"

    if ma20 > ma60:
        return "Sideways Bullish"

    if ma20 < ma60:
        return "Sideways Bearish"

    return "Sideways"


def parse_reason_score(reason):
    """
    從文字中取得 (+9.2)、(+0.0) 等分數。
    """

    match = re.search(
        r"\(\+(-?\d+(?:\.\d+)?)\)",
        reason
    )

    if match:
        return float(match.group(1))

    return None


def display_reason(reason):
    """
    依照原因得分顯示不同顏色。
    """

    reason_score = parse_reason_score(reason)

    if reason_score is None:
        st.info(reason)

    elif reason_score <= 0:
        st.error(f"🔴 {reason}")

    elif reason_score < 7:
        st.warning(f"🟡 {reason}")

    else:
        st.success(f"🟢 {reason}")


def display_conclusion(score):
    """
    顯示綜合結論。
    """

    if score >= 85:
        st.success(
            "目前技術面強勢，多項指標同步偏多。"
            "可等待價格拉回重要均線或支撐後分批觀察，"
            "但不宜在短線急漲後追高。"
        )

    elif score >= 70:
        st.success(
            "整體技術面偏多，但部分指標仍可能存在短線壓力。"
            "可持續觀察成交量是否配合，以及價格是否守住重要均線。"
        )

    elif score >= 55:
        st.info(
            "多空訊號混合，目前尚未形成明確趨勢。"
            "建議等待價格放量突破壓力，或跌破支撐後再重新判斷。"
        )

    elif score >= 40:
        st.warning(
            "目前技術面偏弱，空方訊號略占優勢。"
            "持股者可控制部位，並留意重要均線與近期支撐。"
        )

    else:
        st.error(
            "目前空方訊號較多，整體技術面明顯偏弱。"
            "不建議只因指標進入超賣區就搶反彈，"
            "應等待趨勢與成交量出現改善。"
        )


# ==================================================
# 側邊欄
# ==================================================

with st.sidebar:

    st.header("📊 系統資訊")

    st.write("**AI 台股分析系統**")
    st.caption("Version 1.0.0")

    st.divider()

    st.write("**開發者**")
    st.write("子珺 袁")

    st.write("**學校與科系**")
    st.write("淡江大學航空太空工程")

    st.divider()

    st.caption(
        "本系統使用歷史日線技術指標，"
        "並結合最新成交價進行即時位置判斷。"
    )

    if st.button(
        "清除歷史資料快取",
        use_container_width=True
    ):
        st.cache_data.clear()
        st.success("快取已清除。")


# ==================================================
# 首頁封面
# ==================================================

title_col, version_col = st.columns(
    [5, 1],
    vertical_alignment="center"
)

with title_col:
    st.title("📈 AI 台股分析系統")

with version_col:
    st.caption("Version 1.0.0")

st.subheader("台灣智慧股票分析器")

st.caption(
    "開發者：子珺 袁｜"
    "淡江大學航空太空工程"
)

st.info(
    "結合歷史日線技術指標與最新成交價，"
    "提供台股趨勢、動能、風險與綜合評分。"
)

st.divider()


# ==================================================
# 股票輸入區
# ==================================================

st.subheader("股票分析")

input_col, button_col = st.columns(
    [4, 1],
    vertical_alignment="bottom"
)

with input_col:
    stock = st.text_input(
        "請輸入台股代號",
        value="0056",
        placeholder="例如：2330、0050、0056",
        help=(
            "輸入台灣上市或上櫃股票代號。"
            "例如台積電輸入 2330。"
        )
    ).strip().upper()

with button_col:
    analyze_button = st.button(
        "開始分析",
        type="primary",
        use_container_width=True
    )


# ==================================================
# 尚未開始分析時顯示說明
# ==================================================

if not analyze_button:

    st.caption(
        "輸入股票代號後按下「開始分析」，"
        "系統將下載歷史資料並取得最新行情。"
    )

    feature_col1, feature_col2, feature_col3 = st.columns(3)

    with feature_col1:
        st.info(
            "📈 **趨勢分析**\n\n"
            "MA5、MA20、MA60 與目前價格位置。"
        )

    with feature_col2:
        st.info(
            "📊 **動能分析**\n\n"
            "RSI、MACD、KD 與布林通道。"
        )

    with feature_col3:
        st.info(
            "⚠️ **風險分析**\n\n"
            "ATR、成交量與綜合技術評分。"
        )


# ==================================================
# 執行分析
# ==================================================

if analyze_button:

    if not stock:
        st.error("股票代號不能空白。")
        st.stop()

    try:
        with st.spinner(
            f"正在分析 {stock}，"
            "請稍候..."
        ):

            # ===== 歷史資料 =====
            df = load_history(stock)

            latest = df.iloc[-1]
            latest_date = df.index[-1]

            historical_close = float(
                latest["Close"]
            )

            # ===== 最新行情 =====
            realtime = load_realtime(stock)

            if (
                realtime is not None
                and realtime.get("price") is not None
            ):
                current_price = float(
                    realtime["price"]
                )

                price_source = "最新成交價"

            else:
                current_price = historical_close
                price_source = "最新日線收盤價"

            if current_price <= 0:
                raise ValueError(
                    "目前取得的價格無效。"
                )

            # ===== 評分 =====
            score, reasons = calculate_score(
                df,
                current_price=current_price
            )

            grade, stars, advice = get_rating(
                score
            )

            # ===== 指標 =====
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

            atr_percent = (
                atr / current_price * 100
            )

            risk = risk_level(
                atr,
                current_price
            )

            trend = determine_trend(
                current_price,
                ma5,
                ma20,
                ma60
            )

    except Exception as error:
        st.error(f"分析失敗：{error}")
        st.stop()


    # ==================================================
    # 股票標題
    # ==================================================

    st.divider()

    st.header(f"📌 {stock} 分析結果")

    st.caption(
        f"歷史資料日期："
        f"{latest_date.strftime('%Y-%m-%d')}"
    )


    # ==================================================
    # 最新行情
    # ==================================================

    st.subheader("最新行情")

    price_col, change_col, time_col, market_col = st.columns(4)

    price_col.metric(
        "最新成交價",
        f"{current_price:,.2f}"
    )

    if realtime is not None:

        change = realtime.get("change")
        change_percent = realtime.get(
            "change_percent"
        )

        if (
            change is not None
            and change_percent is not None
        ):
            change_col.metric(
                "今日漲跌",
                f"{float(change):+.2f}",
                f"{float(change_percent):+.2f}%"
            )

        else:
            change_col.metric(
                "今日漲跌",
                "無資料"
            )

        realtime_date = realtime.get(
            "date",
            ""
        )

        realtime_time = realtime.get(
            "time",
            ""
        )

        time_col.metric(
            "行情時間",
            f"{realtime_date} {realtime_time}"
        )

        market_col.metric(
            "市場",
            realtime.get(
                "market",
                "未知"
            )
        )

    else:
        change_col.metric(
            "今日漲跌",
            "無即時資料"
        )

        time_col.metric(
            "歷史資料日期",
            latest_date.strftime("%Y-%m-%d")
        )

        market_col.metric(
            "價格來源",
            price_source
        )

        st.warning(
            "目前無法取得即時行情，"
            "本次評分改用最新完整日線收盤價。"
        )

    st.caption(
        f"最新日線收盤價：{historical_close:.2f}｜"
        f"評分使用價格：{current_price:.2f}｜"
        f"價格來源：{price_source}"
    )


    # ==================================================
    # 今日價格
    # ==================================================

    if realtime is not None:

        open_price = realtime.get("open")
        high_price = realtime.get("high")
        low_price = realtime.get("low")

        if any(
            value is not None
            for value in [
                open_price,
                high_price,
                low_price
            ]
        ):
            st.subheader("今日價格區間")

            open_col, high_col, low_col = st.columns(3)

            open_col.metric(
                "今日開盤",
                (
                    f"{float(open_price):.2f}"
                    if open_price is not None
                    else "無資料"
                )
            )

            high_col.metric(
                "今日最高",
                (
                    f"{float(high_price):.2f}"
                    if high_price is not None
                    else "無資料"
                )
            )

            low_col.metric(
                "今日最低",
                (
                    f"{float(low_price):.2f}"
                    if low_price is not None
                    else "無資料"
                )
            )


    # ==================================================
    # AI 綜合評分
    # ==================================================

    st.divider()
    st.subheader("AI 綜合評分")

    score_col, grade_col, advice_col, risk_col = st.columns(4)

    score_col.metric(
        "AI Score",
        f"{score}/100"
    )

    grade_col.metric(
        "Grade",
        grade
    )

    advice_col.metric(
        "Recommendation",
        advice
    )

    risk_col.metric(
        "Risk",
        risk
    )

    rating_col, trend_col = st.columns(2)

    rating_col.metric(
        "Rating",
        stars
    )

    trend_col.metric(
        "Trend",
        trend
    )

    st.progress(
        min(
            max(float(score), 0),
            100
        ) / 100
    )


    # ==================================================
    # 價格與均線圖
    # ==================================================

    st.divider()
    st.subheader("價格與均線")

    chart_df = df[
        [
            "Close",
            "MA5",
            "MA20",
            "MA60"
        ]
    ].tail(120).copy()

    chart_df = chart_df.rename(
        columns={
            "Close": "收盤價"
        }
    )

    st.line_chart(
        chart_df,
        use_container_width=True
    )

    st.caption(
        "圖表顯示最近 120 個交易日的"
        "收盤價與移動平均線。"
    )


    # ==================================================
    # 技術指標摘要
    # ==================================================

    st.divider()
    st.subheader("技術指標摘要")

    indicator_col1, indicator_col2, indicator_col3 = st.columns(3)

    with indicator_col1:
        st.metric(
            "MA5",
            f"{ma5:.2f}"
        )

        st.metric(
            "MA20",
            f"{ma20:.2f}"
        )

        st.metric(
            "MA60",
            f"{ma60:.2f}"
        )

    with indicator_col2:
        st.metric(
            "RSI",
            f"{rsi:.2f}"
        )

        st.metric(
            "MACD",
            f"{macd:.4f}"
        )

        st.metric(
            "Signal",
            f"{signal:.4f}"
        )

    with indicator_col3:
        st.metric(
            "K",
            f"{k:.2f}"
        )

        st.metric(
            "D",
            f"{d:.2f}"
        )

        st.metric(
            "ATR Percent",
            f"{atr_percent:.2f}%"
        )


    # ==================================================
    # 完整技術指標
    # ==================================================

    with st.expander(
        "查看完整技術指標表格",
        expanded=False
    ):

        indicator_data = {
            "指標": [
                "評分使用價格",
                "最新日線收盤價",
                "MA5",
                "MA20",
                "MA60",
                "RSI",
                "MACD",
                "Signal",
                "MACD Histogram",
                "K",
                "D",
                "ATR",
                "ATR Percent",
                "成交量"
            ],
            "數值": [
                f"{current_price:.2f}",
                f"{historical_close:.2f}",
                f"{ma5:.2f}",
                f"{ma20:.2f}",
                f"{ma60:.2f}",
                f"{rsi:.2f}",
                f"{macd:.4f}",
                f"{signal:.4f}",
                f"{macd - signal:.4f}",
                f"{k:.2f}",
                f"{d:.2f}",
                f"{atr:.2f}",
                f"{atr_percent:.2f}%",
                f"{int(volume):,}"
            ]
        }

        indicator_df = pd.DataFrame(
            indicator_data
        )

        st.dataframe(
            indicator_df,
            hide_index=True,
            use_container_width=True
        )


    # ==================================================
    # 分析原因
    # ==================================================

    st.divider()
    st.subheader("分析原因")

    for reason in reasons:
        display_reason(reason)


    # ==================================================
    # AI 結論
    # ==================================================

    st.divider()
    st.subheader("AI 結論")

    display_conclusion(score)

    st.caption(
        "注意：本系統為規則型技術分析工具，"
        "不構成投資建議，也不代表未來報酬或獲利保證。"
    )


# ==================================================
# 頁尾
# ==================================================

st.divider()

st.caption(
    "AI 台股分析系統 v1.0.0｜"
    "Developed by 子珺 袁｜"
    "Tamkang University Aerospace Engineering"
)