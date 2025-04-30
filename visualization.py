import matplotlib.pyplot as plt
from blackjack import Action


def visualize_strategy(strategy, filename="strategy.jpg", caption=True):
    """
    Render a blackjack Strategy as a colored table and save to `filename`.
    Rows: Hard 5–17, Soft A,2–A,9, Pairs 2–2–A–A.
    Columns: dealer upcard 2–10, Ace.

    Args:
        strategy: Strategy object
        filename: output image file path
        caption: whether to draw legend caption
    """
    # 1) Columns
    upcards = list(range(2, 11)) + [1]    # 1 = Ace, shown last
    col_labels = [str(x) for x in range(2, 11)] + ["A"]

    # 2) Rows definitions
    hard_totals = list(range(5, 18))       # 5 through 17
    soft_totals = list(range(13, 21))      # soft 13 (A,2) through 20 (A,9)
    pair_ranks  = [2,3,4,5,6,7,8,9,10,1]    # 1 = Ace

    row_keys    = []  # list of (total, soft, can_split)
    row_labels  = []

    # Hard rows (no splits, no soft)
    for tot in hard_totals:
        label = str(tot)
        row_labels.append(label)
        row_keys.append((tot, False, False))

    # Soft rows (soft=True, no split)
    for tot in soft_totals:
        other = tot - 11
        label = f"A,{other}"
        row_labels.append(label)
        row_keys.append((tot, True, False))

    # Pair rows (can_split=True)
    for r in pair_ranks:
        if r == 1:
            label = "A,A"
            tot   = 2
            soft  = True
        else:
            label = f"{r},{r}"
            tot   = r * 2
            soft  = False
        row_labels.append(label)
        row_keys.append((tot, soft, True))

    # 3) Color mapping
    color_map = {
        Action.H: "#66FF66",  # Hit = light green
        Action.S: "#FF6666",  # Stand = light red
        Action.D: "#6666FF",  # Double = light blue
        Action.P: "#CCCCCC",  # Split = light gray
    }

    # 4) Build table data
    cell_text   = []
    cell_colors = []
    for (tot, soft, can_split) in row_keys:
        texts = []
        colors= []
        for up in upcards:
            # initial‐hand state: can_double=True
            key = (tot, up, soft, True, can_split)
            act = strategy.table[key]
            texts.append(act.name)
            colors.append(color_map[act])
        cell_text.append(texts)
        cell_colors.append(colors)

    # 5) Plot Table
    fig, ax = plt.subplots(figsize=(8, len(row_keys)*0.3))
    ax.axis("off")
    tbl = ax.table(
        cellText   = cell_text,
        cellColours= cell_colors,
        rowLabels  = row_labels,
        colLabels  = col_labels,
        cellLoc    = "center",
        loc        = "center"
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.2)
    plt.tight_layout()

    # 6) Caption
    if caption:
        fig.text(
            0.5, 0.02,
            "H = Hit (green), S = Stand (red), D = Double (blue), P = Split (gray)",
            ha="center", fontsize=8
        )

    # 7) Save and close
    plt.savefig(filename, dpi=150)
    plt.close()


def plot_evolution(win_rates, filename="evolution.png"):
    """
    Plot win rates over generations and save to `filename`.

    Args:
        win_rates: list of floats (win percentages)
        filename: output image file path
    """
    generations = list(range(1, len(win_rates) + 1))
    plt.figure(figsize=(10, 4))
    # Line plot with markers
    plt.plot(generations, win_rates, marker='o', linewidth=2)
    # Title and labels
    plt.title("Evolution of Strategy Win Rate over Generations", fontsize=14, fontweight='bold')
    plt.xlabel("Generation", fontsize=12)
    plt.ylabel("Win Rate", fontsize=12)
    # Grid and aesthetics
    plt.grid(True, linestyle='--', alpha=0.6)
    # Tight layout
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
