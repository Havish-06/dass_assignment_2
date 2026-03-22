"""Game engine for the Monopoly implementation.
Handles gameplay flow, trading, turns, and board interaction."""


from moneypoly.config import (
    JAIL_FINE,
    AUCTION_MIN_INCREMENT,
    INCOME_TAX_AMOUNT,
    LUXURY_TAX_AMOUNT,
    MAX_TURNS,
    GO_SALARY,
)
from moneypoly.player import Player
from moneypoly.board import Board
from moneypoly.bank import Bank
from moneypoly.dice import Dice
from moneypoly.cards import CardDeck, CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from moneypoly import ui


CHANCE_DECK = CardDeck(CHANCE_CARDS)
COMMUNITY_DECK = CardDeck(COMMUNITY_CHEST_CARDS)


def _card_collect(game, player, value):
    """Handle a card where the bank pays the player."""
    amount = game.bank.pay_out(value)
    player.add_money(amount)


def _card_pay(game, player, value):
    """Handle a card where the player pays the bank."""
    player.deduct_money(value)
    game.bank.collect(value)


def _card_jail(game, player, value):  # pylint: disable=unused-argument
    """Send the player directly to jail."""
    player.go_to_jail()
    print(f"  {player.name} has been sent to Jail!")


def _card_jail_free(game, player, value):  # pylint: disable=unused-argument
    """Give the player a Get Out of Jail Free card."""
    player.jail.cards += 1
    print(f"  {player.name} now holds a Get Out of Jail Free card.")


def _card_move_to(game, player, value):
    """Move the player to a board position, handling Go and property landing."""
    old_pos = player.position
    player.position = value
    if value < old_pos:
        player.add_money(GO_SALARY)
        print(f"  {player.name} passed Go and collected ${GO_SALARY}.")
    tile = game.board.get_tile_type(value)
    if tile == "property":
        prop = game.board.get_property_at(value)
        if prop:
            game.handle_property_tile(player, prop)


def _card_birthday(game, player, value):
    """Collect a fixed amount from every other player who can afford it.

    Players who do not have more than ``value`` in cash are skipped so that
    the birthday card itself never causes bankruptcy.
    """
    for other in list(game.players):
        if other is player:
            continue
        # Only take money from players who strictly have more than the gift
        # amount; this prevents their balance from reaching zero via birthday.
        if other.balance > value:
            other.deduct_money(value)
            player.add_money(value)
            game.check_bankruptcy(other)


def _card_collect_from_all(game, player, value):
    """Collect a fixed amount from all other players, even if they go broke.

    Unlike the birthday card, this action will attempt to take the money from
    every other player regardless of their current balance, so it can cause
    bankruptcy.
    """
    for other in list(game.players):
        if other is player:
            continue
        other.deduct_money(value)
        player.add_money(value)
        game.check_bankruptcy(other)


_ACTION_HANDLERS = {
    "collect": _card_collect,
    "pay": _card_pay,
    "jail": _card_jail,
    "jail_free": _card_jail_free,
    "move_to": _card_move_to,
    "birthday": _card_birthday,
    "collect_from_all": _card_collect_from_all,
}


def apply_card(game, player, card):
    """Apply the effect of a drawn Chance or Community Chest card."""
    if card is None:
        return

    print(f"  Card drawn: \"{card['description']}\"")
    action = card["action"]
    value = card["value"]

    handler = _ACTION_HANDLERS.get(action)
    if handler is None:
        print(f"  Warning: Unknown card action '{action}'")
        return
    handler(game, player, value)
