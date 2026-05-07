from backend.strategies.stat_arb import StatArbStrategy


def test_strategy_emits_yes_signal_when_fair_probability_is_higher():
    strategy = StatArbStrategy(min_edge=0.04, max_position_pct=0.1)
    signals = strategy.generate(
        [
            {
                "market_id": "m1",
                "captured_at": "2026-05-07T12:00:00Z",
                "yes_price": 0.45,
                "no_price": 0.55,
                "fair_probability": 0.56,
                "confidence": 0.7,
            }
        ],
        cash=1000,
    )

    assert len(signals) == 1
    assert signals[0].side == "BUY_YES"
    assert signals[0].quantity > 0


def test_strategy_ignores_small_edges():
    strategy = StatArbStrategy(min_edge=0.08)
    signals = strategy.generate(
        [
            {
                "market_id": "m1",
                "captured_at": "2026-05-07T12:00:00Z",
                "yes_price": 0.45,
                "no_price": 0.55,
                "fair_probability": 0.49,
                "confidence": 0.7,
            }
        ],
        cash=1000,
    )

    assert signals == []

