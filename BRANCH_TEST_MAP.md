# Branch-to-Test Mapping

This document maps important `if`/`elif`/`else` branches in the MoneyPoly codebase to the unit tests that exercise them. It is organized by module and function.

---

## moneypoly.game

### `apply_card` and card handlers

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `card is None` returns immediately | `test_empty_deck_draw_and_peek` (draw returns `None`, then `apply_card` effectively no-ops via callers) in `tests/test_dice_and_cards.py` |
| Unknown `action` prints a warning and returns without effect | `test_apply_card_unknown_action_warns_and_does_nothing` in `tests/test_game_ui_main.py` |
| `"collect"` card: bank pays player | `test_collect_card_pays_from_bank_to_player` in `tests/test_bankruptcy_cards.py` |
| `"pay"` card: player pays bank | `test_pay_card_charges_player_and_credits_bank` in `tests/test_bankruptcy_cards.py` |
| `"jail"` card: send player directly to jail | `test_jail_card_sends_player_directly_to_jail` in `tests/test_bankruptcy_cards.py` |
| `"jail_free"` card: increment jail card count | `test_jail_free_card_increases_jail_card_count` in `tests/test_bankruptcy_cards.py` |
| `"move_to"` card moves player and pays GO salary when passing Go | `test_move_to_card_moves_player_and_awards_go_salary_when_passing` in `tests/test_bankruptcy_cards.py` |
| `"move_to"` card landing on property calls `handle_property_tile` | `test_move_to_card_calls_handle_property_tile_when_landing_on_property` in `tests/test_bankruptcy_cards.py` |
| `"birthday"` card skips players who cannot afford the gift and never bankrupts them | `test_birthday_skips_players_who_cannot_afford_gift` in `tests/test_bankruptcy_cards.py` |
| `"collect_from_all"` charges all players and can bankrupt them | `test_collect_from_all_can_bankrupt_and_eliminate_other_players` in `tests/test_bankruptcy_cards.py` |

---

### `interactive_menu`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Choice `0`: exit menu loop | `test_interactive_menu_standings_and_exit` in `tests/test_game_ui_main.py` |
| Choice `1`: call `ui.print_standings` | `test_interactive_menu_standings_and_exit` in `tests/test_game_ui_main.py` |
| Choice `2`: call `ui.print_board_ownership` | `test_interactive_menu_board_and_mortgage_unmortgage_trade_loan` in `tests/test_game_ui_main.py` |
| Choice `3`: call `_menu_mortgage` | `test_interactive_menu_board_and_mortgage_unmortgage_trade_loan` in `tests/test_game_ui_main.py` |
| Choice `4`: call `_menu_unmortgage` | `test_interactive_menu_board_and_mortgage_unmortgage_trade_loan` in `tests/test_game_ui_main.py` |
| Choice `5`: call `_menu_trade` | `test_interactive_menu_board_and_mortgage_unmortgage_trade_loan` in `tests/test_game_ui_main.py` |
| Choice `6`: request loan and call `bank.give_loan` when amount > 0 | `test_interactive_menu_board_and_mortgage_unmortgage_trade_loan` in `tests/test_game_ui_main.py` |

---

### `mortgage_property` / `unmortgage_property`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `mortgage_property`: player does not own property → fail | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `mortgage_property`: property already mortgaged → fail | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `mortgage_property`: success when owned and not mortgaged | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `unmortgage_property`: player does not own property → fail | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `unmortgage_property`: property not mortgaged → fail | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `unmortgage_property`: player cannot afford cost → fail | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |
| `unmortgage_property`: success when owned, mortgaged, and affordable | `test_mortgage_and_unmortgage_property_paths` in `tests/test_game_ui_main.py` |

---

