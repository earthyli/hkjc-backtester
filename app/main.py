import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from strategy import run_backtest_logic, check_live_race_signals

st.set_page_config(page_title="HKJC 赛马智能决策系统", layout="wide")

# ==================== 左侧边栏 (Sidebar) ====================
st.sidebar.header("🧭 系统模式与参数")
mode = st.sidebar.radio("选择运行模式", ["📊 历史策略回测", "🚨 临场实时监控"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 策略参数设置")
threshold = st.sidebar.slider("独赢/位置 赔率比阈值 (WIN/PLA Ratio)", min_value=4.0, max_value=12.0, value=8.5, step=0.5)

# 🌟 新增：临场砸盘策略的核心过滤阈值（位置赔率瞬间缩水比例）
steam_drop = st.sidebar.slider("🔥 临场位置赔率砸盘跌幅阈值", min_value=10, max_value=40, value=20, step=5) / 100.0

bet_size = st.sidebar.number_input("单场单注本金 (HKD)", min_value=10, max_value=1000, value=100)

st.sidebar.markdown("---")
st.sidebar.header("📜 选马量化铁律说明")
st.sidebar.markdown(f"""
> 💡 **核心逻辑 (Ratio + Late Steam)：**
> 系统目前由【双重指标】交叉锁定：
> 1. $\\text{{当前赔率比}} \\ge {threshold:,.1f}$
> 2. $\\text{{位置赔率临场跌幅}} \\ge {steam_drop*100:,.0f}\\%$
> 只有当大资金在临场最后两分钟疯狂扫货、导致位置赔率瞬间缩水超过目标比例时，系统才会触发狙击信号。

⚔️ **两大下注铁律：**
1. **只打位置 (PLACE)**：利用聪明钱的防守厚度，只买位置。
2. **同场去重 (狙击龙头)**：单场只买位置被砸得最凶的一匹马。
""")

# ==================== 右侧主面板数据处理 ====================
@st.cache_data
def load_real_hkjc_data():
    json_path = "data/history_races.json"
    if os.path.exists(json_path):
        return pd.read_json(json_path)
    return pd.DataFrame()

df = load_real_hkjc_data()

if mode == "📊 历史策略回测":
    st.title("🏇 HKJC 赛马策略历史回测面板")
    if not df.empty:
        results = run_backtest_logic(df, win_pla_threshold=threshold, bet_amount=bet_size)
        st.header("📊 回测核心业绩指标")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("总触发下注次数", f"{results['total_bets']} 次")
        with col2: st.metric("核心胜率 (Win Rate)", f"{results['win_rate']:.2f}%")
        with col3: st.metric("净利润 (Net Profit)", f"${results['net_profit']:.2f} HKD", delta=f"${results['net_profit']:.2f}")
        with col4: st.metric("投资回报率 (ROI)", f"{results['roi']:.2f}%", delta=f"{results['roi']:.2f}%")

        st.subheader("📋 策略触发交易明细")
        st.dataframe(results['details'].style.format({
            'win_odds': '{:.1f}', 'pla_odds': '{:.1f}', 'odds_ratio': '{:.2f}', 'payout': '${:.1f}'
        }), use_container_width=True)
    else:
        st.warning("⚠️ 未找到真实历史数据文件！请先在 Trae 终端运行：python3 fetch_real_data.py")

elif mode == "🚨 临场实时监控":
    st.title("🚨 HKJC 临场秒级资金异动监控 (砸盘捕获版)")
    st.warning("📢 **数据源状态提示**：今天非香港官方赛马日。系统目前正在运行【实战砸盘大盘模拟环境】，数据仅供策略演示。")
    
    st.markdown("### 📅 当前监控赛事基本信息")
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1: st.info("季度日期：2026年06月16日 (模拟)")
    with info_col2: st.info("🏟️ 比赛场地：香港沙田马场 (Sha Tin)")
    with info_col3: st.info("跑道材质：草地 - A 跑道 (晴天/好地)")
    with info_col4: st.info("🎯 当前目标场次：第 3 场 (Race 3)")
        
    st.markdown("---")
    st.subheader("🕒 下一场开赛倒计时：分秒级临场波动")
    if st.button("🔄 立即模拟临场最后一分钟赔率刷新"):
        st.toast("正在重新捕获最后 60 秒盘口暴跌信号...", icon="⚡")
    
    # 构建包含时间线跨度的模拟大盘
    np.random.seed(random.randint(1, 1000)) 
    
    # 1. 模拟开赛前 15 分钟的初始大盘
    initial_win = np.random.uniform(5.0, 60.0, 12).round(1)
    initial_pla = (initial_win / np.random.uniform(3.0, 6.0, 12)).round(1)
    
    # 2. 模拟临场最后一分钟的大盘（大部分马赔率正常微调）
    live_win = (initial_win * np.random.uniform(0.96, 1.04, 12)).round(1)
    live_pla = (initial_pla * np.random.uniform(0.96, 1.04, 12)).round(1)
    
    # 🌟 强行让 5号马（索引4）在最后 1 分钟发生恐怖的“主力巨资砸盘”事件：
    initial_win[4] = 50.0
    initial_pla[4] = 6.5   # 初始 Ratio 是 7.69 (未达到 8.5)
    
    live_win[4] = 45.0
    live_pla[4] = 4.2      # 临场突然被大资金疯狂注入！位置赔率直接被砸到 4.2，跌幅高达 35.4%！
    
    df_live = pd.DataFrame({
        'horse_no': list(range(1, 13)),
        'horse_name': [f"闪电侠_{i}号" for i in range(1, 13)],
        'initial_win_odds': initial_win,
        'initial_pla_odds': initial_pla,
        'win_odds': live_win,
        'pla_odds': live_pla
    })
    
    # 调用升级版的实时监控大脑
    signal = check_live_race_signals(df_live, win_pla_threshold=threshold, late_steam_threshold=steam_drop)
    
    # 触发警报
    if signal is not None:
        st.error(f"🔥 ⚠️ 【绝对砸盘警报】沙田第 3 场侦测到超级基金【末期落飞（Late Steamer）】大动作！")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("🎯 狙击龙头马匹", f"{int(signal['horse_no'])} 号马 ({signal['horse_name']})")
        with c2: st.metric("🛡️ 临场位置赔率", f"{signal['pla_odds']} 倍", delta=f"从 {signal['initial_pla_odds']} 跌落")
        with c3: st.metric("📉 位置盘口跌幅", f"{signal['pla_drop']*100:.1f}%", delta="已破危险线", delta_color="inverse")
        with c4: st.metric("⚡ 当前独赢/位置比", f"{signal['odds_ratio']:.2f}")
        
        st.markdown(f"💡 **终极实战决策**：**{int(signal['horse_no'])}号马 ({signal['horse_name']})** 在最后关头被神秘主力资金疯狂砸盘，位置赔率瞬间**缩水暴跌了 {signal['pla_drop']*100:.1f}%**！这符合巨鳄扫货的绝对特征。建议立刻投入 **${bet_size} HKD** 全力狙击其 **位置 (PLACE)**！")
    else:
        st.success("✅ 临场最后阶段没有出现主力恶意砸盘和吸筹现象，大盘资金安全，建议本场冷静观望。")
        
    st.subheader("📋 第 3 场：大盘多维度临场对比看板")
    df_live['odds_ratio'] = df_live['win_odds'] / df_live['pla_odds']
    df_live['pla_drop_pct'] = df_live['pla_drop'] * 100
    
    # 格式化表格输出
    st.dataframe(df_live.style.format({
        'initial_win_odds': '{:.1f}', 'initial_pla_odds': '{:.1f}',
        'win_odds': '{:.1f}', 'pla_odds': '{:.1f}', 
        'odds_ratio': '{:.2f}', 'pla_drop_pct': '{:.1f}%'
    }), use_container_width=True)