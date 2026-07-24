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
    layout="wide"
)

# ==================================================
# 首頁標題
# ==================================================

st.title("📈 AI 台股分析系統")

st.markdown("""
### 🤖 Intelligent Taiwan Stock Analyzer

**Developer：子珺 袁**

🎓 Tamkang University - Aerospace Engineering

Version **1.0.0**
""")

st.info(
    "本系統使用歷史日線計算技術指標，並結合最新成交價進行即時分析。"
)

st.divider()
# ==================================================
# 股票輸入區
# ==================================================

stock = st.text_input(
    "請輸入台股代號",
    value="0056",
    placeholder="例如：2330、0050、0056"
).strip().upper()

analyze_button = st.button(
    "開始分析",
    type="primary",
    use_container_width=True
)


# ==================================================
# 執行分析
# ==================================================

if analyze_button:

    if not stock:
        st.error("股票代號不能空白。")
        st.stop()

    try:
        with st.spinner("正在下載歷史資料與最新行情..."):

            # 下載歷史資料
            df = download_stock(stock)

            if df is None or df.empty:
                raise ValueError("找不到股票歷史資料。")

            if len(df) < 60:
                raise ValueError(
                    f"資料只有 {len(df)} 個交易日，"
                    "至少需要 60 個交易日。"
                )

            # 計算技術指標
            df = add_indicators(df)
            df = df.dropna().copy()

            if df.empty:
                raise ValueError(
                    "技術指標計算後沒有可用資料。"
                )

            latest = df.iloc[-1]
            latest_date = df.index[-1]

            historical_close = float(latest["Close"])

            # 取得即時行情
            try:
                realtime = get_realtime_price(stock)
            except Exception:
                realtime = None

            if (
                realtime is not None
                and realtime.get("price") is not None
            ):
                current_price = float(realtime["price"])
                price_source = "最新成交價"
            else:
                current_price = historical_close
                price_source = "最新日線收盤價"

            # 計算評分
            score, reasons = calculate_score(
                df,
                current_price=current_price
            )

            grade, stars, advice = get_rating(score)

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

            risk = risk_level(
                atr,
                current_price
            )

    except Exception as error:
        st.error(f"分析失敗：{error}")
        st.stop()

    # ==================================================
    # 最新行情
    # ==================================================

    st.subheader("最新行情")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "最新成交價",
        f"{current_price:,.2f}"
    )

    if realtime is not None:

        change = realtime.get("change")
        change_percent = realtime.get("change_percent")

        if (
            change is not None
            and change_percent is not None
        ):
            col2.metric(
                "今日漲跌",
                f"{float(change):+.2f}",
                f"{float(change_percent):+.2f}%"
            )
        else:
            col2.metric(
                "今日漲跌",
                "無資料"
            )

        col3.metric(
            "行情時間",
            f"{realtime.get('date', '')} "
            f"{realtime.get('time', '')}"
        )

        col4.metric(
            "市場",
            realtime.get("market", "未知")
        )

    else:
        col2.metric(
            "今日漲跌",
            "無即時資料"
        )

        col3.metric(
            "歷史資料日期",
            latest_date.strftime("%Y-%m-%d")
        )

        col4.metric(
            "價格來源",
            price_source
        )

    st.caption(
        f"最新日線收盤價：{historical_close:.2f}｜"
        f"評分使用價格：{current_price:.2f}｜"
        f"價格來源：{price_source}"
    )

    # ==================================================
    # AI 綜合評分
    # ==================================================

    st.divider()
    st.subheader("AI 綜合評分")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "AI Score",
        f"{score}/100"
    )

    col2.metric(
        "Grade",
        grade
    )

    col3.metric(
        "Recommendation",
        advice
    )

    col4.metric(
        "Risk",
        risk
    )

    st.write(f"**Rating：{stars}**")

    st.progress(
        min(max(score, 0), 100) / 100
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

    st.line_chart(
        chart_df,
        use_container_width=True
    )

    # ==================================================
    # 技術指標
    # ==================================================

    st.divider()
    st.subheader("技術指標")

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
            f"{atr / current_price * 100:.2f}%",
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

        match = re.search(
            r"\(\+(-?\d+(?:\.\d+)?)\)",
            reason
        )

        if match:
            reason_score = float(match.group(1))
        else:
            reason_score = None

        if reason_score is None:
            st.info(reason)

        elif reason_score <= 0:
            st.error(f"🔴 {reason}")

        elif reason_score < 7:
            st.warning(f"🟡 {reason}")

        else:
            st.success(f"🟢 {reason}")

    # ==================================================
    # AI 結論
    # ==================================================

    st.divider()
    st.subheader("AI 結論")

    if score >= 85:
        st.success(
            "目前技術面強勢，多項指標同步偏多。"
            "可等待拉回後分批布局，但應避免追高。"
        )

    elif score >= 70:
        st.success(
            "整體技術面偏多，但部分指標仍存在短線壓力。"
        )

    elif score >= 55:
        st.info(
            "多空訊號混合，目前尚未形成明確趨勢。"
        )

    elif score >= 40:
        st.warning(
            "目前技術面偏弱，空方訊號略占優勢。"
        )

    else:
        st.error(
            "目前空方訊號較多，整體技術面明顯偏弱。"
        )

    st.caption(
        "注意：本系統是規則型技術分析工具，"
        "不代表未來報酬或獲利保證。"
    )