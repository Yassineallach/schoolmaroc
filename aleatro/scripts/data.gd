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
	"Flush Five", "Flush House", "Five of a Kind", "Straight Flush", "Four of a Kind", "Full House", "Flush", "Straight",
	"Three of a Kind", "Two Pair", "Pair", "High Card",
]

# name -> [base chips, base mult, chips per level, mult per level]
const HAND_BASE := {
	"Flush Five": [160, 16, 50, 3],
	"Flush House": [140, 14, 40, 4],
	"Five of a Kind": [120, 12, 35, 3],
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
## Charm ids from older versions and what they became.
const RENAMED_CHARMS := {"crown": "seer"}
## Charms the shop only offers once a run flag is set.
const CHARM_UNLOCKS := {"ripe": "plantain_spoiled"}

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
	{"id": "snowball", "name": "Snowball", "desc": "Gains +1 Mult for every hand played and loses 1 Mult for every discard", "cost": 6, "rarity": 1},
	{"id": "treasury", "name": "Treasury", "desc": "+2 Chips for every $1 you hold", "cost": 6, "rarity": 1},
	{"id": "hollow", "name": "Hollow", "desc": "x1 Mult for each empty charm slot (counts itself)", "cost": 8, "rarity": 1},
	{"id": "prism", "name": "Prism", "desc": "x3 Mult if played cards include all 4 suits", "cost": 7, "rarity": 1},
	{"id": "warden", "name": "Warden", "desc": "Sell during a boss blind to disable it", "cost": 6, "rarity": 1},
	{"id": "duet", "name": "Duet", "desc": "x2 Mult if hand contains a Pair", "cost": 8, "rarity": 2},
	{"id": "seer", "name": "Seer", "desc": "+1 Mult for every Spell cast this run", "cost": 6, "rarity": 0},
	# --- batch 1
	{"id": "pairchips", "name": "Twin Veil", "desc": "+50 Chips if the hand contains a Pair", "cost": 3, "rarity": 0},
	{"id": "twopairchips", "name": "Duo Veil", "desc": "+80 Chips if the hand contains Two Pair", "cost": 4, "rarity": 0},
	{"id": "tripschips", "name": "Triad Veil", "desc": "+100 Chips if the hand contains Three of a Kind", "cost": 4, "rarity": 0},
	{"id": "straightchips", "name": "Rail Veil", "desc": "+100 Chips if the hand contains a Straight", "cost": 4, "rarity": 0},
	{"id": "flushchips", "name": "Tide Veil", "desc": "+80 Chips if the hand contains a Flush", "cost": 4, "rarity": 0},
	{"id": "tripsx", "name": "Triad Crown", "desc": "x3 Mult if the hand contains Three of a Kind", "cost": 8, "rarity": 2},
	{"id": "quadsx", "name": "Quad Crown", "desc": "x4 Mult if the hand contains Four of a Kind", "cost": 8, "rarity": 2},
	{"id": "straightx", "name": "Rail Crown", "desc": "x3 Mult if the hand contains a Straight", "cost": 8, "rarity": 2},
	{"id": "flushx", "name": "Tide Crown", "desc": "x2 Mult if the hand contains a Flush", "cost": 8, "rarity": 2},
	{"id": "grin", "name": "Grin", "desc": "Scored face cards give +5 Mult", "cost": 4, "rarity": 0},
	{"id": "radio", "name": "Radio", "desc": "Scored 10s and 4s give +10 Chips and +4 Mult", "cost": 4, "rarity": 0},
	{"id": "spearhead", "name": "Spearhead", "desc": "Scored Spades give +50 Chips", "cost": 7, "rarity": 1},
	{"id": "clover", "name": "Clover Stone", "desc": "Scored Clubs give +7 Mult", "cost": 7, "rarity": 1},
	{"id": "rawgem", "name": "Raw Topaz", "desc": "Scored Diamonds earn $1", "cost": 7, "rarity": 1},
	{"id": "heartstone", "name": "Heartstone", "desc": "Scored Hearts have a 1 in 2 chance to give x1.5 Mult", "cost": 7, "rarity": 1},
	{"id": "portrait", "name": "Portrait", "desc": "The first scored face card gives x2 Mult", "cost": 5, "rarity": 0},
	{"id": "tightrope", "name": "Tightrope", "desc": "x3 Mult on the final hand of the round", "cost": 6, "rarity": 1},
	{"id": "fist", "name": "Iron Fist", "desc": "The lowest card held in hand gives Mult equal to twice its value", "cost": 5, "rarity": 0},
	{"id": "regent", "name": "Regent", "desc": "Each King held in hand gives x1.5 Mult", "cost": 8, "rarity": 2},
	{"id": "moonrise", "name": "Moonrise", "desc": "Each Queen held in hand gives +13 Mult", "cost": 5, "rarity": 0},
	{"id": "encore", "name": "Encore", "desc": "Retrigger scored 2s, 3s, 4s and 5s", "cost": 6, "rarity": 1},
	{"id": "masquerade", "name": "Masquerade", "desc": "Retrigger scored face cards", "cost": 6, "rarity": 1},
	{"id": "punchcard", "name": "Punch Card", "desc": "Retrigger the first scored card 2 more times", "cost": 4, "rarity": 0},
	{"id": "twilight", "name": "Twilight", "desc": "Retrigger every scored card on the final hand of the round", "cost": 5, "rarity": 1},
	{"id": "callingcard", "name": "Calling Card", "desc": "Scored face cards have a 1 in 2 chance to earn $2", "cost": 4, "rarity": 0},
	{"id": "ticket", "name": "Gilt Ticket", "desc": "Scored Gilded cards earn $4", "cost": 5, "rarity": 0},
	{"id": "patience", "name": "Patience", "desc": "At end of round, earn $2 per discard left if you used none", "cost": 4, "rarity": 0},
	{"id": "corsair", "name": "Corsair", "desc": "+Mult equal to the sell value of your other charms", "cost": 4, "rarity": 0},
	{"id": "fame", "name": "Fame", "desc": "+Mult equal to how many times this hand type has been played this run", "cost": 5, "rarity": 0},
	{"id": "commuter", "name": "Commuter", "desc": "Gains +1 Mult for each hand in a row with no scored face card; resets on a face card", "cost": 6, "rarity": 0},
	{"id": "sprinter", "name": "Sprinter", "desc": "Gains +15 Chips each time the hand contains a Straight", "cost": 5, "rarity": 0},
	{"id": "foursquare", "name": "Four Square", "desc": "Gains +4 Chips each time exactly 4 cards are played", "cost": 4, "rarity": 0},
	{"id": "sorbet", "name": "Sorbet", "desc": "+100 Chips. Loses 5 Chips every hand played", "cost": 5, "rarity": 0},
	{"id": "kettle", "name": "Kettle Corn", "desc": "+20 Mult. Loses 4 Mult at the end of each round", "cost": 5, "rarity": 0},
	{"id": "plantain", "name": "Plantain", "desc": "+15 Mult. 1 in 6 chance to spoil at the end of each round", "cost": 5, "rarity": 0},
	{"id": "ripe", "name": "Ripe Plantain", "desc": "x3 Mult. 1 in 1000 chance to spoil at the end of each round", "cost": 4, "rarity": 0},
	{"id": "fizz", "name": "Fizz", "desc": "Retrigger every played card for the next 10 hands", "cost": 6, "rarity": 1},
	{"id": "cardshark", "name": "Card Shark", "desc": "x3 Mult if this hand type was already played this round", "cost": 6, "rarity": 1},
	{"id": "loyal", "name": "Loyalty Stamp", "desc": "x4 Mult every 6th hand played", "cost": 5, "rarity": 1},
	{"id": "slate", "name": "Slate", "desc": "x3 Mult if every card held in hand is a Spade or a Club", "cost": 6, "rarity": 1},
	{"id": "spread", "name": "Wide Grip", "desc": "Flushes and Straights can be made with 4 cards", "cost": 7, "rarity": 1},
	{"id": "hopscotch", "name": "Hopscotch", "desc": "Straights may skip one rank between cards (like 3 5 6 8 9)", "cost": 7, "rarity": 1},
	{"id": "blot", "name": "Ink Blot", "desc": "Hearts and Diamonds count as the same suit, and so do Spades and Clubs", "cost": 7, "rarity": 1},
	{"id": "mirage", "name": "Mirage", "desc": "Every card counts as a face card", "cost": 5, "rarity": 1},
	{"id": "puddle", "name": "Puddle", "desc": "Every played card counts in scoring", "cost": 3, "rarity": 0},
	{"id": "mimic", "name": "Mimic", "desc": "Retrigger the abilities of cards held in hand", "cost": 5, "rarity": 1},
	{"id": "ironwill", "name": "Iron Will", "desc": "x0.2 Mult for each Iron card in your full deck", "cost": 7, "rarity": 1},
	{"id": "quarry", "name": "Quarry", "desc": "+25 Chips for each Stone card in your full deck", "cost": 6, "rarity": 1},
	{"id": "mason", "name": "Mason", "desc": "Adds a Stone card to your deck when a blind starts", "cost": 6, "rarity": 1},
	{"id": "midas", "name": "Gilded Touch", "desc": "Scored face cards turn Gilded", "cost": 7, "rarity": 1},
	{"id": "leech", "name": "Leech", "desc": "Gains x0.1 Mult for each scored enhanced card, and strips the enhancement", "cost": 7, "rarity": 1},
	{"id": "rambler", "name": "Rambler", "desc": "Every scored card permanently gains +5 Chips", "cost": 5, "rarity": 1},
	{"id": "relic", "name": "Old Relic", "desc": "Scored cards of the round's suit give x1.5 Mult (suit changes every round)", "cost": 8, "rarity": 2},
	{"id": "keep", "name": "Keep", "desc": "Gains +3 Chips per discarded card of the round's suit (suit changes every round)", "cost": 6, "rarity": 1},
	{"id": "idol", "name": "Idol", "desc": "Scored copies of the round's card give x2 Mult (card changes every round)", "cost": 6, "rarity": 1},
	{"id": "rebate", "name": "Rebate", "desc": "Earn $5 for each discarded card of the round's rank (rank changes every round)", "cost": 4, "rarity": 0},
	{"id": "errand", "name": "Errand List", "desc": "Earn $4 when you play the listed hand type (it changes every round)", "cost": 4, "rarity": 0},
	{"id": "trousers", "name": "Patched Trousers", "desc": "Gains +2 Mult each time the hand contains Two Pair", "cost": 6, "rarity": 1},
	{"id": "flashcard", "name": "Flash Card", "desc": "Gains +2 Mult each time you reroll the shop", "cost": 5, "rarity": 1},
	{"id": "monolith", "name": "Monolith", "desc": "Gains x0.2 Mult for each hand in a row that isn't your most played hand type; resets when it is", "cost": 8, "rarity": 2},
	{"id": "frenzy", "name": "Frenzy", "desc": "When a Small or Big Blind starts, gains x0.5 Mult and destroys a random other charm", "cost": 7, "rarity": 1},
	{"id": "dagger", "name": "Ritual Knife", "desc": "When a blind starts, destroys the charm to its right and gains double its sell value as Mult", "cost": 6, "rarity": 1},
	{"id": "hologram", "name": "Hologram", "desc": "Gains x0.25 Mult each time a card is added to your deck", "cost": 7, "rarity": 1},
	{"id": "starmap", "name": "Star Map", "desc": "Gains x0.1 Mult each time you use a Rune", "cost": 6, "rarity": 1},
	{"id": "bonfire", "name": "Bonfire", "desc": "Gains x0.25 Mult for each charm sold; resets when a boss is beaten", "cost": 9, "rarity": 2},
	{"id": "maneki", "name": "Beckoning Cat", "desc": "Gains x0.25 Mult each time a Lucky card pays out", "cost": 6, "rarity": 1},
	{"id": "glazier", "name": "Glazier", "desc": "Gains x0.75 Mult each time a Glass card shatters", "cost": 6, "rarity": 1},
	{"id": "iou", "name": "IOU", "desc": "You can go up to $20 into debt", "cost": 1, "rarity": 0},
	{"id": "nestegg", "name": "Nest Egg", "desc": "Its sell value rises by $3 at the end of each round", "cost": 4, "rarity": 0},
	{"id": "giftwrap", "name": "Gift Wrap", "desc": "At the end of each round, every charm's sell value rises by $1", "cost": 6, "rarity": 1},
	{"id": "skyrocket", "name": "Skyrocket", "desc": "Earn $1 at the end of each round; the payout grows by $2 each time a boss is beaten", "cost": 6, "rarity": 1},
	{"id": "ninelives", "name": "Nine Lives", "desc": "Earn $1 at the end of each round for each 9 in your full deck", "cost": 7, "rarity": 1},
	{"id": "moonshot", "name": "Moonshot", "desc": "Interest is paid twice", "cost": 5, "rarity": 1},
	{"id": "satellite", "name": "Satellite", "desc": "Earn $1 at the end of each round for each different Rune used this run", "cost": 6, "rarity": 1},
	{"id": "valet", "name": "Valet", "desc": "Each face card held in hand has a 1 in 2 chance to earn $1", "cost": 6, "rarity": 0},
	{"id": "bootstraps", "name": "Bootstraps", "desc": "+2 Mult for every $5 you hold", "cost": 7, "rarity": 1},
	{"id": "toreador", "name": "Toreador", "desc": "Earn $8 each time a boss blind's effect hits your hand", "cost": 7, "rarity": 1},
	{"id": "wanderer", "name": "Wanderer", "desc": "Create a Spell when you play a hand while holding $4 or less", "cost": 8, "rarity": 2},
	{"id": "trader", "name": "Trader", "desc": "If the first discard of a round is a single card, destroy it and earn $3", "cost": 6, "rarity": 1},
	{"id": "burglar", "name": "Cat Burglar", "desc": "When a blind starts, gain 3 hands and lose all discards", "cost": 6, "rarity": 1},
	{"id": "tipsy", "name": "Tipsy", "desc": "+1 discard each round", "cost": 4, "rarity": 0},
	{"id": "juggler", "name": "Juggler", "desc": "+1 hand size", "cost": 4, "rarity": 0},
	{"id": "minstrel", "name": "Minstrel", "desc": "+2 hand size, but 1 fewer hand each round", "cost": 6, "rarity": 1},
	{"id": "merry", "name": "Merry Fool", "desc": "+3 discards each round, but -1 hand size", "cost": 7, "rarity": 1},
	{"id": "daredevil", "name": "Daredevil", "desc": "+250 Chips, but -2 hand size", "cost": 7, "rarity": 2},
	{"id": "sprout", "name": "Bean Sprout", "desc": "+5 hand size, shrinking by 1 every round", "cost": 6, "rarity": 1},
	{"id": "noodles", "name": "Noodle Bowl", "desc": "x2 Mult; loses x0.01 Mult for each card discarded", "cost": 6, "rarity": 1},
	{"id": "chaos", "name": "Chaos", "desc": "1 free reroll in every shop", "cost": 4, "rarity": 0},
	{"id": "stargazer", "name": "Stargazer", "desc": "Runes in the shop are free", "cost": 8, "rarity": 1},
	{"id": "license", "name": "License", "desc": "x3 Mult if at least 16 cards in your full deck are enhanced", "cost": 7, "rarity": 2},
	{"id": "pennant", "name": "Pennant", "desc": "Each Uncommon charm you own gives x1.5 Mult", "cost": 8, "rarity": 2},
	{"id": "tracing", "name": "Tracing Paper", "desc": "Copies the ability of the charm to its right", "cost": 10, "rarity": 2},
	{"id": "brainwave", "name": "Brainwave", "desc": "Copies the ability of your leftmost charm", "cost": 10, "rarity": 2},
	{"id": "phantom", "name": "Phantom", "desc": "After 2 rounds, sell it to duplicate a random other charm", "cost": 8, "rarity": 2},
	{"id": "loaded", "name": "Loaded Dice", "desc": "Doubles every listed chance (1 in 4 becomes 2 in 4)", "cost": 4, "rarity": 1},
	{"id": "crystal", "name": "Crystal Ball", "desc": "Each scored 8 has a 1 in 4 chance to create a Spell", "cost": 5, "rarity": 0},
	{"id": "secondsight", "name": "Second Sight", "desc": "If the first hand of a round is a single 6, destroy it and create an Omen", "cost": 6, "rarity": 1},
	{"id": "ouija", "name": "Spirit Board", "desc": "Create an Omen when you play a Straight Flush", "cost": 6, "rarity": 1},
	{"id": "quantum", "name": "Quantum", "desc": "Create a Spell when the hand contains both an Ace and a Straight", "cost": 4, "rarity": 0},
	{"id": "diviner", "name": "Diviner", "desc": "Create a Spell when a blind starts", "cost": 6, "rarity": 1},
	{"id": "notary", "name": "Notary", "desc": "When a round starts, add a random card with a random seal to your hand", "cost": 6, "rarity": 1},
	{"id": "clone", "name": "Clone", "desc": "If the first hand of a round is a single card, add a copy of it to your deck and hand", "cost": 8, "rarity": 2},
	{"id": "rabble", "name": "Rabble", "desc": "When a blind starts, create 2 Common charms (if there is room)", "cost": 6, "rarity": 0},
	{"id": "kindling", "name": "Kindling", "desc": "Levels up the hand type of your first discard each round", "cost": 8, "rarity": 2},
	{"id": "orbit", "name": "Orbit", "desc": "1 in 4 chance to level up the hand type you play", "cost": 5, "rarity": 1},
	{"id": "blankmask", "name": "Blank Mask", "desc": "Earn $5 when you discard 3 or more face cards at once", "cost": 4, "rarity": 0},
	{"id": "roadtrip", "name": "Road Trip", "desc": "Gains x0.5 Mult for each Jack discarded this round", "cost": 8, "rarity": 2},
	{"id": "doublevision", "name": "Double Vision", "desc": "x2 Mult if the scored cards include a Club and a card of another suit", "cost": 6, "rarity": 1},
	{"id": "tiny", "name": "Tiny", "desc": "Gains +8 Chips each time a 2 is scored", "cost": 8, "rarity": 2},
	{"id": "ringmaster", "name": "Ringmaster", "desc": "Charms and spells you already own can still show up in the shop", "cost": 5, "rarity": 1},
	{"id": "lastlaugh", "name": "Last Laugh", "desc": "Saves you from losing a round if you scored at least a quarter of the target, then breaks", "cost": 5, "rarity": 1},
	{"id": "wear", "name": "Wear and Tear", "desc": "+4 Mult for each card your deck is below its starting size", "cost": 6, "rarity": 1},
	{"id": "bonecrown", "name": "Bone Crown", "desc": "Gains x1 Mult each time a face card is destroyed", "cost": 20, "rarity": 3},
	{"id": "foolking", "name": "Fool King", "desc": "Scored Kings and Queens give x2 Mult", "cost": 20, "rarity": 3},
	{"id": "skull", "name": "Skull", "desc": "Gains x1 Mult for every 23 cards discarded", "cost": 20, "rarity": 3},
	{"id": "veto", "name": "Veto", "desc": "Disables the effect of every boss blind", "cost": 20, "rarity": 3},
	{"id": "hoarder", "name": "Hoarder", "desc": "When you leave the shop, makes a Negative copy of a random spell you hold", "cost": 20, "rarity": 3},
	{"id": "scrapbook", "name": "Scrapbook", "desc": "Gains +3 Mult each time you skip a booster pack", "cost": 5, "rarity": 0},
	{"id": "daydream", "name": "Daydream", "desc": "1 in 2 chance to create a Spell when you open a booster pack", "cost": 4, "rarity": 0},
	{"id": "rewind", "name": "Rewind", "desc": "x0.25 Mult for each blind skipped this run", "cost": 6, "rarity": 1},
	{"id": "float", "name": "Root Float", "desc": "Sell this to get a Twin Tag", "cost": 6, "rarity": 1},
]

