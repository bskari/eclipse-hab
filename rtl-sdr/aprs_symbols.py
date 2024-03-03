import dataclasses
import typing

def get_symbol(table: str, symbol: str) -> str:
    if table == "/":
        return PRIMARY_TABLE.get(symbol, symbol)
    elif table == "\\":
        return ALTERNATE_TABLE.get(symbol, symbol)
    # I've seen some packets with other tables, like "I". Just guess?
    if symbol in PRIMARY_TABLE:
        return PRIMARY_TABLE[symbol]
    return ALTERNATE_TABLE.get(symbol, symbol)
  
  
PRIMARY_TABLE = {
    "!": "🚓",
    "#": "✡",  # Digipeater
    "$": "📞",
    "'": "🛩",
    "-": "🏠",
    ".": "X",
    ":": "🚒",
    "<": "🏍",
    "=": "🚂",
    ">": "🚗",
    "&": "🌉",
    "C": "🚣",
    "F": "🚜",
    "O": "🎈",
    "P": "🚓",
    "R": "🚙",
    "U": "🚌",
    "V": "🚙",
    "X": "🚁",
    "Y": "⛵",
    "[": "🧍",
    "^": "✈",
    "`": "📡",
    "b": "🚲",
    "d": "🚒",
    "f": "🚒",
    "g": "🛩",
    "j": "🛻",
    "k": "🛻",
    "l": "💻",
    "m": "🗼",
    "p": "🐕",
    "r": "🗼",
    "s": "🛥",
    "u": "🚚",
    "v": "🚐",
    "y": "🗼",
}

ALTERNATE_TABLE = {
  "#": "✡",
  "-": "🏠",
  ".": "?",
  "0": "⊙",
  "o": "⊙",
  "k": "🛻",
  "u": "🛻",
  "v": "🗼",
}
