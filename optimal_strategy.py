from blackjack import Strategy, Action, fitness_ev, legal_actions
from visualization import visualize_strategy

def compute_optimal_action(
    total: int,
    upcard: int,
    soft: bool,
    can_double: bool,
    can_split: bool
) -> Action:
    """
    Single‑deck basic strategy, dealer stands on soft 17.
    """
    # 1) Pair splits
    if can_split:
        if soft:
            # A,A
            return Action.P
        rank = total // 2

        if rank == 10:
            # 10,10
            return Action.S

        if rank == 9:
            # 9,9
            if upcard in (2, 3, 4, 5, 6, 8, 9):
                return Action.P
            else:
                return Action.S

        if rank == 8:
            return Action.P

        if rank == 7:
            if 2 <= upcard <= 7:
                return Action.P
            else:
                return Action.H

        if rank == 6:
            if 2 <= upcard <= 6:
                return Action.P
            else:
                return Action.H

        if rank == 5:
            # treat as hard 10
            if can_double and 2 <= upcard <= 9:
                return Action.D
            else:
                return Action.H

        if rank == 4:
            if upcard in (5, 6):
                return Action.P
            else:
                return Action.H

        if rank in (2, 3):
            if 2 <= upcard <= 7:
                return Action.P
            else:
                return Action.H

    # 2) Soft hands (A + x)
    if soft:
        # soft 20+ and soft 19
        if total >= 19:
            return Action.S

        # A,7 (soft 18)
        if total == 18:
            if upcard in (3, 4, 5, 6):
                return Action.D if can_double else Action.S

            if upcard in (2, 7, 8):
                return Action.S

            return Action.H

        # A,6 (soft 17)
        if total == 17:
            if upcard in (3, 4, 5, 6):
                return Action.D if can_double else Action.H

            return Action.H

        # A,5 or A,4 (soft 16 or 15)
        if total in (15, 16):
            if upcard in (4, 5, 6):
                return Action.D if can_double else Action.H

            return Action.H

        # A,3 or A,2 (soft 14 or 13)
        if total in (13, 14):
            if upcard in (5, 6):
                return Action.D if can_double else Action.H

            return Action.H

        # anything lower
        return Action.H

    # 3) Hard hands
    if total >= 17:
        return Action.S

    if 13 <= total <= 16:
        if 2 <= upcard <= 6:
            return Action.S
        else:
            return Action.H

    if total == 12:
        if upcard in (4, 5, 6):
            return Action.S
        else:
            return Action.H

    if total == 11:
        return Action.D if can_double else Action.H

    if total == 10:
        if can_double and 2 <= upcard <= 9:
            return Action.D
        else:
            return Action.H

    if total == 9:
        if can_double and 3 <= upcard <= 6:
            return Action.D
        else:
            return Action.H

    # hard 8 or less
    return Action.H

def build_optimal_strategy() -> Strategy:
    table: dict = {}

    for total in range(2, 22):   # include total=2 for A,A
        for upcard in range(1, 11):
            for soft in (False, True):
                for can_double in (False, True):
                    for can_split in (False, True):
                        # only allow split on first two cards
                        if can_split and not can_double:
                            continue

                        action = compute_optimal_action(
                            total,
                            upcard,
                            soft,
                            can_double,
                            can_split
                        )

                        # enforce legality
                        if action not in legal_actions(
                            can_double, can_split
                        ):
                            action = Action.H

                        table[
                            (total, upcard, soft, can_double, can_split)
                        ] = action

    return Strategy(table=table)

def main():
    opt = build_optimal_strategy()

    # simulate edge over 500,000 hands
    edge = fitness_ev(opt, 500_000)
    print(f"Optimal strategy edge ≈ {edge:.2%}")

    visualize_strategy(
        opt,
        filename="optimal_strategy.jpg"
    )
    print("Saved visualization to optimal_strategy.jpg")

if __name__ == '__main__':
    main()