### `_menu_mortgage`, `_menu_unmortgage`, `_menu_trade`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `_menu_mortgage`: no mortgageable properties → return | `test_mortgage_and_unmortgage_property_paths` indirectly (setup and menu calls) in `tests/test_game_ui_main.py` |
| `_menu_mortgage`: valid index selects property and calls `mortgage_property` | `test_menu_mortgage_and_unmortgage_and_trade` in `tests/test_game_ui_main.py` |
| `_menu_unmortgage`: no mortgaged properties → return | `test_mortgage_and_unmortgage_property_paths` indirectly in `tests/test_game_ui_main.py` |
| `_menu_unmortgage`: valid index selects property and calls `unmortgage_property` | `test_menu_mortgage_and_unmortgage_and_trade` in `tests/test_game_ui_main.py` |
| `_menu_trade`: no other players → prints and returns without calling `trade` | `test_menu_trade_returns_when_no_other_players` in `tests/test_game_ui_main.py` |
| `_menu_trade`: invalid partner selection index → return without calling `trade` | `test_menu_trade_returns_on_invalid_partner_selection` in `tests/test_game_ui_main.py` |
| `_menu_trade`: player has no properties → prints and returns | `test_menu_trade_returns_when_player_has_no_properties` in `tests/test_game_ui_main.py` |
| `_menu_trade`: invalid property index → return without calling `trade` | `test_menu_trade_returns_on_invalid_property_selection` in `tests/test_game_ui_main.py` |
| `_menu_trade`: happy-path trade (valid partner, property, and cash) calls `trade` once | `test_menu_mortgage_and_unmortgage_and_trade` in `tests/test_game_ui_main.py` |

---

### `play_turn`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Player starts in jail: calls `_handle_jail_turn` and `advance_turn`, then returns | `test_play_turn_calls_jail_handler_for_jailed_player` in `tests/test_game_ui_main.py` |
| Dice `doubles_streak >= 3`: send player to jail and advance turn | `test_play_turn_triple_doubles_sends_to_jail` in `tests/test_game_ui_main.py` |
| Non-triple, non-doubles roll: call `_move_and_resolve`, then `advance_turn` | `test_play_turn_moves_player_and_advances_turn_for_non_doubles` in `tests/test_game_ui_main.py` |
| Doubles (but not triple): call `_move_and_resolve` and **do not** advance turn | `test_play_turn_doubles_gives_extra_turn_without_advancing_player` in `tests/test_game_ui_main.py` |

---

### `_move_and_resolve`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Tile `"go_to_jail"`: send player to jail | `test_go_to_jail_tile_sends_player_to_jail` in `tests/test_taxes_and_rent.py` |
| Tile `"income_tax"`: deduct tax (up to balance), bank collects same, may bankrupt | `test_income_tax_reduces_balance_but_not_eliminate_when_affordable` and `test_income_tax_can_bankrupt_and_eliminate_player` in `tests/test_taxes_and_rent.py` |
| Tile `"luxury_tax"`: deduct tax (up to balance), bank collects same, may bankrupt | `test_luxury_tax_can_bankrupt_and_eliminate_player` in `tests/test_taxes_and_rent.py` |
| Tile `"free_parking"`: no effect on balance or jail state | `test_free_parking_tile_has_no_effect` in `tests/test_taxes_and_rent.py` |
| Tile `"chance"`: draw from `CHANCE_DECK` and call `apply_card` | Indirectly via card tests in `tests/test_bankruptcy_cards.py` and deck tests in `tests/test_dice_and_cards.py` (card effects and deck mechanics are covered; this branch is a thin wrapper) |
| Tile `"community_chest"`: draw from `COMMUNITY_DECK` and call `apply_card` | Same as chance: `tests/test_bankruptcy_cards.py` and `tests/test_dice_and_cards.py` cover card effects and deck behaviour |
| Tile `"railroad"`: look up property and, if present, call `handle_property_tile` | Currently no real Board properties at railroad positions; effectively dead branch (documented as such) |
| Tile `"property"`: look up property and call `handle_property_tile` if non-`None` | Property flows (buy/skip/rent) tested via `handle_property_tile` and movement tests in `tests/test_winner_and_movement_and_purchase.py`, plus `_card_move_to` property landing in `tests/test_bankruptcy_cards.py` |

---

