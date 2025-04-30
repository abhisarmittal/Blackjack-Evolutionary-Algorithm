# blackjack.py

import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional

# ────────────────────────────────────────────────────────────────────────────────
# Types and Helpers
# ────────────────────────────────────────────────────────────────────────────────

StateKey = Tuple[int, int, bool, bool, bool]

class Action(Enum):
    H = auto()  # Hit
    S = auto()  # Stand
    D = auto()  # Double down
    P = auto()  # Split

def legal_actions(can_double: bool, can_split: bool) -> List[Action]:
    acts = [Action.H, Action.S]
    if can_double:
        acts.append(Action.D)
    if can_split:
        acts.append(Action.P)
    return acts

@dataclass
class Strategy:
    table: Dict[StateKey, Action] = field(default_factory=dict)

    def action_for(self,
                   total: int,
                   upcard: int,
                   soft: bool,
                   can_double: bool,
                   can_split: bool) -> Action:
        key = (total, upcard, soft, can_double, can_split)
        action = self.table[key]
        if action not in legal_actions(can_double, can_split):
            raise ValueError(f"Illegal action {action} for state {key}")
        return action


# ────────────────────────────────────────────────────────────────────────────────
# Card, Deck, and Hand (Six‑deck shoe)
# ────────────────────────────────────────────────────────────────────────────────

class Card:
    def __init__(self, rank: str):
        self.rank = rank
        if rank in ['J', 'Q', 'K']:
            self.value = 10
        elif rank == 'A':
            self.value = 1
        else:
            self.value = int(rank)

    def __repr__(self):
        return self.rank

class Deck:
    ranks = [str(n) for n in range(2, 11)] + ['J','Q','K','A']

    def __init__(self):
        # six 52‑card decks: 6 × 4 of each rank
        self.cards = [Card(r) for r in Deck.ranks] * 4 * 6
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            self.__init__()
        return self.cards.pop()

