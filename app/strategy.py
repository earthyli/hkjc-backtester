# -*- coding: utf-8 -*-
import pandas as pd

def run_backtest_logic(df_runners, win_pla_threshold=7.5, bet_amount=100):
    """
    历史策略回测引擎（读取本地历史特征JSON）
    """
    if df_runners.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": df_runners}

    # 1. 计算赔率比
    df_runners['odds_ratio'] = df_runners['win_odds'] / df_runners['pla_odds']
    
    # 2. 筛选冲破安全线的马
    potential_bets = df_runners[df_runners['odds_ratio'] >= win_pla_threshold].copy()
    if potential_bets.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": potential_bets}

    # 3. 严格执行同场去重铁律
    best_indices_per_race = potential_bets.groupby('race_id')['odds_ratio'].idxmax()
    selected_bets = potential_bets.loc[best_indices_per_race].copy()

    # 4. 模拟派彩结算
    total_bets = len(selected_bets)
    total_investment = total_bets * bet_amount
    
    selected_bets['payout'] = selected_bets.apply(
        lambda row: (bet_amount * row['pla_odds'] * 0.95) if row['is_top_three'] else 0, axis=1
    )
    
    total_return = selected_bets['payout'].sum()
    net_profit = total_return - total_investment
    win_rate = (selected_bets['is_top_three'].sum() / total_bets) * 100 if total_bets > 0 else 0
    roi = (net_profit / total_investment) * 100 if total_investment > 0 else 0
    
    return {
        "total_bets": total_bets,
        "net_profit": net_profit,
        "win_rate": win_rate,
        "roi": roi,
        "details": selected_bets[['race_id', 'horse_no', 'win_odds', 'pla_odds', 'odds_ratio', 'is_top_three', 'payout']]
    }


def check_live_race_signals(df_live_runners, win_pla_threshold=8.5, late_steam_threshold=0.20):
    """
    实战临场砸盘雷达核心算法
    """
    if df_live_runners.empty:
        return None
        
    # 计算临场当前的独赢/位置比率
    df_live_runners['odds_ratio'] = df_live_runners['win_odds'] / df_live_runners['pla_odds']
    
    # 计算位置赔率相比15分钟前的砸盘缩水跌幅
    df_live_runners['pla_drop'] = (df_live_runners['initial_pla_odds'] - df_live_runners['pla_odds']) / df_live_runners['initial_pla_odds']
    
    # ⚔️ 双重指标交叉锁定
    triggered = df_live_runners[
        (df_live_runners['odds_ratio'] >= win_pla_threshold) & 
        (df_live_runners['pla_drop'] >= late_steam_threshold)
    ]
    
    if triggered.empty:
        return None
        
    # 💥 同场去重铁律：只抓在临场最后关头主力扫货扫得最凶（跌幅最大）的那一匹龙头马
    best_pick = triggered.loc[triggered['pla_drop'].idxmax()]
    return best_pick