class Game:
    """Manages the full state and flow of a MoneyPoly game session."""

    def __init__(self, player_names):
        self.board = Board()
        self.bank = Bank()
        self.dice = Dice()
        self.players = [Player(name) for name in player_names]
        self.current_index = 0
        self.turn_number = 0

    def current_player(self):
        """Return the Player whose turn it currently is."""
        return self.players[self.current_index]

    def advance_turn(self):
        """Move to the next player in the rotation."""
        self.current_index = (self.current_index + 1) % len(self.players)
        self.turn_number += 1

    def interactive_menu(self):
        """Offer the current player a pre-roll menu (mortgage, trade, etc.)."""
        while True:
            print("\n  Pre-roll options:")
            print("    1. View standings")
            print("    2. View board ownership")
            print("    3. Mortgage a property")
            print("    4. Unmortgage a property")
            print("    5. Trade with another player")
            print("    6. Request emergency loan")
            print("    0. Roll dice")
            choice = ui.safe_int_input("  Choice: ", default=0)

            if choice == 0:
                break
            if choice == 1:
                ui.print_standings(self.players)
            elif choice == 2:
                ui.print_board_ownership(self.board)
            elif choice == 3:
                self._menu_mortgage(self.current_player())
            elif choice == 4:
                self._menu_unmortgage(self.current_player())
            elif choice == 5:
                self._menu_trade(self.current_player())
            elif choice == 6:
                amount = ui.safe_int_input("  Loan amount: ", default=0)
                if amount > 0:
                    self.bank.give_loan(self.current_player(), amount)

    def mortgage_property(self, player, prop):
        """Mortgage `prop` owned by `player` and credit them the payout."""
        if prop.owner != player:
            print(f"  {player.name} does not own {prop.name}.")
            return False
        payout = prop.mortgage()
        if payout == 0:
            print(f"  {prop.name} is already mortgaged.")
            return False
        player.add_money(payout)
        self.bank.collect(-payout)
        print(f"  {player.name} mortgaged {prop.name} and received ${payout}.")
        return True

    def unmortgage_property(self, player, prop):
        """Lift the mortgage on `prop`, charging the player the redemption cost."""
        if prop.owner != player:
            print(f"  {player.name} does not own {prop.name}.")
            return False
        if not prop.is_mortgaged:
            print(f"  {prop.name} is not mortgaged.")
            return False

        cost = int(prop.mortgage_value * 1.1)
        if player.balance < cost:
            print(f"  {player.name} cannot afford to unmortgage {prop.name} (${cost}).")
            return False

        player.deduct_money(cost)
        self.bank.collect(cost)
        prop.is_mortgaged = False
        print(f"  {player.name} unmortgaged {prop.name} for ${cost}.")
        return True

    def _menu_mortgage(self, player):
        """Interactively select a property to mortgage."""
        mortgageable = [p for p in player.properties if not p.is_mortgaged]
        if not mortgageable:
            print("  No properties available to mortgage.")
            return
        for i, prop in enumerate(mortgageable):
            print(f"  {i + 1}. {prop.name}  (value: ${prop.mortgage_value})")
        idx = ui.safe_int_input("  Select: ", default=0) - 1
        if 0 <= idx < len(mortgageable):
            self.mortgage_property(player, mortgageable[idx])

    def _menu_unmortgage(self, player):
        """Interactively select a mortgaged property to redeem."""
        mortgaged = [p for p in player.properties if p.is_mortgaged]
        if not mortgaged:
            print("  No mortgaged properties to redeem.")
            return
        for i, prop in enumerate(mortgaged):
            cost = int(prop.mortgage_value * 1.1)
            print(f"  {i + 1}. {prop.name}  (cost to redeem: ${cost})")
        idx = ui.safe_int_input("  Select: ", default=0) - 1
        if 0 <= idx < len(mortgaged):
            self.unmortgage_property(player, mortgaged[idx])

    def _menu_trade(self, player):
        """Interactively set up a trade between the current player and another."""
        others = [p for p in self.players if p != player]
        if not others:
            print("  No other players to trade with.")
            return
        for i, p in enumerate(others):
            print(f"  {i + 1}. {p.name}  (${p.balance})")
        idx = ui.safe_int_input("  Trade with: ", default=0) - 1
        if not 0 <= idx < len(others):
            return
        partner = others[idx]
        if not player.properties:
            print(f"  {player.name} has no properties to trade.")
            return
        for i, prop in enumerate(player.properties):
            print(f"  {i + 1}. {prop.name}")
        pidx = ui.safe_int_input("  Property to offer: ", default=0) - 1
        if not 0 <= pidx < len(player.properties):
            return
        chosen_prop = player.properties[pidx]
        cash = ui.safe_int_input(
            f"  Cash to receive from {partner.name}: $", default=0
        )
        self.trade(player, partner, chosen_prop, cash)

    def play_turn(self):
        """Execute one complete turn for the current player."""
        player = self.current_player()
        ui.print_banner(
            f"Turn {self.turn_number + 1}  |  {player.name}  |  ${player.balance}"
        )

        # Allow the current player to use the pre-roll interactive menu
        # self.interactive_menu()

        if player.jail.in_jail:
            self._handle_jail_turn(player)
            self.advance_turn()
            return

        roll = self.dice.roll()
        print(f"  {player.name} rolled: {self.dice.describe()}")

        # Three consecutive doubles sends a player to jail
        if self.dice.doubles_streak >= 3:
            print(f"  {player.name} rolled doubles three times in a row — go to jail!")
            player.go_to_jail()
            self.advance_turn()
            return

        self._move_and_resolve(player, roll)

        # Rolling doubles earns an extra turn
        if self.dice.is_doubles():
            print(f"  Doubles! {player.name} rolls again.")
            return

        self.advance_turn()

    def _move_and_resolve(self, player, steps):
        """Move `player` by `steps` and trigger whatever tile they land on."""
        player.move(steps)
        position = player.position
        tile = self.board.get_tile_type(position)
        print(f"  {player.name} moved to position {position}  [{tile}]")

        if tile == "go_to_jail":
            player.go_to_jail()
            print(f"  {player.name} has been sent to Jail!")

        elif tile == "income_tax":
            player.deduct_money(INCOME_TAX_AMOUNT)
            self.bank.collect(INCOME_TAX_AMOUNT)
            print(f"  {player.name} paid income tax: ${INCOME_TAX_AMOUNT}.")

        elif tile == "luxury_tax":
            player.deduct_money(LUXURY_TAX_AMOUNT)
            self.bank.collect(LUXURY_TAX_AMOUNT)
            print(f"  {player.name} paid luxury tax: ${LUXURY_TAX_AMOUNT}.")

        elif tile == "free_parking":
            print(f"  {player.name} rests on Free Parking. Nothing happens.")

        elif tile == "chance":
            card = CHANCE_DECK.draw()
            apply_card(self, player, card)

        elif tile == "community_chest":
            card = COMMUNITY_DECK.draw()
            apply_card(self, player, card)

        elif tile == "railroad": #seems redundant
            prop = self.board.get_property_at(position)
            if prop is not None:
                self.handle_property_tile(player, prop)

        elif tile == "property":
            prop = self.board.get_property_at(position)
            if prop is not None:
                self.handle_property_tile(player, prop)

        self._check_bankruptcy(player)


    def handle_property_tile(self, player, prop):
        """Decide what to do when `player` lands on a property tile."""
        if prop.owner is None:
            print(f"  {prop.name} is unowned — asking price ${prop.price}.")
            choice = input("  Buy (b), Auction (a), or Skip (s)? ").strip().lower()
            if choice == "b":
                self.buy_property(player, prop)
            elif choice == "a":
                self.auction_property(prop)
            else:
                print(f"  {player.name} passes on {prop.name}.")
        elif prop.owner == player:
            print(f"  {player.name} owns {prop.name}. No rent due.")
        else:
            self.pay_rent(player, prop)

    def buy_property(self, player, prop):
        """
        Purchase `prop` on behalf of `player`.
        Returns True on success, False if the player cannot afford it.
        """
        if player.balance < prop.price:
            print(f"  {player.name} cannot afford {prop.name} (${prop.price}).")
            return False
        player.deduct_money(prop.price)
        prop.owner = player
        player.add_property(prop)
        self.bank.collect(prop.price)
        print(f"  {player.name} purchased {prop.name} for ${prop.price}.")
        return True

    def pay_rent(self, player, prop):
        """
        Charge `player` the current rent on `prop` and transfer it to the owner.
        """
        if prop.is_mortgaged:
            print(f"  {prop.name} is mortgaged — no rent collected.")
            return
        if prop.owner is None:
            return

        rent = prop.get_rent()
        player.deduct_money(rent)
        print(f"  {player.name} paid ${rent} rent on {prop.name} to {prop.owner.name}.")


    def trade(self, seller, buyer, prop, cash_amount):
        """
        Execute a property trade: `seller` transfers `prop` to `buyer`
        in exchange for `cash_amount` from `buyer`.
        Returns True on success.
        """
        if prop.owner != seller:
            print(f"  Trade failed: {seller.name} does not own {prop.name}.")
            return False
        if buyer.balance < cash_amount:
            print(f"  Trade failed: {buyer.name} cannot afford ${cash_amount}.")
            return False

        buyer.deduct_money(cash_amount)
        prop.owner = buyer
        seller.remove_property(prop)
        buyer.add_property(prop)
        print(
            f"  Trade complete: {seller.name} sold {prop.name} "
            f"to {buyer.name} for ${cash_amount}."
        )
        return True

    def auction_property(self, prop):
        """Run an open auction for `prop` among all active players."""
        print(f"\n  [Auction] Bidding on {prop.name} (listed at ${prop.price})")
        highest_bid = 0
        highest_bidder = None

        for player in self.players:
            print(f"  {player.name}'s bid (balance: ${player.balance}, "
                  f"current high: ${highest_bid}):")
            bid = ui.safe_int_input("  Enter amount (0 to pass): ", default=0)
            if bid <= 0:
                print(f"  {player.name} passes.")
                continue
            min_required = highest_bid + AUCTION_MIN_INCREMENT
            if bid < min_required:
                print(f"  Bid too low — minimum raise is ${AUCTION_MIN_INCREMENT}.")
                continue
            if bid > player.balance:
                print(f"  {player.name} cannot afford ${bid}.")
                continue
            highest_bid = bid
            highest_bidder = player
            print(f"  {player.name} bids ${bid}.")

        if highest_bidder is not None:
            highest_bidder.deduct_money(highest_bid)
            prop.owner = highest_bidder
            highest_bidder.add_property(prop)
            self.bank.collect(highest_bid)
            print(
                f"  {highest_bidder.name} won {prop.name} "
                f"at auction for ${highest_bid}."
            )
        else:
            print(f"  No bids placed. {prop.name} remains unowned.")

    def _handle_jail_turn(self, player):
        """Process a jailed player's turn — offer to pay fine or use card."""
        print(f"  {player.name} is in jail (turn {player.jail.turns + 1}/3).")

        # Use a Get Out of Jail Free card if available
        if player.jail.cards > 0:
            if ui.confirm("  Use your Get Out of Jail Free card? (y/n): "):
                player.jail.cards -= 1
                player.jail.release()
                print(f"  {player.name} used a Get Out of Jail Free card!")
                roll = self.dice.roll()
                print(f"  {player.name} rolled: {self.dice.describe()}")
                self._move_and_resolve(player, roll)
                return

        # Offer to pay the fine voluntarily
        if ui.confirm(f"  Pay ${JAIL_FINE} fine to leave jail? (y/n): "):
            player.deduct_money(JAIL_FINE)
            self.bank.collect(JAIL_FINE)
            # Paying the fine can itself cause bankruptcy; eliminate the
            # player immediately rather than letting them move.
            self.check_bankruptcy(player)
            if player not in self.players:
                return
            player.jail.release()
            print(f"  {player.name} paid the ${JAIL_FINE} fine and is released.")
            roll = self.dice.roll()
            print(f"  {player.name} rolled: {self.dice.describe()}")
            self._move_and_resolve(player, roll)
            return

        # No action
        # Serve the turn
        player.jail.turns += 1
        if player.jail.turns >= 3:
            # Mandatory release after 3 turns
            print(f"  {player.name} must leave jail. Paying mandatory ${JAIL_FINE} fine.")
            player.deduct_money(JAIL_FINE)
            self.bank.collect(JAIL_FINE)
            self.check_bankruptcy(player)
            if player not in self.players:
                return
            player.jail.release()
            roll = self.dice.roll()
            print(f"  {player.name} rolled: {self.dice.describe()}")
            self._move_and_resolve(player, roll)
            return

    def _check_bankruptcy(self, player):
        """Eliminate `player` from the game if they are bankrupt."""
        if player.is_bankrupt():
            print(f"\n  *** {player.name} is bankrupt and has been eliminated! ***")
            player.is_eliminated = True
            # Release all properties back to the bank
            for prop in list(player.properties):
                prop.owner = None
                prop.is_mortgaged = False
            player.properties.clear()
            if player in self.players:
                self.players.remove(player)
            if self.current_index >= len(self.players):
                self.current_index = 0

    def check_bankruptcy(self, player):
        """Public wrapper to check and eliminate a player if bankrupt.

        This is used from helper functions such as card actions to avoid
        accessing the internal implementation detail directly.
        """
        self._check_bankruptcy(player)

    def find_winner(self):
        """Return the player with the highest net worth."""
        if not self.players:
            return None
        # Winner is the player with the highest net worth.
        return max(self.players, key=lambda p: p.net_worth())

    def run(self):
        """Run the game loop until only one player remains or turns run out."""
        ui.print_banner("Welcome to MoneyPoly!")
        print()
        for p in self.players:
            print(f"  {p.name} starts with ${p.balance}.")

        while  self.turn_number < MAX_TURNS:
            if len(self.players) <= 1:
                break
            self.play_turn()
            ui.print_standings(self.players)
            print()

        winner = self.find_winner()
        if winner:
            ui.print_banner("GAME OVER")
            print(f"\n  {winner.name} wins with a net worth of ${winner.net_worth()}!\n")
        else:
            print("\n  The game ended with no players remaining.")