# Card upgrades. Enhancements and seals live on playing cards; editions on cards and charms.
const ENHANCEMENTS := {
	"etched": {"name": "Etched", "desc": "+30 Chips when scored", "face": Color("dbe9ff"), "badge": Color("2f6fd1")},
	"charged": {"name": "Charged", "desc": "+4 Mult when scored", "face": Color("ffe0dc"), "badge": Color("d63a3a")},
	"glass": {"name": "Glass", "desc": "x2 Mult when scored; 1 in 4 chance to shatter", "face": Color("e3fbff"), "badge": Color("3aa6c4")},
	"iron": {"name": "Iron", "desc": "x1.5 Mult while held in hand", "face": Color("c8ced8"), "badge": Color("5d6675")},
	"gilded": {"name": "Gilded", "desc": "Earn $3 if held in hand at end of round", "face": Color("ffe7a0"), "badge": Color("c08a12")},
	"lucky": {"name": "Lucky", "desc": "1 in 5 chance of +20 Mult and 1 in 15 chance of $20 when scored", "face": Color("e2f6da"), "badge": Color("3b9a4a")},
	"stone": {"name": "Stone", "desc": "+50 Chips; no rank or suit, always scores", "face": Color("9a9590"), "badge": Color("5d5852")},
	"wild": {"name": "Wild", "desc": "Counts as every suit", "face": Color("f3e6ff"), "badge": Color("8a4fd0")},
}
const EDITIONS := {
	"foil": {"name": "Foil", "desc": "+50 Chips", "cost": 2, "shader": 1},
	"holo": {"name": "Holo", "desc": "+10 Mult", "cost": 3, "shader": 2},
	"chroma": {"name": "Chroma", "desc": "x1.5 Mult", "cost": 5, "shader": 3},
	"negative": {"name": "Negative", "desc": "+1 slot", "cost": 5, "shader": 4},
}
const SEALS := {
	"crimson": {"name": "Crimson Seal", "desc": "Retrigger this card", "color": Color("d6283c")},
	"golden": {"name": "Golden Seal", "desc": "Earn $3 when this card is scored", "color": Color("f2b415")},
	"azure": {"name": "Azure Seal", "desc": "Creates the Rune for the last hand played if held in hand at end of round", "color": Color("2f8fe8")},
	"violet": {"name": "Violet Seal", "desc": "Creates a Spell when discarded", "color": Color("9b5de5")},
}

