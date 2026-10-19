class_name Data
extends RefCounted

const SUIT_NAMES := ["Spades", "Hearts", "Clubs", "Diamonds"]
const SUIT_COLORS := [Color("2b2d42"), Color("e63946"), Color("1d6fd1"), Color("f08a24")]
const RANK_LABELS := {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"}

const CHIP_COLOR := Color("2f8fe8")
const MULT_COLOR := Color("ff4d4d")
const MONEY_COLOR := Color("ffcc33")
const XMULT_COLOR := Color("ff9f1c")

const HAND_ORDER := [
	"Straight Flush", "Four of a Kind", "Full House", "Flush", "Straight",
	"Three of a Kind", "Two Pair", "Pair", "High Card",
]

# name -> [base chips, base mult, chips per level, mult per level]
const HAND_BASE := {
	"Straight Flush": [100, 8, 40, 4],
	"Four of a Kind": [60, 7, 30, 3],
	"Full House": [40, 4, 25, 2],
	"Flush": [35, 4, 15, 2],
	"Straight": [30, 4, 30, 3],
	"Three of a Kind": [30, 3, 20, 2],
	"Two Pair": [20, 2, 20, 1],
	"Pair": [10, 2, 15, 1],
	"High Card": [5, 1, 10, 1],
}

const ANTE_BASE := [300, 800, 2000, 5000, 11000, 20000, 35000, 50000]
const FINAL_ANTE := 8
const BLIND_NAMES := ["Small Blind", "Big Blind"]
const BLIND_COLORS := [Color("3a7bd5"), Color("e0a526")]

# rarity: 0 common, 1 uncommon, 2 rare
const CHARMS := [
	{"id": "jester", "name": "Jester", "desc": "+4 Mult", "cost": 2, "rarity": 0},
	{"id": "ruby", "name": "Ruby Ring", "desc": "Scored Hearts give +3 Mult", "cost": 5, "rarity": 0},
	{"id": "topaz", "name": "Topaz Ring", "desc": "Scored Diamonds give +3 Mult", "cost": 5, "rarity": 0},
	{"id": "onyx", "name": "Onyx Ring", "desc": "Scored Spades give +3 Mult", "cost": 5, "rarity": 0},
	{"id": "jade", "name": "Jade Ring", "desc": "Scored Clubs give +3 Mult", "cost": 5, "rarity": 0},
	{"id": "twin", "name": "Twin Mask", "desc": "+8 Mult if hand contains a Pair", "cost": 3, "rarity": 0},
	{"id": "triad", "name": "Triad Mask", "desc": "+12 Mult if hand contains Three of a Kind", "cost": 4, "rarity": 0},
	{"id": "duo", "name": "Duo Mask", "desc": "+10 Mult if hand contains Two Pair", "cost": 4, "rarity": 0},
	{"id": "ladder", "name": "Ladder", "desc": "+12 Mult if hand contains a Straight", "cost": 4, "rarity": 0},
	{"id": "tide", "name": "Tide", "desc": "+10 Mult if hand contains a Flush", "cost": 4, "rarity": 0},
	{"id": "mint", "name": "Thin Mint", "desc": "+20 Mult if 3 or fewer cards are played", "cost": 5, "rarity": 0},
	{"id": "flag", "name": "Flag", "desc": "+30 Chips per remaining discard", "cost": 5, "rarity": 0},
	{"id": "glitch", "name": "Glitch", "desc": "+0 to +23 Mult, at random", "cost": 4, "rarity": 0},
	{"id": "even", "name": "Even Keel", "desc": "Scored 10, 8, 6, 4, 2 give +4 Mult", "cost": 4, "rarity": 0},
	{"id": "odd", "name": "Odd Duck", "desc": "Scored A, 9, 7, 5, 3 give +31 Chips", "cost": 4, "rarity": 0},
	{"id": "scribe", "name": "Scribe", "desc": "Scored Aces give +20 Chips and +4 Mult", "cost": 4, "rarity": 0},
	{"id": "well", "name": "Deep Well", "desc": "+2 Chips per card left in the draw pile", "cost": 5, "rarity": 0},
	{"id": "crowd", "name": "Crowd", "desc": "+3 Mult per charm owned", "cost": 4, "rarity": 0},
	{"id": "laststand", "name": "Last Stand", "desc": "+15 Mult when no discards remain", "cost": 5, "rarity": 0},
	{"id": "court", "name": "Royal Court", "desc": "Scored J, Q, K give +30 Chips", "cost": 5, "rarity": 0},
	{"id": "spiral", "name": "Spiral", "desc": "Scored A, 2, 3, 5, 8 give +8 Mult", "cost": 7, "rarity": 1},
	{"id": "gold", "name": "Gold Tooth", "desc": "Earn $4 at the end of each round", "cost": 6, "rarity": 1},
	{"id": "snowball", "name": "Snowball", "desc": "Gains +1 Mult for every hand played", "cost": 6, "rarity": 1},
	{"id": "treasury", "name": "Treasury", "desc": "+2 Chips for every $1 you hold", "cost": 6, "rarity": 1},
	{"id": "hollow", "name": "Hollow", "desc": "x1 Mult for each empty charm slot (counts itself)", "cost": 8, "rarity": 1},
	{"id": "prism", "name": "Prism", "desc": "x3 Mult if played cards include all 4 suits", "cost": 7, "rarity": 1},
	{"id": "duet", "name": "Duet", "desc": "x2 Mult if hand contains a Pair", "cost": 8, "rarity": 2},
	{"id": "crown", "name": "Crown", "desc": "x1.5 Mult for each scored King", "cost": 9, "rarity": 2},
]

const RARITY_COLORS := [Color("4a6fa5"), Color("3f9a5a"), Color("b8334a")]
const RARITY_NAMES := ["Common", "Uncommon", "Rare"]
const RUNE_COLOR := Color("6c4ab6")
const RUNE_COST := 3

# Boss blinds ("hexes")
const HEXES := [
	{"id": "rust", "name": "The Rust", "desc": "All Clubs are debuffed", "suit": 2, "mult": 2.0, "min_ante": 1, "color": Color("8c9a3d")},
	{"id": "thorn", "name": "The Thorn", "desc": "All Hearts are debuffed", "suit": 1, "mult": 2.0, "min_ante": 1, "color": Color("b3364e")},
	{"id": "ash", "name": "The Ash", "desc": "All Spades are debuffed", "suit": 0, "mult": 2.0, "min_ante": 1, "color": Color("5b5d70")},
	{"id": "rot", "name": "The Rot", "desc": "All Diamonds are debuffed", "suit": 3, "mult": 2.0, "min_ante": 1, "color": Color("c46a2b")},
	{"id": "halving", "name": "The Halving", "desc": "Base Chips and Mult are halved", "mult": 2.0, "min_ante": 1, "color": Color("4b8e8d")},
	{"id": "grip", "name": "The Grip", "desc": "Discards 2 random held cards after every hand", "mult": 2.0, "min_ante": 1, "color": Color("a3542a")},
	{"id": "bulwark", "name": "The Bulwark", "desc": "Extra large blind", "mult": 4.0, "min_ante": 2, "color": Color("7b4fa0")},
	{"id": "needle", "name": "The Needle", "desc": "Play only 1 hand", "mult": 1.0, "min_ante": 2, "color": Color("5f7a2c")},
	{"id": "mute", "name": "The Mute", "desc": "All face cards are debuffed", "mult": 2.0, "min_ante": 2, "color": Color("6b6b9a")},
	{"id": "drought", "name": "The Drought", "desc": "No discards this round", "mult": 2.0, "min_ante": 2, "color": Color("c4a03a")},
]


static func ante_target(ante: int) -> int:
	if ante <= FINAL_ANTE:
		return ANTE_BASE[ante - 1]
	var raw := float(ANTE_BASE[FINAL_ANTE - 1]) * pow(1.75, ante - FINAL_ANTE)
	var mag := pow(10.0, floor(log(raw) / log(10.0)) - 1)
	return int(floor(raw / mag) * mag)


static func card_chips(rank: int) -> int:
	if rank == 14:
		return 11
	if rank >= 11:
		return 10
	return rank


static func charm_def(id: String) -> Dictionary:
	for c in CHARMS:
		if c.id == id:
			return c
	return {}


static func hand_chips(hand: String, level: int) -> int:
	var b: Array = HAND_BASE[hand]
	return b[0] + b[2] * (level - 1)


static func hand_mult(hand: String, level: int) -> int:
	var b: Array = HAND_BASE[hand]
	return b[1] + b[3] * (level - 1)


static func fmt(n) -> String:
	var s := str(int(n))
	var neg := s.begins_with("-")
	if neg:
		s = s.substr(1)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if neg else "") + s + out
