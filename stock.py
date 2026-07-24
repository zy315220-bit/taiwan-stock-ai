import pandas as pd
import yfinance as yf


def flatten_columns(df):

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.loc[:, ~df.columns.duplicated()].copy()

    return df


def download_stock(stock_code):

    stock_code = stock_code.strip().upper()

    if not stock_code:
        raise ValueError("股票代號不能空白。")

    if stock_code.endswith(".TW") or stock_code.endswith(".TWO"):
        ticker_list = [stock_code]
    else:
        ticker_list = [
            stock_code + ".TW",
            stock_code + ".TWO"
        ]

    for ticker in ticker_list:

        try:
            # ===== 1. 下載一年日線資料 =====
            daily = yf.download(
                ticker,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )

            if daily is None or daily.empty:
                continue

            daily = flatten_columns(daily)

            required_columns = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            if not all(
                column in daily.columns
                for column in required_columns
            ):
                continue

            for column in required_columns:
                daily[column] = pd.to_numeric(
                    daily[column],
                    errors="coerce"
                )

            daily = daily.dropna(subset=["Close"]).copy()

            # ===== 2. 下載最近 5 分鐘資料 =====
            intraday = yf.download(
                ticker,
                period="5d",
                interval="5m",
                progress=False,
                auto_adjust=False,
                threads=False,
                prepost=False
            )

            if intraday is not None and not intraday.empty:

                intraday = flatten_columns(intraday)

                if all(
                    column in intraday.columns
                    for column in required_columns
                ):
                    for column in required_columns:
                        intraday[column] = pd.to_numeric(
                            intraday[column],
                            errors="coerce"
                        )

                    intraday = intraday.dropna(
                        subset=["Close"]
                    ).copy()

                    if not intraday.empty:

                        # 將時間轉為台北時間
                        if intraday.index.tz is not None:
                            intraday.index = (
                                intraday.index
                                .tz_convert("Asia/Taipei")
                            )

                        # 取得最近一個交易日
                        latest_date = intraday.index[-1].date()

                        latest_intraday = intraday[
                            intraday.index.date == latest_date
                        ]

                        if not latest_intraday.empty:

                            latest_open = float(
                                latest_intraday["Open"].iloc[0]
                            )

                            latest_high = float(
                                latest_intraday["High"].max()
                            )

                            latest_low = float(
                                latest_intraday["Low"].min()
                            )

                            latest_close = float(
                                latest_intraday["Close"].iloc[-1]
                            )

                            latest_volume = float(
                                latest_intraday["Volume"].sum()
                            )

                            latest_index = pd.Timestamp(latest_date)

                            # 更新或新增最新交易日
                            daily.loc[
                                latest_index,
                                "Open"
                            ] = latest_open

                            daily.loc[
                                latest_index,
                                "High"
                            ] = latest_high

                            daily.loc[
                                latest_index,
                                "Low"
                            ] = latest_low

                            daily.loc[
                                latest_index,
                                "Close"
                            ] = latest_close

                            daily.loc[
                                latest_index,
                                "Volume"
                            ] = latest_volume

            daily = daily.sort_index()

            daily.attrs["ticker"] = ticker

            return daily

        except Exception as error:
            print(f"{ticker} 下載失敗：{error}")
            continue

    raise ValueError(
        f"找不到股票代號 {stock_code}，"
        "請確認股票代號是否正確。"
    )