# Spells: held in two slots and cast on the cards selected in hand.
# max = most cards it can target; 0 = no target needed.
const SPELLS := [
	{"id": "etch", "name": "Etch", "desc": "Make up to 2 selected cards Etched", "max": 2, "enh": "etched"},
	{"id": "charge", "name": "Charge", "desc": "Make up to 2 selected cards Charged", "max": 2, "enh": "charged"},
	{"id": "glaze", "name": "Glaze", "desc": "Make 1 selected card Glass", "max": 1, "enh": "glass"},
	{"id": "forge", "name": "Forge", "desc": "Make 1 selected card Iron", "max": 1, "enh": "iron"},
	{"id": "gild", "name": "Gild", "desc": "Make 1 selected card Gilded", "max": 1, "enh": "gilded"},
	{"id": "clover", "name": "Clover", "desc": "Make up to 2 selected cards Lucky", "max": 2, "enh": "lucky"},
	{"id": "bloom", "name": "Bloom", "desc": "Turn up to 3 selected cards into Hearts", "max": 3, "suit": 1},
	{"id": "shade", "name": "Shade", "desc": "Turn up to 3 selected cards into Spades", "max": 3, "suit": 0},
	{"id": "bramble", "name": "Bramble", "desc": "Turn up to 3 selected cards into Clubs", "max": 3, "suit": 2},
	{"id": "kindle", "name": "Kindle", "desc": "Turn up to 3 selected cards into Diamonds", "max": 3, "suit": 3},
	{"id": "ascend", "name": "Ascend", "desc": "Raise up to 2 selected cards by one rank", "max": 2},
	{"id": "purge", "name": "Purge", "desc": "Destroy up to 2 selected cards", "max": 2},
	{"id": "mirror", "name": "Mirror", "desc": "Select 2 cards: the left one becomes a copy of the right one", "max": 2, "min": 2},
	{"id": "windfall", "name": "Windfall", "desc": "Double your money (up to +$20)", "max": 0},
	{"id": "petrify", "name": "Petrify", "desc": "Turn 1 selected card to Stone", "max": 1, "enh": "stone"},
	{"id": "chimera", "name": "Chimera", "desc": "Make 1 selected card Wild", "max": 1, "enh": "wild"},
	{"id": "replay", "name": "Replay", "desc": "Create a copy of the last Spell cast this run (not Replay)", "max": 0},
	{"id": "oracle", "name": "Oracle", "desc": "Create up to 2 random Runes", "max": 0},
	{"id": "summon", "name": "Summon", "desc": "Create up to 2 random Spells", "max": 0},
	{"id": "fortune", "name": "Fortune", "desc": "1 in 4 chance to give a random charm Foil, Holo or Chroma", "max": 0},
	{"id": "barter", "name": "Barter", "desc": "Earn the total sell value of your charms (up to $50)", "max": 0},
	{"id": "conjure", "name": "Conjure", "desc": "Create a random charm", "max": 0},
	# Omens: rare spells that come from packs and charms, never the regular shop.
	# "hand": acts on the cards in hand, so only during a round.
	{"id": "courtiers", "name": "Courtiers", "desc": "Destroy 1 random card in hand; add 3 random enhanced face cards to your hand", "max": 0, "omen": true, "hand": true},
	{"id": "reaper", "name": "Reaper", "desc": "Destroy 1 random card in hand; add 2 random enhanced Aces to your hand", "max": 0, "omen": true, "hand": true},
	{"id": "chant", "name": "Chant", "desc": "Destroy 1 random card in hand; add 4 random enhanced numbered cards to your hand", "max": 0, "omen": true, "hand": true},
	{"id": "talisman", "name": "Talisman", "desc": "Add a Golden Seal to 1 selected card", "max": 1, "omen": true},
	{"id": "aura", "name": "Aura", "desc": "Give 1 selected card Foil, Holo or Chroma", "max": 1, "omen": true},
	{"id": "wraith", "name": "Wraith", "desc": "Create a Rare charm, but your money drops to $0", "max": 0, "omen": true},
	{"id": "converge", "name": "Converge", "desc": "Turn every card in hand into one random suit", "max": 0, "omen": true, "hand": true},
	{"id": "mono", "name": "Mono", "desc": "Turn every card in hand into one random rank; -1 hand size", "max": 0, "omen": true, "hand": true},
	{"id": "void", "name": "Void", "desc": "Make a random charm Negative; -1 hand size", "max": 0, "omen": true},
	{"id": "pyre", "name": "Pyre", "desc": "Destroy 5 random cards in hand; earn $20", "max": 0, "omen": true, "hand": true},
	{"id": "rebirth", "name": "Rebirth", "desc": "Copy a random charm and destroy all the others", "max": 0, "omen": true},
	{"id": "sigil", "name": "Sigil", "desc": "Add a Crimson Seal to 1 selected card", "max": 1, "omen": true},
	{"id": "curse", "name": "Curse", "desc": "Make a random charm Chroma and destroy all the others", "max": 0, "omen": true},
	{"id": "lull", "name": "Lull", "desc": "Add an Azure Seal to 1 selected card", "max": 1, "omen": true},
	{"id": "whisper", "name": "Whisper", "desc": "Add a Violet Seal to 1 selected card", "max": 1, "omen": true},
	{"id": "duplicate", "name": "Duplicate", "desc": "Add 2 copies of 1 selected card to your deck", "max": 1, "omen": true},
	{"id": "soul", "name": "Soul", "desc": "Create a Legendary charm", "max": 0, "omen": true, "hidden": true},
	{"id": "singularity", "name": "Singularity", "desc": "Level up every hand type", "max": 0, "omen": true, "hidden": true},
]
const OMEN_COLOR := Color("4b3a8a")
# Tags: the reward for skipping a Small or Big Blind.
const TAGS := [
	{"id": "riches", "name": "Riches Tag", "desc": "Double your money (up to +$40)", "color": Color("e0a526")},
	{"id": "haste", "name": "Haste Tag", "desc": "Earn $5 for each blind skipped this run", "color": Color("d9572b")},
	{"id": "rare", "name": "Rare Tag", "desc": "The next shop has a free Rare charm", "color": Color("b8334a")},
	{"id": "uncommon", "name": "Uncommon Tag", "desc": "The next shop has a free Uncommon charm", "color": Color("3f9a5a")},
	{"id": "coupon", "name": "Coupon Tag", "desc": "Everything first stocked in the next shop is free", "color": Color("f07a9a")},
	{"id": "star", "name": "Star Tag", "desc": "Level up a random hand type 3 times", "color": Color("6c4ab6")},
	{"id": "juggle", "name": "Juggle Tag", "desc": "+3 hand size for the next round", "color": Color("2ec4b6")},
	{"id": "bundle", "name": "Bundle Tag", "desc": "Open a free Charm Pack", "color": Color("4a6fa5")},
	{"id": "tome", "name": "Tome Tag", "desc": "Open a free Spell Pack", "color": Color("2f7f6f")},
	{"id": "twin", "name": "Twin Tag", "desc": "Copies the next tag you get", "color": Color("8a96a3")},
	{"id": "invest", "name": "Investment Tag", "desc": "Earn $15 after beating the next boss", "color": Color("c08a12")},
	{"id": "dice", "name": "Dice Tag", "desc": "Rerolls in the next shop start at $0", "color": Color("3a7bd5")},
]

