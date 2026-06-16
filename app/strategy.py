import pandas as pd

def run_backtest_logic(df_runners, win_pla_threshold=7.5, bet_amount=100):
    """
    回测逻辑
    """
    if df_runners.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": df_runners}

    # 1. 计算每匹马的独赢与位置赔率比
    df_runners['odds_ratio'] = df_runners['win_odds'] / df_runners['pla_odds']
    
    # 2. 初步筛选
    potential_bets = df_runners[df_runners['odds_ratio'] >= win_pla_threshold].copy()
    
    if potential_bets.empty:
        return {"total_bets": 0, "roi": 0, "net_profit": 0, "win_rate": 0, "details": potential_bets}

    # 3. 同场去重
    best_indices_per_race = potential_bets.groupby('race_id')['odds_ratio'].idxmax()
    selected_bets = potential_bets.loc[best_indices_per_race].copy()

    # 4. 模拟结算
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
    } # 👈 注意这里：之前你的代码可能在这里漏掉了右边的闭合括号

def check_live_race_signals(df_live_runners, win_pla_threshold=8.5):
    # 实时临场监控
    if df_live_runners.empty:
        return None
        
    df_live_runners['odds_ratio'] = df_live_runners['win_odds'] / df_live_runners['pla_odds']
    
    triggered = df_live_runners[df_live_runners['odds_ratio'] >= win_pla_threshold]
    if triggered.empty:
        return None
        
    best_pick = triggered.loc[triggered['odds_ratio'].idxmax()]
    return best_pick