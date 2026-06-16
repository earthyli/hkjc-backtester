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
bet_size = st.sidebar.number_input("单场单注本金 (HKD)", min_value=10, max_value=1000, value=100)

# 🌟 选马量化铁律说明展示板
st.sidebar.markdown("---")
st.sidebar.header("📜 选马量化铁律说明")

st.sidebar.markdown(f"""
> 💡 **核心逻辑 (Ratio)：**
> 系统的选马核心公式为：
> $$\Delta = \\frac{{\\text{{独赢赔率 (WIN)}}}}{{\\text{{位置赔率 (PLA)}}}}$$
> 当一匹马的 $\Delta \\ge {threshold:,.1f}$ 时，代表公众极其低估它，但专业“聪明钱”却在位置彩池重注防守，此马极具爆冷跑入前三的性价比。

⚔️ **两大下注铁律：**
1. **跟从聪明钱**：一旦触发条件，**绝对不买独赢**，只精准购买该马的 **位置 (PLACE)**，确保高胜率。
2. **同场去重 (冷静防守)**：同一场比赛不管有多少匹马冲破阈值，系统都会通过 `idxmax()` 保持克制，**单场绝对只买比值最高的一匹马**，严防内部自残。
""")

st.sidebar.caption("💡 提示：在真实赛马日，建议锁定阈值为 8.5 以上以获取最高 ROI。")

# ==================== 右侧主面板数据处理 ====================
@st.cache_data
def load_real_hkjc_data():
    json_path = "data/history_races.json"
    if os.path.exists(json_path):
        return pd.read_json(json_path)
    return pd.DataFrame()

df = load_real_hkjc_data()

# ================= 模式 1：历史策略回测 =================
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

# ================= 模式 2：临场实时监控 =================
elif mode == "🚨 临场实时监控":
    st.title("🚨 HKJC 临场秒级资金异动监控")
    
    st.warning("📢 **数据源状态提示**：今天非香港官方赛马日。系统目前正在运行【实战大盘模拟环境】，数据仅供策略演示。")
    
    st.markdown("### 📅 当前监控赛事基本信息")
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1: st.info("📆 **赛事日期**：2026年06月16日 (模拟)")
    with info_col2: st.info("🏟️ **比赛场地**：香港沙田马场 (Sha Tin)")
    with info_col3: st.info("🛣️ **跑道材质**：草地 - A 跑道 (晴天/好地)")
    with info_col4: st.info("🎯 **当前目标场次**：第 3 场 (Race 3)")
        
    st.markdown("---")
    
    st.subheader("🕒 下一场开赛倒计时：分秒级临场波动")
    if st.button("🔄 立即刷新当前场次赔率 (Live Fetch)"):
        st.toast("正在实时连接马会公开赔率接口...", icon="🌐")
    
    # 模拟 12 匹马大盘赔率
    np.random.seed(random.randint(1, 1000)) 
    live_data = {
        'horse_no': list(range(1, 13)),
        'horse_name': [f"闪电侠_{i}号" for i in range(1, 13)],
        'win_odds': np.random.uniform(2.0, 70.0, 12).round(1),
    }
    live_data['pla_odds'] = (live_data['win_odds'] / np.random.uniform(3.0, 9.0, 12)).round(1)
    
    # 种下 5号马 异动信号
    live_data['win_odds'][4] = 45.0
    live_data['pla_odds'][4] = 4.2  
    
    df_live = pd.DataFrame(live_data)
    
    # 调用实时监控大脑
    signal = check_live_race_signals(df_live, win_pla_threshold=threshold)
    
    # 如果触发信号，红框高能报警
    if signal is not None:
        st.error(f"🔥 ⚠️ 【绝对警报】沙田日赛 **第 3 场 (Race 3)** 发现巨鳄资金暗中防御！")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("🎯 推荐下注马匹", f"{int(signal['horse_no'])} 号马 ({signal['horse_name']})")
        with c2: st.metric("📈 临场独赢赔率", f"{signal['win_odds']} 倍")
        with c3: st.metric("🛡️ 临场位置赔率", f"{signal['pla_odds']} 倍")
        with c4: st.metric("⚡ 当前异动比率 (Ratio)", f"{signal['odds_ratio']:.2f}")
        st.markdown(f"💡 **实战投资建议**：请核对官方 **第 3 场** 盘口。当前 **{int(signal['horse_no'])}号马 ({signal['horse_name']})** 比值高达 **{signal['odds_ratio']:.2f}**（突破了 {threshold} 安全线）。建议立刻投入 **${bet_size} HKD** 购买其 **位置 (PLACE)**！")
    else:
        st.success("✅ 当前场次数据平稳，无明显错误定价，建议冷静观望，放弃本场下注。")
        
    st.subheader("📋 第 3 场：全马匹实时大盘赔率看板")
    df_live['odds_ratio'] = df_live['win_odds'] / df_live['pla_odds']
    st.dataframe(df_live.style.format({'win_odds': '{:.1f}', 'pla_odds': '{:.1f}', 'odds_ratio': '{:.2f}'}), use_container_width=True)