# Booster packs: open one, pick from what's inside (or skip). Arcana and
# Omen packs are used on cards drawn from your deck right away; Celestial
# packs level hands up right away.
#   kind: what's inside   show/choose: how many shown / picked   weight: shop odds
const PACK_KINDS := {
	"standard": {"name": "Card Pack", "what": "playing cards", "color": Color("c08a12")},
	"arcana": {"name": "Spell Pack", "what": "Spells", "color": Color("2f7f6f")},
	"celestial": {"name": "Rune Pack", "what": "Runes", "color": Color("6c4ab6")},
	"buffoon": {"name": "Charm Pack", "what": "charms", "color": Color("4a6fa5")},
	"spectral": {"name": "Omen Pack", "what": "Omens", "color": Color("4b3a8a")},
}
const PACKS := {
	"standard": {"kind": "standard", "size": "", "show": 3, "choose": 1, "cost": 4, "weight": 4.0},
	"standard_jumbo": {"kind": "standard", "size": "Jumbo", "show": 5, "choose": 1, "cost": 6, "weight": 2.0},
	"standard_mega": {"kind": "standard", "size": "Mega", "show": 5, "choose": 2, "cost": 8, "weight": 0.5},
	"arcana": {"kind": "arcana", "size": "", "show": 3, "choose": 1, "cost": 4, "weight": 4.0},
	"arcana_jumbo": {"kind": "arcana", "size": "Jumbo", "show": 5, "choose": 1, "cost": 6, "weight": 2.0},
	"arcana_mega": {"kind": "arcana", "size": "Mega", "show": 5, "choose": 2, "cost": 8, "weight": 0.5},
	"celestial": {"kind": "celestial", "size": "", "show": 3, "choose": 1, "cost": 4, "weight": 4.0},
	"celestial_jumbo": {"kind": "celestial", "size": "Jumbo", "show": 5, "choose": 1, "cost": 6, "weight": 2.0},
	"celestial_mega": {"kind": "celestial", "size": "Mega", "show": 5, "choose": 2, "cost": 8, "weight": 0.5},
	"buffoon": {"kind": "buffoon", "size": "", "show": 2, "choose": 1, "cost": 4, "weight": 1.2},
	"buffoon_jumbo": {"kind": "buffoon", "size": "Jumbo", "show": 4, "choose": 1, "cost": 6, "weight": 0.6},
	"buffoon_mega": {"kind": "buffoon", "size": "Mega", "show": 4, "choose": 2, "cost": 8, "weight": 0.15},
	"spectral": {"kind": "spectral", "size": "", "show": 2, "choose": 1, "cost": 4, "weight": 0.6},
	"spectral_jumbo": {"kind": "spectral", "size": "Jumbo", "show": 4, "choose": 1, "cost": 6, "weight": 0.3},
	"spectral_mega": {"kind": "spectral", "size": "Mega", "show": 4, "choose": 2, "cost": 8, "weight": 0.07},
}


