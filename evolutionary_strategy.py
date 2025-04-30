import os
import random
from typing import List, Dict, Tuple

import matplotlib.pyplot as plt

from blackjack import Strategy, Action, fitness_ev_2, legal_actions
from visualization import visualize_strategy

# ────────────────────────────────────────────────────────────────────────────────
# Hyperparameters
# ────────────────────────────────────────────────────────────────────────────────

POPULATION_SIZE  = 300       # number of strategies per generation
N_GENERATIONS    = 100      # total generations to run
# FITNESS_ROUNDS   = 10000    # hands per fitness evaluation
FITNESS_N_PER_ROUND = 30  # hands per fitness evaluation 2

MUTATION_RATE    = 0      # probability that a child is mutated
MUTATION_IMPACT  = 0.1     # fraction of strategy cells to change on mutation

TOURNAMENT_SIZE  = 5        # competitors in tournament selection
ELITE_COUNT      = 0        # number of top strategies carried over

# ────────────────────────────────────────────────────────────────────────────────
# Genetic operators
# ────────────────────────────────────────────────────────────────────────────────

def random_strategy() -> Strategy:
    table: Dict[Tuple[int,int,bool,bool,bool], Action] = {}
    for total in range(2, 22):
        for upcard in range(1, 11):
            for soft in (False, True):
                for can_double in (False, True):
                    for can_split in (False, True):
                        if can_split and not can_double:
                            continue
                        legal = legal_actions(can_double, can_split)
                        table[(total, upcard, soft, can_double, can_split)] = random.choice(legal)
    return Strategy(table=table)

def tournament_selection(pop: List[Strategy], edges: List[float]) -> Strategy:
    competitors = random.sample(list(zip(pop, edges)), TOURNAMENT_SIZE)
    return max(competitors, key=lambda x: x[1])[0]

def uniform_crossover(p1: Strategy, p2: Strategy) -> Strategy:
    child_table: Dict[Tuple[int,int,bool,bool,bool], Action] = {}
    for key in p1.table:
        child_table[key] = p1.table[key] if random.random() < 0.5 else p2.table[key]
    return Strategy(table=child_table)

def apply_mutation(strategy: Strategy):
    total_cells = len(strategy.table)
    n_mutations = max(1, int(MUTATION_IMPACT * total_cells))
    keys = random.sample(list(strategy.table.keys()), n_mutations)
    for key in keys:
        can_double = key[3]
        can_split  = key[4]
        legal      = legal_actions(can_double, can_split)
        current    = strategy.table[key]
        choices    = [a for a in legal if a != current]
        strategy.table[key] = random.choice(choices)

# ────────────────────────────────────────────────────────────────────────────────
# Main evolutionary loop with elitism + edge history plotting
# ────────────────────────────────────────────────────────────────────────────────

def main():
    outdir = "gen_strategies"
    os.makedirs(outdir, exist_ok=True)

    # initialize population
    population = [random_strategy() for _ in range(POPULATION_SIZE)]

    # history lists for plotting
    best_edges: List[float] = []
    avg_edges:  List[float] = []

    for gen in range(1, N_GENERATIONS + 1):
        # evaluate edge
        edges = [fitness_ev_2(s, FITNESS_N_PER_ROUND) for s in population]

        # record history
        best_edge = max(edges)
        avg_edge  = sum(edges) / len(edges)
        best_edges.append(best_edge)
        avg_edges.append(avg_edge)

        # select elites
        sorted_idxs = sorted(range(len(population)),
                             key=lambda i: edges[i],
                             reverse=True)
        elites = [population[i] for i in sorted_idxs[:ELITE_COUNT]]

        print(f"Generation {gen}: Best edge = {best_edge:.2%}, Avg = {avg_edge:.2%}")

        # save best strategy visualization
        best_strat = population[sorted_idxs[0]]
        fname = os.path.join(outdir, f"s{gen}.jpg")
        visualize_strategy(best_strat, filename=fname)
        print(f"  → saved best strategy to {fname}")

        # build next generation
        new_population = elites.copy()
        while len(new_population) < POPULATION_SIZE:
            p1 = tournament_selection(population, edges)
            p2 = tournament_selection(population, edges)
            child = uniform_crossover(p1, p2)
            if random.random() < MUTATION_RATE:
                apply_mutation(child)
            new_population.append(child)
        population = new_population

    # final summary
    final_edges = [fitness_ev_2(s, FITNESS_N_PER_ROUND) for s in population]
    final_best  = max(final_edges)
    print(f"Final best edge ≈ {final_best:.2%}")

    # ─────────────────────────────────────────────────────────────────────────────
    # Plot evolution of edges
    # ─────────────────────────────────────────────────────────────────────────────
    gens = list(range(1, N_GENERATIONS + 1))

    plt.figure()
    plt.plot(gens, best_edges,    label="Best Edge")
    plt.plot(gens, avg_edges,     label="Average Edge")
    plt.xlabel("Generation")
    plt.ylabel("Edge")
    plt.title("Evolution of Strategy Edge Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plot_path = os.path.join(outdir, "edge_evolution.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved edge evolution plot to {plot_path}")

if __name__ == "__main__":
    main()
