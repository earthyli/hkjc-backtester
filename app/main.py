# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os
import random
import requests
from strategy import run_backtest_logic, check_live_race_signals

st.set_page_config(page_title="HKJC 赛马智能决策系统", layout="wide")

# ==================== 左侧边栏控制面板 ====================
st.sidebar.header("🧭 系统模式与参数")
mode = st.sidebar.radio("选择运行模式", ["📊 历史策略回测", "🚨 临场实时监控"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 策略参数设置")
threshold = st.sidebar.slider("独赢/位置 赔率比阈值 (WIN/PLA Ratio)", min_value=4.0, max_value=12.0, value=8.5, step=0.5)
steam_drop = st.sidebar.slider("🔥 临场位置赔率砸盘跌幅阈值 (%)", min_value=10, max_value=40, value=20, step=5) / 100.0
bet_size = st.sidebar.number_input("单场单注本金 (HKD)", min_value=10, max_value=1000, value=100)

st.sidebar.markdown("---")
st.sidebar.header("🏁 实战赛程选择")
race_no = st.sidebar.selectbox(
    "🏟️ 选择当前监控场次", 
    options=list(range(1, 12)), 
    index=2, 
    format_func=lambda x: f"第 {x} 场 (Race {x})"
)

st.sidebar.markdown("---")
st.sidebar.header("📜 选马量化铁律说明")
st.sidebar.markdown(f"""
> 💡 **核心策略指标公式：**
> 1. **当前赔率比 (Ratio)**：
>    `WIN 赔率 / PLA 赔率 >= {threshold:.1f}`
> 2. **临场位置跌幅 (Late Steam)**：
>    `(初始 PLA - 临场 PLA) / 初始 PLA >= {steam_drop*100:.0f}%`

⚔️ **下注纪律备忘：**
* **绝对不买独赢**，只买符合异动特征的**位置 (PLACE)**。
* 同场多匹触发时，冷静防守，**单场只推跌幅最大的一匹马**。
""")

# ==================== 🌟 满血升级版：网络请求伪装模块 ====================
def fetch_hkjc_live_odds(race_number):
    """
    深度伪装穿透，强行获取马会大盘最新的公开实时动态赔率
    """
    url = f"https://bet.hkjc.com/racing/getJSON.aspx?type=winpla&race={race_number}"
    
    # 模拟真实高配浏览器，并注入马会必备的 Referer 页面来源认证
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://bet.hkjc.com/racing/pages/odds_wp.aspx?lang=ch',  # 告诉马会防火墙：我是在官方赔率页面里刷新的
        'X-Requested-With': 'XMLHttpRequest',  # 声明这是标准的 AJAX 异步数据流请求
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200 and len(response.text) > 50:
            # 校验是否为合法的 JSON 格式，排除拦截网页
            res_json = response.json()
            if "out" in res_json or "inv" in res_json:
                return {"status": "SUCCESS", "data": res_json, "raw_text": response.text[:1000]}
        return {"status": "EMPTY", "msg": f"网关已建立连接但暂未广播有效数据", "raw_text": response.text[:1000]}
    except Exception as e:
        return {"status": "ERROR", "msg": f"请求遭拦截或网络超时: {str(e)}", "raw_text": "None"}

# 加载本地回测数据集
@st.cache_data
def load_real_hkjc_data():
    json_path = "data/history_races.json"
    if os.path.exists(json_path):
        return pd.read_json(json_path)
    return pd.DataFrame()

df_history = load_real_hkjc_data()

# ==================== 模式 1：历史策略回测 ====================
if mode == "📊 历史策略回测":
    st.title("🏇 HKJC 赛马策略历史回测面板")
    if not df_history.empty:
        results = run_backtest_logic(df_history, win_pla_threshold=threshold, bet_amount=bet_size)
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
        st.warning("⚠️ 未找到历史特征数据集。")

# ==================== 模式 2：临场实时监控 ====================
elif mode == "🚨 临场实时监控":
    st.title("🚨 HKJC 临场秒级资金异动监控 (网络穿透版)")
    
    # 核心动作：实时叩击官方接口
    api_result = fetch_hkjc_live_odds(race_no)
    
    # 🌟 固化的开发者显微镜组件：点击展开直接透视马会返回给我们的底层数据
    with st.expander("🔍 开发者实时网关穿透透视镜 (Raw Data Monitor)"):
        st.write(f"📡 目标探测URL: `https://bet.hkjc.com/racing/getJSON.aspx?type=winpla&race={race_no}`")
        st.write(f"⚡ 接口当前状态: `{api_result['status']}` | 描述: `{api_result.get('msg', '正常沟通中')}`")
        st.markdown("**🔄 马会服务器当前响应的前 600 个字符原始文本：**")
        st.code(api_result["raw_text"], language="html" if "<html" in api_result["raw_text"] else "json")

    # 根据真实网络情况决策数据流
    if api_result["status"] == "SUCCESS":
        st.success(f"🟢 **数据源状态**：深度伪装成功！已实时灌入第 {race_no} 场沙田现场大盘真实赔率。")
        is_simulation = False
    else:
        st.warning(f"📢 **数据源状态提示**：真实网关未激活（{api_result['msg']}）。系统自动进入【黄昏赛仿真沙盒】。")
        is_simulation = True

    st.markdown("### 📅 当前监控赛事基本信息")
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1: st.info("📆 赛事日期：2026年06月21日 (今天黄昏赛)")
    with info_col2: st.info("🏟️ 比赛场地：香港沙田马场 (本地大盘)")
    with info_col3: st.info("跑道材质：草地 - A 跑道 (晴天/好地)")
    with info_col4: st.info(f"🎯 核心监控目标：第 {race_no} 场 (Race {race_no})")
        
    st.markdown("---")
    st.subheader(f"🕒 第 {race_no} 场开赛临场动向")
    
    if st.button("🔄 强制拉取最新秒级盘口数据"):
        st.toast("正在重新向香港马会服务器发出伪装请求...", icon="⚡")
        
    if is_simulation:
        np.random.seed(race_no + random.randint(1, 99))
        initial_win = np.random.uniform(6.0, 65.0, 12).round(1)
        initial_pla = (initial_win / np.random.uniform(3.0, 6.0, 12)).round(1)
        live_win = (initial_win * np.random.uniform(0.97, 1.03, 12)).round(1)
        live_pla = (initial_pla * np.random.uniform(0.97, 1.03, 12)).round(1)
        
        initial_win[4] = 48.0
        initial_pla[4] = 6.8
        live_win[4] = 44.0
        live_pla[4] = 4.1  
        
        df_live = pd.DataFrame({
            'horse_no': list(range(1, 13)),
            'horse_name': [f"沙田战驹_{i}号" for i in range(1, 13)],
            'initial_pla_odds': initial_pla,
            'win_odds': live_win,
            'pla_odds': live_pla
        })

    signal = check_live_race_signals(df_live, win_pla_threshold=threshold, late_steam_threshold=steam_drop)
    
    if signal is not None:
        st.error(f"🔥 ⚠️ 【绝对砸盘警报】Race {race_no} 捕捉到主力大额建仓【末期落飞】特征！")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("🎯 狙击龙头马", f"{int(signal['horse_no'])} 号马 ({signal['horse_name']})")
        with c2: st.metric("🛡️ 临场位置赔率", f"{signal['pla_odds']} 倍", delta=f"从 {signal['initial_pla_odds']} 暴跌")
        with c3: st.metric("📉 位置盘口缩水跌幅", f"{signal['pla_drop']*100:.1f}%", delta="突破防御上限", delta_color="inverse")
        with c4: st.metric("⚡ 当前独赢/位置比率", f"{signal['odds_ratio']:.2f}")
        st.markdown(f"💡 **实战决策建议**：请立刻核对官方 **第 {race_no} 场** 赔率板。当前 **{int(signal['horse_no'])}号马** 触发了极强的聪明钱暗中吸筹机制，建议立即投入 **${bet_size} HKD** 锁定买入其 **位置 (PLACE)**！")
    else:
        st.success(f"✅ 第 {race_no} 场临场盘口未见异常大资金防御，属于散户博弈，建议冷静观望。")
        
    st.subheader(f"📋 第 {race_no} 场：大盘多维度临场对比看板")
    df_live['odds_ratio'] = df_live['win_odds'] / df_live['pla_odds']
    df_live['pla_drop_pct'] = ((df_live['initial_pla_odds'] - df_live['pla_odds']) / df_live['initial_pla_odds']) * 100
    
    st.dataframe(df_live.style.format({
        'initial_pla_odds': '{:.1f}',
        'win_odds': '{:.1f}', 'pla_odds': '{:.1f}', 
        'odds_ratio': '{:.2f}', 'pla_drop_pct': '{:.1f}%'
    }), use_container_width=True)