static func pack_name(id: String) -> String:
	var p: Dictionary = PACKS[id]
	return ("%s %s" % [p.size, PACK_KINDS[p.kind].name]).strip_edges()


static func pack_desc(id: String) -> String:
	var p: Dictionary = PACKS[id]
	return "Choose %d of %d %s" % [p.choose, p.show, PACK_KINDS[p.kind].what]


# Vouchers: permanent upgrades, one offered per ante. The second of each
# pair needs the first.
const VOUCHER_COST := 10
const VOUCHERS := [
	{"id": "shelf", "name": "Extra Shelf", "desc": "+1 card slot in the shop"},
	{"id": "shelves", "name": "Full Shelves", "desc": "+1 more card slot in the shop", "needs": "shelf"},
	{"id": "clearance", "name": "Clearance", "desc": "Everything in the shop is 25% off"},
	{"id": "firesale", "name": "Fire Sale", "desc": "Everything in the shop is 50% off", "needs": "clearance"},
	{"id": "polish", "name": "Polish", "desc": "Foil, Holo and Chroma show up 2x more often"},
	{"id": "shine", "name": "Shine", "desc": "Foil, Holo and Chroma show up 4x more often", "needs": "polish"},
	{"id": "cheapdice", "name": "Cheap Dice", "desc": "Rerolls cost $2 less"},
	{"id": "shaker", "name": "Loaded Shaker", "desc": "Rerolls cost another $2 less", "needs": "cheapdice"},
	{"id": "satchel", "name": "Satchel", "desc": "+1 spell slot"},
	{"id": "lamp", "name": "Spirit Lamp", "desc": "Omens can show up in Spell Packs", "needs": "satchel"},
	{"id": "spyglass", "name": "Spyglass", "desc": "Rune Packs always hold the Rune for your most played hand"},
	{"id": "planetarium", "name": "Planetarium", "desc": "Runes kept in your slots give x1.5 Mult when their hand is played", "needs": "spyglass"},
	{"id": "grip", "name": "Extra Grip", "desc": "+1 hand every round"},
	{"id": "tongs", "name": "Tongs", "desc": "+1 more hand every round", "needs": "grip"},
	{"id": "wastebin", "name": "Wastebin", "desc": "+1 discard every round"},
	{"id": "recycler", "name": "Recycler", "desc": "+1 more discard every round", "needs": "wastebin"},
	{"id": "spellseller", "name": "Spell Seller", "desc": "Spells show up in the shop 2x more often"},
	{"id": "spellbaron", "name": "Spell Baron", "desc": "Spells show up in the shop 4x more often", "needs": "spellseller"},
	{"id": "runeseller", "name": "Rune Seller", "desc": "Runes show up in the shop 2x more often"},
	{"id": "runebaron", "name": "Rune Baron", "desc": "Runes show up in the shop 4x more often", "needs": "runeseller"},
	{"id": "nestbox", "name": "Nest Box", "desc": "Interest can reach $10 per round"},
	{"id": "goldtree", "name": "Golden Tree", "desc": "Interest can reach $20 per round", "needs": "nestbox"},
	{"id": "blank", "name": "Blank", "desc": "Does nothing?"},
	{"id": "antimatter", "name": "Hollow Space", "desc": "+1 charm slot", "needs": "blank"},
	{"id": "stall", "name": "Card Stall", "desc": "Playing cards can show up in the shop"},
	{"id": "showcase", "name": "Showcase", "desc": "Playing cards in the shop may have an enhancement, edition or seal", "needs": "stall"},
	{"id": "timeglyph", "name": "Time Glyph", "desc": "-1 ante, but 1 fewer hand every round"},
	{"id": "stoneglyph", "name": "Stone Glyph", "desc": "-1 ante, but 1 fewer discard every round", "needs": "timeglyph"},
	{"id": "bossswap", "name": "Boss Swap", "desc": "Reroll the boss blind once per ante ($10)"},
	{"id": "rewrite", "name": "Rewrite", "desc": "Reroll the boss blind as often as you like ($10 each)", "needs": "bossswap"},
	{"id": "brush", "name": "Brush", "desc": "+1 hand size"},
	{"id": "palette", "name": "Palette", "desc": "+1 more hand size", "needs": "brush"},
]


