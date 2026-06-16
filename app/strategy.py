import pandas as pd

def run_backtest_logic(df_runners, win_pla_threshold=7.5, bet_amount=100):
    """
    历史策略回测引擎（保持不变）
    """
    if df_runners.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": df_runners}

    df_runners['odds_ratio'] = df_runners['win_odds'] / df_runners['pla_odds']
    potential_bets = df_runners[df_runners['odds_ratio'] >= win_pla_threshold].copy()
    
    if potential_bets.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": potential_bets}

    best_indices_per_race = potential_bets.groupby('race_id')['odds_ratio'].idxmax()
    selected_bets = potential_bets.loc[best_indices_per_race].copy()

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
        "total_investment": total_investment,
        "total_return": total_return,
        "net_profit": net_profit,
        "win_rate": win_rate,
        "roi": roi,
        "details": selected_bets[['race_id', 'horse_no', 'win_odds', 'pla_odds', 'odds_ratio', 'is_top_three', 'payout']]
    }


def check_live_race_signals(df_live_runners, win_pla_threshold=8.5, late_steam_threshold=0.20):
    """
    🔥 升级版：临场砸盘实时监控算法
    late_steam_threshold=0.20 代表主力资金在最后关头把位置赔率砸低了 20% 以上
    """
    if df_live_runners.empty:
        return None
        
    # 1. 计算临场当前的独赢/位置比率
    df_live_runners['odds_ratio'] = df_live_runners['win_odds'] / df_live_runners['pla_odds']
    
    # 2. 计算位置赔率相比 15分钟前的 临场跌幅 (Drop Rate)
    # 跌幅公式 = (初始位置赔率 - 临场位置赔率) / 初始位置赔率
    df_live_runners['pla_drop'] = (df_live_runners['initial_pla_odds'] - df_live_runners['pla_odds']) / df_live_runners['initial_pla_odds']
    
    # 3. ⚖️ 双重铁律交叉过滤：
    # 条件一：当前 Ratio 达到安全线 (说明性价比极高)
    # 条件二：最后关头位置赔率被强行砸低 20% 以上 (坐实超级巨鳄疯狂建仓行为)
    triggered = df_live_runners[
        (df_live_runners['odds_ratio'] >= win_pla_threshold) & 
        (df_live_runners['pla_drop'] >= late_steam_threshold)
    ]
    
    if triggered.empty:
        return None
        
    # 4. 同场去重：只推荐主力砸盘砸得最狠（跌幅最大）的那一匹绝对核心马
    best_pick = triggered.loc[triggered['pla_drop'].idxmax()]
    return best_pick