class Hand:
    def __init__(self, cards: List[Card] = None):
        self.cards = cards or []

    def add(self, card: Card):
        self.cards.append(card)

    def best_value(self) -> int:
        total = sum(c.value for c in self.cards)
        if any(c.rank == 'A' for c in self.cards) and total + 10 <= 21:
            return total + 10
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.best_value() == 21

    def is_soft(self) -> bool:
        tot = sum(c.value for c in self.cards)
        return any(c.rank == 'A' for c in self.cards) and tot + 10 <= 21

    def can_split(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def is_bust(self) -> bool:
        return self.best_value() > 21

    def __repr__(self):
        sf = 'S' if self.is_soft() else ''
        return f"{self.cards} ({self.best_value()}{sf})"


def play_dealer_hand(deck: Deck, upcard: Card, hole: Card) -> Hand:
    dealer = Hand([upcard, hole])
    while dealer.best_value() < 17:
        dealer.add(deck.draw())
    return dealer


# ────────────────────────────────────────────────────────────────────────────────
# Standard EV Simulation — six‑deck, reshuffle each hand
# ────────────────────────────────────────────────────────────────────────────────

def simulate_round_ev(strat: Strategy) -> List[Tuple[float, float]]:
    deck = Deck()
    results: List[Tuple[float, float]] = []

    # initial deal
    player_cards = [deck.draw(), deck.draw()]
    dealer_up, hole = deck.draw(), deck.draw()

    # dealer natural?
    if Hand([dealer_up, hole]).is_blackjack():
        if Hand(player_cards).is_blackjack():
            return [(1.0, 0.0)]
        else:
            return [(1.0, -1.0)]

    queue: List[Tuple[Hand, float, bool]] = [(Hand(player_cards), 1.0, True)]
    final_hands: List[Tuple[Hand, float, Optional[float]]] = []

    while queue:
        hand, bet, is_nat = queue.pop(0)

        if is_nat and hand.is_blackjack():
            final_hands.append((hand, bet, 1.5 * bet))
            continue

        total      = hand.best_value()
        soft       = hand.is_soft()
        can_double = (len(hand.cards) == 2)
        can_split  = hand.can_split() and can_double

        action = strat.action_for(total, dealer_up.value, soft, can_double, can_split)

        # split aces
        if action == Action.P and can_split and hand.cards[0].rank == 'A':
            c1, c2 = hand.cards
            final_hands.extend([
                (Hand([c1, deck.draw()]), bet, None),
                (Hand([c2, deck.draw()]), bet, None)
            ])
            continue

        # normal split
        if action == Action.P and can_split:
            c1, c2 = hand.cards
            queue.append((Hand([c1, deck.draw()]), bet, False))
            queue.append((Hand([c2, deck.draw()]), bet, False))
            continue

        # double
        if action == Action.D and can_double:
            hand.add(deck.draw())
            if hand.is_bust():
                final_hands.append((hand, bet * 2, -bet * 2))
            else:
                final_hands.append((hand, bet * 2, None))
            continue

        # hit
        if action == Action.H:
            hand.add(deck.draw())
            if hand.is_bust():
                final_hands.append((hand, bet, -bet))
            else:
                queue.insert(0, (hand, bet, False))
            continue

        # stand
        final_hands.append((hand, bet, None))

    # dealer plays
    dealer = play_dealer_hand(deck, dealer_up, hole)

    # settle
    results = []
    for hand, bet, profit in final_hands:
        if profit is not None:
            results.append((bet, profit))
        else:
            if dealer.is_bust():
                results.append((bet, bet))
            else:
                ph = hand.best_value()
                dh = dealer.best_value()
                if ph > dh:
                    results.append((bet, bet))
                elif ph < dh:
                    results.append((bet, -bet))
                else:
                    results.append((bet, 0.0))
    return results


def fitness_ev(strat: Strategy, n_rounds: int = 10000) -> float:
    total_bet, total_profit = 0.0, 0.0
    for _ in range(n_rounds):
        for bet, profit in simulate_round_ev(strat):
            total_bet    += bet
            total_profit += profit
    return total_profit / total_bet


# ────────────────────────────────────────────────────────────────────────────────
# Scenario‑based fitness — avoid duplicate r1,r2 permutations
# ────────────────────────────────────────────────────────────────────────────────

def simulate_state_ev(deck: Deck,
                      hand: Hand,
                      dealer_up: Card,
                      dealer_hole: Card,
                      strat: Strategy
                     ) -> List[Tuple[float, float]]:
    """
    Play out from fixed initial state, returning (bet, profit) pairs.
    """
    # dealer natural?
    if Hand([dealer_up, dealer_hole]).is_blackjack():
        if hand.is_blackjack():
            return [(1.0, 0.0)]
        else:
            return [(1.0, -1.0)]

    queue: List[Tuple[Hand, float, bool]] = [(hand, 1.0, True)]
    final_hands: List[Tuple[Hand, float, Optional[float]]] = []

    while queue:
        h, bet, is_nat = queue.pop(0)

        if is_nat and h.is_blackjack():
            final_hands.append((h, bet, 1.5 * bet))
            continue

        total      = h.best_value()
        soft       = h.is_soft()
        can_double = (len(h.cards) == 2)
        can_split  = h.can_split() and can_double

        action = strat.action_for(total,
                                  dealer_up.value,
                                  soft,
                                  can_double,
                                  can_split)

        # split aces
        if action == Action.P and can_split and h.cards[0].rank == 'A':
            c1, c2 = h.cards
            h1 = Hand([c1, deck.draw()])
            h2 = Hand([c2, deck.draw()])
            final_hands.extend([(h1, bet, None), (h2, bet, None)])
            continue

        # normal split
        if action == Action.P and can_split:
            c1, c2 = h.cards
            queue.append((Hand([c1, deck.draw()]), bet, False))
            queue.append((Hand([c2, deck.draw()]), bet, False))
            continue

        # double
        if action == Action.D and can_double:
            h.add(deck.draw())
            if h.is_bust():
                final_hands.append((h, bet * 2, -bet * 2))
            else:
                final_hands.append((h, bet * 2, None))
            continue

        # hit
        if action == Action.H:
            h.add(deck.draw())
            if h.is_bust():
                final_hands.append((h, bet, -bet))
            else:
                queue.insert(0, (h, bet, False))
            continue

        # stand
        final_hands.append((h, bet, None))

    # dealer plays and settle
    dealer = play_dealer_hand(deck, dealer_up, dealer_hole)
    results: List[Tuple[float, float]] = []
    for h, bet, profit in final_hands:
        if profit is not None:
            results.append((bet, profit))
        else:
            if dealer.is_bust():
                results.append((bet, bet))
            else:
                ph = h.best_value()
                dh = dealer.best_value()
                if ph > dh:
                    results.append((bet, bet))
                elif ph < dh:
                    results.append((bet, -bet))
                else:
                    results.append((bet, 0.0))
    return results


def fitness_ev_2(strat: Strategy,
                 n_per_state: int = 10
                ) -> float:
    """
    Scenario‑based: for each unordered pair (r1,r2) and each dealer upcard,
    simulate n_per_state hands from that fixed scenario. Returns edge.
    """
    total_bet, total_profit = 0.0, 0.0
    ranks = Deck.ranks

    # iterate unique unordered combos r1 <= r2 by index
    for i in range(len(ranks)):
        for j in range(i, len(ranks)):
            r1 = ranks[i]
            r2 = ranks[j]

            player_hand = Hand([Card(r1), Card(r2)])
            total = player_hand.best_value()
            soft  = player_hand.is_soft()
            can_split = (r1 == r2)
            can_double = True

            for up_rank in ranks:
                upcard = Card(up_rank)

                for _ in range(n_per_state):
                    # fresh shoe
                    deck = Deck()

                    # remove player's two cards
                    removed = 0
                    for cr in (r1, r2):
                        for k, dc in enumerate(deck.cards):
                            if dc.rank == cr:
                                deck.cards.pop(k)
                                removed += 1
                                break
                    if removed != 2:
                        raise ValueError(f"Failed to remove player cards {r1},{r2}")

                    # remove dealer upcard
                    removed = False
                    for k, dc in enumerate(deck.cards):
                        if dc.rank == up_rank:
                            deck.cards.pop(k)
                            removed = True
                            break
                    if not removed:
                        raise ValueError(f"Failed to remove upcard {up_rank}")

                    # draw hole
                    hole = deck.draw()

                    # simulate from this fixed state
                    for bet, profit in simulate_state_ev(
                        deck,
                        Hand([Card(r1), Card(r2)]),
                        upcard,
                        hole,
                        strat
                    ):
                        total_bet    += bet
                        total_profit += profit

    return total_profit / total_bet