### `handle_property_tile`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Property unowned; input `"b"`: attempt to buy via `buy_property` | `test_buy_property_succeeds_when_affordable` and related tests in `tests/test_winner_and_movement_and_purchase.py` |
| Property unowned; input `"a"`: call `auction_property` | `test_property_tile_auction_path` (and other property/auction interaction tests) in `tests/test_winner_and_movement_and_purchase.py` |
| Property unowned; input `"s"`: skip purchase | `test_unowned_property_tile_skip_with_s` in `tests/test_winner_and_movement_and_purchase.py` |
| Property unowned; invalid input: print invalid choice and skip by default | `test_unowned_property_tile_invalid_choice_defaults_to_skip` in `tests/test_winner_and_movement_and_purchase.py` |
| Property owned by current player: no rent collected | `test_landing_on_owned_property_does_not_charge_rent` in `tests/test_winner_and_movement_and_purchase.py` |
| Property owned by another player: call `pay_rent` | `test_pay_rent_transfers_to_owner` and `test_pay_rent_can_bankrupt_tenant` in `tests/test_trade_and_rent.py` (pay_rent behaviour), plus movement tests in `tests/test_winner_and_movement_and_purchase.py` |

---

### `buy_property`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `player.balance < prop.price`: cannot afford, returns `False` | `test_buy_property_fails_when_balance_less_than_price` in `tests/test_winner_and_movement_and_purchase.py` |
| Player can afford: deduct price, set owner, add property, bank collects | `test_buy_property_succeeds_when_affordable` in `tests/test_winner_and_movement_and_purchase.py` |

---

### `pay_rent`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Property is mortgaged: no rent collected | `test_mortgaged_property_collects_no_rent` in `tests/test_trade_and_rent.py` |
| Property has no owner: returns without effect | `test_pay_rent_no_owner_no_effect` in `tests/test_trade_and_rent.py` |
| Normal rent: deduct from tenant, add to owner | `test_pay_rent_transfers_to_owner` in `tests/test_trade_and_rent.py` |
| Rent payment can bankrupt tenant and eliminate them | `test_pay_rent_can_bankrupt_tenant` in `tests/test_trade_and_rent.py` |

---

### `trade`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `prop.owner != seller`: trade fails | `test_trade_fails_when_seller_does_not_own_property` in `tests/test_trade_and_rent.py` |
| `buyer.balance < cash_amount`: trade fails | `test_trade_fails_when_buyer_cannot_afford` in `tests/test_trade_and_rent.py` |
| Successful trade: transfer property and adjust balances | `test_trade_succeeds_and_transfers_property_and_cash` in `tests/test_trade_and_rent.py` |

---

### `auction_property`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Bid `<= 0`: player passes | `test_auction_property_no_bids_and_with_winner` (all players bid 0) in `tests/test_game_ui_main.py` |
| Bid `< highest_bid + AUCTION_MIN_INCREMENT`: bid rejected as too low | `test_auction_property_rejects_low_and_unaffordable_bids` in `tests/test_game_ui_main.py` |
| Bid `> player.balance`: bid rejected as unaffordable | `test_auction_property_rejects_low_and_unaffordable_bids` in `tests/test_game_ui_main.py` |
| Valid highest bid exists: winner pays, becomes owner, bank collects | `test_auction_property_no_bids_and_with_winner` in `tests/test_game_ui_main.py` |
| No valid bids at all: property remains unowned | `test_auction_property_no_bids_and_with_winner` (first part) in `tests/test_game_ui_main.py` |

---