static func voucher_def(id: String) -> Dictionary:
	for v in VOUCHERS:
		if v.id == id:
			return v
	return {}


static func tag_def(id: String) -> Dictionary:
	for t in TAGS:
		if t.id == id:
			return t
	return {}


const SPELL_COLOR := Color("2f7f6f")
const SPELL_COST := 3


## Spells, Omens and Runes all live in the same slots. A Rune's id is
## "rune:<hand>"; its definition is built here.
static func spell_def(id: String) -> Dictionary:
	if id.begins_with("rune:"):
		var hand := id.substr(5)
		if not HAND_BASE.has(hand):
			return {}
		var b: Array = HAND_BASE[hand]
		return {"id": id, "name": hand, "desc": "Level up %s: +%d Chips, +%d Mult" % [hand, b[2], b[3]],
			"max": 0, "rune": hand}
	for s in SPELLS:
		if s.id == id:
			return s
	return {}


# Challenges: preset runs with their own rules.
# mods: money, hands, discards, hand_size, charm_slots, spell_slots
# rules: no_interest, no_hand_money, no_reward [blind idx], flipped (1 in N face
#   down), discard_cost, inflation, no_shop_charms, played_debuffed
# deck: ranks, suits, copies, enh, ed, seal
# charms: [{id, ed?, locked?}]   spells: [ids]   banned_charms / banned_hexes: [ids]
const CHALLENGES := [
	{"id": "glass_house", "name": "Glass House", "desc": "Every card in the deck is Glass. Handle with care.",
		"deck": {"enh": "glass"}},
	{"id": "low_ceiling", "name": "Low Ceiling", "desc": "Nothing above a 9 in the deck.",
		"deck": {"ranks": [2, 3, 4, 5, 6, 7, 8, 9]}, "charms": [{"id": "even", "locked": true}, {"id": "odd", "locked": true}],
		"banned_charms": ["court", "scribe"]},
	{"id": "court_only", "name": "Court Only", "desc": "Only 10s and higher, two of each.",
		"deck": {"ranks": [10, 11, 12, 13, 14], "copies": 2}, "charms": [{"id": "court", "locked": true}],
		"banned_hexes": ["mute", "mask"]},
	{"id": "blindfold", "name": "Blindfold", "desc": "Some cards are dealt face down.",
		"rules": {"flipped": 4}},
	{"id": "tightrope", "name": "Tightrope", "desc": "One hand a round, but plenty of discards - for a price.",
		"mods": {"hands": 1, "discards": 6, "money": 10}, "rules": {"discard_cost": 1}, "banned_hexes": ["needle", "drought"]},
	{"id": "short_hand", "name": "Short Hand", "desc": "A smaller hand but room for more charms.",
		"mods": {"hand_size": 6, "discards": 5, "charm_slots": 6}, "charms": [{"id": "jester"}, {"id": "snowball"}]},
	{"id": "bare_hands", "name": "Bare Hands", "desc": "No charms at all. Win with spells and runes.",
		"mods": {"charm_slots": 0, "hands": 5, "spell_slots": 3}, "rules": {"no_shop_charms": true},
		"spells": ["mirror", "etch"], "banned_hexes": ["ember", "eclipse", "jade"]},
	{"id": "austerity", "name": "Austerity", "desc": "Small and Big Blinds pay nothing, and savings earn nothing.",
		"mods": {"charm_slots": 4, "money": 8}, "rules": {"no_reward": [0, 1], "no_interest": true}},
	{"id": "inflation", "name": "Inflation", "desc": "Every purchase makes the whole shop pricier.",
		"mods": {"money": 10}, "rules": {"inflation": true}},
	{"id": "burnout", "name": "Burnout", "desc": "Every card is sealed Crimson, but played cards burn out until the next ante.",
		"deck": {"seal": "crimson"}, "rules": {"played_debuffed": true}},
	{"id": "tycoon", "name": "Tycoon", "desc": "Start rich, but leftover hands pay nothing.",
		"mods": {"money": 40}, "rules": {"no_hand_money": true}, "charms": [{"id": "treasury", "locked": true}]},
]


