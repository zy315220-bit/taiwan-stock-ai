from stock import download_stock
from realtime import get_realtime_price
from indicators import add_indicators
from score import calculate_score
from report import print_report


stock = input("請輸入股票代號：").strip()

if not stock:
    print("錯誤：股票代號不能空白。")

else:
    try:
        print("正在下載歷史資料...")

        df = download_stock(stock)

        if len(df) < 60:
            raise ValueError(
                f"資料只有 {len(df)} 個交易日，"
                "至少需要 60 個交易日。"
            )

        print("正在計算技術指標...")

        df = add_indicators(df)
        df = df.dropna().copy()

        if df.empty:
            raise ValueError("技術指標計算後沒有可用資料。")

        print("正在取得最新行情...")

        try:
            realtime = get_realtime_price(stock)
            current_price = realtime.get("price")

        except KeyboardInterrupt:
            print("\n已取消即時行情下載。")
            realtime = None
            current_price = None

        except Exception as error:
            print(f"\n最新行情取得失敗：{error}")
            print("改用最新完整日線收盤價進行評分。")
            realtime = None
            current_price = None

        print("正在計算評分...")

        score, reasons = calculate_score(
            df,
            current_price=current_price
        )

        print_report(
            stock,
            df,
            score,
            reasons,
            realtime
        )

    except KeyboardInterrupt:
        print("\n程式已由使用者中止。")

    except Exception as error:
        print(f"\n程式錯誤：{error}")