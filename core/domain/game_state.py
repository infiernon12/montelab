"""Game state enums and data structures"""
from enum import Enum
from dataclasses import dataclass
from typing import List
from .card import Card


class Position(Enum):
    """Player position at the table"""
    UTG = "UTG"
    MP = "MP"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class Action(Enum):
    """Available player actions"""
    FOLD = "FOLD"
    CALL = "CALL"
    RAISE = "RAISE"
    ALL_IN = "ALL_IN"


class GameStage(Enum):
    """Current game stage"""
    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"


class TableSize(Enum):
    """Table size configurations"""
    HEADS_UP = "heads_up"
    THREE_MAX = "3max"
    FOUR_MAX = "4max"
    FIVE_MAX = "5max"
    SIX_MAX = "6max"
    SEVEN_MAX = "7max"
    EIGHT_MAX = "8max"
    NINE_MAX = "9max"


class GameType(Enum):
    """Game type variants"""
    CASH = "Cash"
    TOURNAMENT = "TTM"


@dataclass
class GameState:
    """Current game state snapshot"""
    table_size: TableSize
    game_type: GameType
    stage: GameStage
    player_cards: List[Card]
    board_cards: List[Card]
    
    def get_opponents_count(self) -> int:
        """Get number of opponents based on table size"""
        opponents_map = {
            TableSize.HEADS_UP: 1,
            TableSize.THREE_MAX: 2,
            TableSize.FOUR_MAX: 3,
            TableSize.FIVE_MAX: 4,
            TableSize.SIX_MAX: 5,
            TableSize.SEVEN_MAX: 6,
            TableSize.EIGHT_MAX: 7,
            TableSize.NINE_MAX: 8
        }
        return opponents_map.get(self.table_size, 1)
    
    def get_players_count(self) -> int:
        """Get total players at table"""
        return self.get_opponents_count() + 1