static func challenge_def(id: String) -> Dictionary:
	for c in CHALLENGES:
		if c.id == id:
			return c
	return {}


## Plain-language lines describing a challenge's setup.
static func challenge_lines(ch: Dictionary) -> Array:
	var out := []
	var mods: Dictionary = ch.get("mods", {})
	var labels := {"money": "Start with $%d", "hands": "%d hands per round", "discards": "%d discards per round",
		"hand_size": "Hand size %d", "charm_slots": "%d charm slots", "spell_slots": "%d spell slots"}
	for k in mods:
		out.append(labels[k] % mods[k])
	var rules: Dictionary = ch.get("rules", {})
	if rules.has("no_interest"):
		out.append("No interest")
	if rules.has("no_hand_money"):
		out.append("No money for leftover hands")
	if rules.has("no_reward"):
		out.append("No reward from " + " or ".join(rules.no_reward.map(func(i): return BLIND_NAMES[i])))
	if rules.has("flipped"):
		out.append("1 in %d cards dealt face down" % rules.flipped)
	if rules.has("discard_cost"):
		out.append("Each discard costs $%d" % rules.discard_cost)
	if rules.has("inflation"):
		out.append("Shop prices rise $1 after every purchase")
	if rules.has("no_shop_charms"):
		out.append("The shop sells no charms")
	if rules.has("played_debuffed"):
		out.append("Played cards are debuffed until the next ante")
	var deck: Dictionary = ch.get("deck", {})
	if not deck.is_empty():
		var parts := []
		if deck.has("ranks"):
			parts.append("ranks %s only" % ", ".join(deck.ranks.map(func(r): return RANK_LABELS[r])))
		if deck.get("copies", 1) > 1:
			parts.append("x%d copies" % deck.copies)
		if deck.has("enh"):
			parts.append("all " + ENHANCEMENTS[deck.enh].name)
		if deck.has("seal"):
			parts.append("all with " + SEALS[deck.seal].name)
		out.append("Deck: " + ", ".join(parts))
	if ch.has("charms"):
		out.append("Starting charms: " + ", ".join(ch.charms.map(func(c): return charm_def(c.id).name + (" (locked)" if c.get("locked", false) else ""))))
	if ch.has("spells"):
		out.append("Starting spells: " + ", ".join(ch.spells.map(func(s): return spell_def(s).name)))
	if ch.has("banned_charms"):
		out.append("Banned charms: " + ", ".join(ch.banned_charms.map(func(c): return charm_def(c).name)))
	if ch.has("banned_hexes"):
		var names := []
		for h in HEXES:
			if ch.banned_hexes.has(h.id):
				names.append(h.name)
		out.append("Banned bosses: " + ", ".join(names))
	return out