### `_handle_jail_turn`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Player has jail card and confirms use: card consumed, released, roll and move | `test_use_get_out_of_jail_free_card_with_confirm_yes` in `tests/test_jail_and_cards.py` |
| Player has no card and declines fine: only `jail.turns` increments, no movement | `test_decline_all_options_increments_jail_turn_counter` in `tests/test_jail_and_cards.py` |
| Voluntary fine: player pays fine (up to balance), is released, and moves | `test_jail_turn_voluntary_fine_deducts_from_player` in `tests/test_jail_and_cards.py` |
| Voluntary fine causes bankruptcy: player eliminated, bank only collects available cash, no move | `test_jail_voluntary_fine_can_bankrupt_and_prevent_movement` in `tests/test_jail_and_cards.py` |
| Three skipped turns: mandatory fine, release, move when still solvent | `test_jail_turn_mandatory_fine_after_three_turns` in `tests/test_jail_and_cards.py` |
| Mandatory fine causes bankruptcy: player eliminated, bank only collects available cash, no move | `test_jail_mandatory_fine_bankruptcy_only_collects_available_cash` in `tests/test_jail_and_cards.py` |

---

### `_check_bankruptcy` / `check_bankruptcy`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Player not bankrupt: no elimination | Many tests indirectly (e.g., tax and rent tests where balance stays >= 0), such as `test_income_tax_reduces_balance_but_not_eliminate_when_affordable` in `tests/test_taxes_and_rent.py` |
| Player bankrupt: eliminate, clear properties, remove from players | `test_collect_from_all_can_bankrupt_and_eliminate_other_players` in `tests/test_bankruptcy_cards.py`, `test_pay_rent_can_bankrupt_tenant` in `tests/test_trade_and_rent.py`, tax and jail bankruptcy tests in `tests/test_taxes_and_rent.py` and `tests/test_jail_and_cards.py` |

---

### `find_winner` and `run`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `find_winner` with no players → returns `None` | `test_find_winner_with_no_players_returns_none` in `tests/test_winner_and_movement_and_purchase.py` |
| `find_winner` chooses player with highest net worth | `test_find_winner_picks_highest_net_worth` in `tests/test_winner_and_movement_and_purchase.py` |
| `run` main loop terminates when only one player remains or turn limit reached | `test_main_runs_game_entry_point` and related integration tests in `tests/test_game_ui_main.py` |

---

## moneypoly.board

### `get_tile_type`, `is_purchasable`, collections

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `get_property_at` returns `Property` for known positions, `None` otherwise | `test_get_property_and_tile_types_and_specials` and `test_is_purchasable_owned_mortgaged_and_collections` in `tests/test_player_board_property.py` |
| `get_tile_type`: `"go"`, `"property"`, `"blank"`, special tiles (including `"jail"`) | `test_get_property_and_tile_types_and_specials` in `tests/test_player_board_property.py` |
| `is_purchasable`: true for unowned, not-mortgaged property | `test_is_purchasable_owned_mortgaged_and_collections` in `tests/test_player_board_property.py` |
| `is_purchasable`: false for mortgaged, owned, or non-property tiles | `test_is_purchasable_owned_mortgaged_and_collections` in `tests/test_player_board_property.py` |
| `properties_owned_by` and `unowned_properties` reflect ownership | `test_is_purchasable_owned_mortgaged_and_collections` in `tests/test_player_board_property.py` |

---

## moneypoly.property

### `Property`, `PropertySpec`, `PropertyGroup`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `PropertySpec.as_tuple` includes name, position, price, rent, group | `test_propertyspec_as_tuple_and_with_group` and `test_propertyspec_tuple_and_with_group` in `tests/test_player_board_property.py` |
| `with_group` returns a new spec with updated group | Same tests as above in `tests/test_player_board_property.py` |
| `Property.mortgage`: first call returns mortgage value, second returns 0 | `test_property_mortgage_unmortgage_and_availability` and `test_mortgage_unmortgage_and_availability` in `tests/test_player_board_property.py` |
| `Property.unmortgage`: first call returns 110% value and clears mortgage; second returns 0 | Same as above in `tests/test_player_board_property.py` |
| `Property.is_available`: true when unowned and not mortgaged; false when mortgaged or owned | `test_property_mortgage_unmortgage_and_availability` and `test_mortgage_unmortgage_and_availability` in `tests/test_player_board_property.py` |
| `Property.get_rent`: base rent vs doubled for full group ownership | `test_group_ownership_rent_and_counts` and `test_get_rent_full_group_and_mortgage` in `tests/test_player_board_property.py` |
| `Property.get_rent`: 0 when mortgaged | `test_group_ownership_rent_and_counts` and `test_get_rent_full_group_and_mortgage` in `tests/test_player_board_property.py` |
| `PropertyGroup.all_owned_by`: false for partial, true for full ownership | `test_group_ownership_rent_and_counts` and `test_group_ownership_and_counts` in `tests/test_player_board_property.py` |
| `PropertyGroup.get_owner_counts` and `size` | Same group ownership tests in `tests/test_player_board_property.py` |

