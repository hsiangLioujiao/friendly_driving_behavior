import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import seaborn as sns
import streamlit as st



pd.options.mode.copy_on_write = True
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
plt.rcParams["font.size"] = 14
plt.rcParams['font.family'] = 'Taipei Sans TC Beta'

st.set_page_config(page_title = "功能打樣版 僅供3人同時使用", page_icon = "random")




def test_columns_correctness(cols, df):
    if set(cols).issubset(df.columns):
        return True
    else:
        missing = list(set(cols) - set(df.columns))
        st.write(f"所上傳的檔案缺少 {missing} 欄位")



st.header("電動公車駕駛友善度統計 - V0.11")

st.sidebar.header("")
st.sidebar.header("")
st.sidebar.header("")
st.sidebar.subheader("輸入準則：")
maximum_acceleration = st.sidebar.number_input("允許的最大加速度[m/s^2]", value=1, placeholder="Type a number...")
maximum_jerk = st.sidebar.number_input("允許的最大加加速(Jerk)[m/s^3]", value=0.6, placeholder="Type a number...")
st.sidebar.header("")
st.sidebar.header("")
st.sidebar.write("參考資料：")
st.sidebar.write("UCL(倫敦大學學院)，高齡乘客無障礙運輸研究，https://discovery.ucl.ac.uk/id/eprint/10120841/1/Karekla_OperationalBusCharacteristics_Accepted.pdf")

st.write("可自行上傳具有日期時間及車速資料之檔案(.xlsx)。")
st.write("檔案首列(row)為「日期時間」及「車速」兩欄位名稱, 其餘列的內容為數字。")
st.write("日期時間資料為datetime64[ns]格式，車速資料的單位為km/h。")
st.write("")
uploaded_file=st.file_uploader("選擇上傳檔案：", type=".xlsx") 
st.write("")

data_correctness = False
cols=['日期時間', '車速']
if uploaded_file:
    df=pd.read_excel(uploaded_file)
    st.write("已上傳檔案：", uploaded_file.name)
    st.write(f"上傳的行駛操作資料(共{len(df)}筆紀錄)：")
    data_correctness=test_columns_correctness(cols, df)
    st.session_state['uploaded_file'] = uploaded_file
else:
    df=pd.read_excel('demo.xlsx')
    st.write(f"預設的行駛操作資料(共{len(df)}筆紀錄)：")
    data_correctness=True

st.divider()

if data_correctness:
    df=df[cols].sort_values(by="日期時間").reset_index(drop=True)
    df["dt[s]"] = df["日期時間"].diff().dt.total_seconds() # 時間差
    df["dV[m/s]"] = df["車速"].diff() / 3.6 # 速度差
    df["加速度"] = df["dV[m/s]"] / df["dt[s]"]
    df["da[m/s^2]"] = df["加速度"].diff()
    df["加加速"] = df["da[m/s^2]"] / df["dt[s]"]
    styled_df = df[['車速', '加速度', '加加速']].describe().style\
        .set_properties(**{
            'font-size': '18px',
            'text-align': 'center',
            'font-weight': 'bold'
        })\
        .format(precision=2)
    st.table(styled_df)


    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    sns.boxplot(y=df["車速"].dropna(), ax=axes[0], color="lightblue", width=0.4)
    axes[0].set_title("車速盒鬚圖", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("車速[km/h]", fontsize=12)
    axes[0].grid(axis="y", linestyle=":", alpha=0.6)

    sns.boxplot(y=df["加速度"].dropna(), ax=axes[1], color="lightgreen", width=0.4)
    axes[1].set_title("加速度盒鬚圖", fontsize=14, fontweight="bold")
    axes[1].set_ylabel("加速度[m/s²]", fontsize=12)
    axes[1].grid(axis="y", linestyle=":", alpha=0.6)

    sns.boxplot(y=df["加加速"].dropna(), ax=axes[2], color="salmon", width=0.4)
    axes[2].set_title("加加速(Jerk)盒鬚圖", fontsize=14, fontweight="bold")
    axes[2].set_ylabel("加加速[m/s³]", fontsize=12)
    axes[2].grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    st.pyplot(fig)


    df["距離"] = df["車速"] * df["dt[s]"] / 3600 # km
    total_hours = df["dt[s]"].sum() / 3600
    total_km = df["距離"].sum()

    # 不友善事件
    is_unfriendly = (df["加速度"].abs() > 1.0) | (df["加加速"].abs() > 0.6)
    unfriendly_points = is_unfriendly.sum()
    # unfriendly_hr = is_unfriendly.sum() / 3600
    # unfriendly_km = df.loc[is_unfriendly, "距離"].sum()
    freq_per_hour_points = unfriendly_points / total_hours
    freq_per_km_points = unfriendly_points / total_km

    # 標記事件開始點
    df["is_unfriendly"] = is_unfriendly.astype(int)
    df["event_start"] = (df["is_unfriendly"] == 1) & (df["is_unfriendly"].shift(1) == 0)

    # 處理第一筆資料的邊界條件
    if df["is_unfriendly"].iloc[0] == 1:
        df.loc[0, "event_start"] = True

    total_unfriendly_events = df["event_start"].sum()
    freq_hour_events = total_unfriendly_events / total_hours
    freq_km_events = total_unfriendly_events / total_km    

    st.subheader(f"📊 ====== 駕駛行為友善度統計報告 ======")
    st.write(f"總行駛時間: {total_hours:.1f} 小時")
    st.write(f"總行駛距離: {total_km:.1f} 公里")
    st.write(f"總紀錄筆數: {len(df)} 筆")
    st.write(f"不友善行為紀錄: {unfriendly_points} 筆")
    st.write(f"不友善連續事件: {total_unfriendly_events} 次\n")

    st.subheader(f"⏱️【時間】發生頻率:")
    st.write(f"  - 每小時平均發生: {freq_per_hour_points:.0f} 筆不友善行為紀錄")
    st.write(f"  - 每小時平均發生: {freq_hour_events:.0f} 次連續事件")
    st.subheader(f"🛣️【距離】發生頻率:")
    st.write(f"  - 每公里平均發生: {freq_per_km_points:.0f} 筆不友善行為紀錄")
    st.write(f"  - 每公里平均發生: {freq_km_events:.0f} 次連續事件")