const RARITY_COLORS := [Color("4a6fa5"), Color("3f9a5a"), Color("b8334a"), Color("9b5de5")]
const RARITY_NAMES := ["Common", "Uncommon", "Rare", "Legendary"]
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
	{"id": "toll", "name": "The Toll", "desc": "Lose $1 for every card played", "mult": 2.0, "min_ante": 1, "color": Color("b5872f")},
	{"id": "shroud", "name": "The Shroud", "desc": "Your first hand is dealt face down", "mult": 2.0, "min_ante": 1, "color": Color("4d5566")},
	{"id": "shackle", "name": "The Shackle", "desc": "-1 hand size", "mult": 2.0, "min_ante": 1, "color": Color("6e6e6e")},
	{"id": "tithe", "name": "The Tithe", "desc": "Every hand must use 5 cards", "mult": 2.0, "min_ante": 1, "color": Color("9c6bb3")},
	{"id": "echo", "name": "The Echo", "desc": "Each hand type may be played only once", "mult": 2.0, "min_ante": 2, "color": Color("3f7f9e")},
	{"id": "monotone", "name": "The Monotone", "desc": "Only one hand type may be played", "mult": 2.0, "min_ante": 2, "color": Color("8a7d5b")},
	{"id": "erosion", "name": "The Erosion", "desc": "Leveled hands lose a level when played", "mult": 2.0, "min_ante": 2, "color": Color("a0603d")},
	{"id": "mask", "name": "The Mask", "desc": "Face cards are dealt face down", "mult": 2.0, "min_ante": 2, "color": Color("5d4a7a")},
	{"id": "lantern", "name": "The Lantern", "desc": "One card is always selected", "mult": 2.0, "min_ante": 3, "color": Color("3a8fb7")},
	# Showdown bosses guard ante 8 (and every 8th ante after it).
	{"id": "ember", "name": "Ember Crown", "desc": "A random charm is disabled every hand", "mult": 2.0, "min_ante": 8, "showdown": true, "color": Color("d9572b")},
	{"id": "jade", "name": "Jade Wreath", "desc": "All cards are debuffed until a charm is sold", "mult": 2.0, "min_ante": 8, "showdown": true, "color": Color("2f9e6e")},
	{"id": "abyss", "name": "Violet Abyss", "desc": "Enormous blind", "mult": 6.0, "min_ante": 8, "showdown": true, "color": Color("7a3fc2")},
	{"id": "eclipse", "name": "Gilded Eclipse", "desc": "Charms are flipped face down and shuffled", "mult": 2.0, "min_ante": 8, "showdown": true, "color": Color("c9a227")},
]


static func ante_target(ante: int) -> int:
	if ante <= FINAL_ANTE:
		return ANTE_BASE[ante - 1]
	var raw := float(ANTE_BASE[FINAL_ANTE - 1]) * pow(1.75, ante - FINAL_ANTE)
	var mag := pow(10.0, floor(log(raw) / log(10.0)) - 1)
	return int(floor(raw / mag) * mag)


static func card_name(card: Dictionary) -> String:
	var names := {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
	return "%s of %s" % [names.get(card.rank, str(card.rank)), SUIT_NAMES[card.suit]]


## Lines describing a card's upgrades, for tooltips and the shop.
static func card_mods(card: Dictionary) -> Array:
	var out := []
	if card.get("enh", "") != "":
		var e: Dictionary = ENHANCEMENTS[card.enh]
		out.append("%s: %s" % [e.name, e.desc])
	if card.get("ed", "") != "":
		var d: Dictionary = EDITIONS[card.ed]
		out.append("%s: %s" % [d.name, d.desc])
	if card.get("seal", "") != "":
		var sl: Dictionary = SEALS[card.seal]
		out.append("%s: %s" % [sl.name, sl.desc])
	if card.get("bonus", 0) > 0:
		out.append("+%d bonus Chips" % card.bonus)
	return out


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