---

## moneypoly.player

### `Player` helpers

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `add_money` / `deduct_money` raise `ValueError` on negative amounts | `test_add_and_deduct_negative_amount_raises` and `test_negative_add_and_deduct_raise` in `tests/test_player_board_property.py` |
| `go_to_jail` sets position and jail status | `test_go_to_jail_sets_position_and_status` and `test_go_to_jail_and_status_line` in `tests/test_player_board_property.py` |
| `status_line` includes jailed tag when in jail | Same tests as above in `tests/test_player_board_property.py` |
| `add_property` / `remove_property` update `count_properties` | `test_properties_helpers_and_repr_and_status_line` and `test_properties_and_count` in `tests/test_player_board_property.py` |
| `__repr__` includes player name | `test_properties_helpers_and_repr_and_status_line` in `tests/test_player_board_property.py` |

### `Player.move`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Move wraps past end of board and awards Go salary once | `test_move_past_go_awards_salary` in `tests/test_winner_and_movement_and_purchase.py` |
| Move lands exactly on Go (position 0) and awards Go salary once | `test_move_lands_exactly_on_go_awards_salary` in `tests/test_winner_and_movement_and_purchase.py` |

---

## moneypoly.dice

### `Dice`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| `reset` sets `die1`, `die2`, and `doubles_streak` to 0 | `test_reset_clears_values_and_streak` in `tests/test_dice_and_cards.py` |
| `roll` updates `doubles_streak` for doubles and non-doubles | `test_roll_updates_doubles_streak_and_describe` in `tests/test_dice_and_cards.py` |
| `describe` output includes `(DOUBLES)` when appropriate | `test_roll_updates_doubles_streak_and_describe` in `tests/test_dice_and_cards.py` |
| `__repr__` returns a string containing `"Dice("` | `test_roll_updates_doubles_streak_and_describe` in `tests/test_dice_and_cards.py` |

---

## moneypoly.cards

### `CardDeck`

| Branch / Condition | Tests covering it |
| ------------------- | ----------------- |
| Drawing from an empty deck returns `None` and `cards_remaining` is 0 | `test_empty_deck_draw_and_peek` in `tests/test_dice_and_cards.py` |
| Drawing cycles through cards and updates `cards_remaining` correctly | `test_draw_cycles_through_cards_and_cards_remaining` in `tests/test_dice_and_cards.py` |
| Automatic reshuffle when deck exhausted and index reset | `test_auto_reshuffle_when_deck_exhausted` and `test_reshuffle_resets_index` in `tests/test_dice_and_cards.py` |
| `peek` does not advance index | `test_draw_cycles_through_cards_and_cards_remaining` in `tests/test_dice_and_cards.py` |
| `__len__` and `__repr__` behave without error | `test_empty_deck_draw_and_peek` and `test_len_and_repr_do_not_crash` in `tests/test_dice_and_cards.py` |

---

## moneypoly.ui and main

These modules have thinner logic; their branches are mostly about printing and argument wiring. They are covered by:

| Area | Tests covering it |
| ---- | ----------------- |
| UI print helpers and `format_currency` | `test_print_helpers_and_format_currency` in `tests/test_game_ui_main.py` |
| `get_player_names` / `main` entrypoint wiring | `test_main_runs_game_entry_point` and related tests in `tests/test_game_ui_main.py` |

---

This table focuses on the main gameplay and state-transition branches. Smaller or purely cosmetic branches (e.g., print-only paths and some reprs) are covered where relevant by the same tests listed above.
