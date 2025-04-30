from blackjack import Strategy, Action, fitness_ev, legal_actions
from visualization import visualize_strategy

def main():
    base_table = {}
    # include total=2 so A,A is covered
    for total in range(2, 22):
        for upcard in range(1, 11):          # 1 = Ace through 10
            for soft in (False, True):
                for can_double in (False, True):
                    for can_split in (False, True):
                        # skip impossible split state
                        if can_split and not can_double:
                            continue
                        legal = legal_actions(can_double, can_split)
                        # baseline: stand on 17+, else hit
                        action = Action.S if total >= 17 else Action.H
                        if action not in legal:
                            action = Action.H
                        base_table[(total, upcard, soft, can_double, can_split)] = action

    strat = Strategy(table=base_table)

    # compute edge
    edge = fitness_ev(strat, 500_000)
    print(f"Baseline strategy edge ≈ {edge:.2%}")

    # visualize and save
    visualize_strategy(strat, filename="baseline_strategy.jpg")
    print("Saved visualization to baseline_strategy.jpg")

if __name__ == '__main__':
    main()
