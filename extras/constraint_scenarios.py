#!/usr/bin/env python3
"""
Constraint Game - Historical Scenario Database
Part of the C2A Training System

Provides 100 historical scenarios organized by difficulty level
for training constraint recognition and transmutation skills.
"""

# The 7 Constraint Archetypes
CONSTRAINT_ARCHETYPES = {
    "resource_scarcity": "Not enough X to achieve Y",
    "information_asymmetry": "Missing critical data for decision",
    "commitment_lock": "Past choices limit current options",
    "coordination_failure": "Can't get group to cooperate",
    "temporal_pressure": "Running out of time",
    "social_trust": "Others don't believe/trust/follow you",
    "self_imposed": "Your own psychology limits action"
}

# Scenario Database
# Levels 1-10: Explicit constraints (pure transmutation training)
# Levels 11-20: Slightly hidden constraints (requires analysis)

SCENARIOS = {
    1: {
        "title": "Apollo 13 - The CO2 Crisis",
        "year": 1970,
        "domain": "Engineering",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are Gene Kranz, NASA Flight Director, April 1970.

Apollo 13's oxygen tank has exploded 200,000 miles from Earth.
The crew has abandoned the damaged Command Module.
They're now in the Lunar Module (LM) designed for 2 people for 45 hours.
Problem: 3 people must survive for 4 days (96 hours).

THE CONSTRAINT: The LM's CO2 scrubbers are becoming saturated.
Within 8 hours, carbon dioxide will reach lethal levels.
You have spare scrubbers from the Command Module, BUT:
- Command Module scrubbers are SQUARE
- Lunar Module receptacles are ROUND
They are physically incompatible.

Available materials: Duct tape, plastic bags, cardboard, hoses, socks.
""",
        "explicit_constraint": "Square scrubbers won't fit in round holes",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Prevent CO2 poisoning and get crew home alive",
        "historical_outcome": "NASA engineers built an adapter using only materials available on the spacecraft. They radioed step-by-step instructions. The adapter worked. All three astronauts survived.",
        "transmutation_keywords": ["adapter", "duct tape", "combine", "modify", "improvise", "materials on hand"],
        "hint": "You have incompatible parts. Can you make them compatible with what's available?",
        "target_transmutations": 1,
        "constraint_logic_pattern": "CONVERSION/ADAPTATION: When two incompatible systems must work together, build an adapter/converter using available resources. The constraint (incompatibility) becomes the design specification."
    },
    
    2: {
        "title": "The Berlin Airlift - Feeding a City",
        "year": 1948,
        "domain": "Logistics",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are General Lucius Clay, U.S. Military Governor of Germany, June 1948.

The Soviet Union has blockaded all ground routes into West Berlin.
2.5 million civilians are trapped with no food, coal, or supplies.
You have only one option: Airlift supplies by plane.

THE CONSTRAINT: West Berlin needs 4,500 tons of supplies per day to survive.
Your largest cargo plane (C-54) carries only 10 tons.
That means 450 flights per day, landing at Tempelhof Airport.
The airport has only ONE runway.
Planes can land maybe 20-30 times per day maximum.

The math doesn't work. You can't physically deliver enough supplies.
""",
        "explicit_constraint": "Not enough flights possible to meet daily supply needs",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Feed 2.5 million people without ground access",
        "historical_outcome": "Operation Vittles: Streamlined operations to land a plane every 30 seconds. Built 2 new airports. Flew for 15 months straight. Delivered 2.3 million tons. Stalin lifted blockade.",
        "transmutation_keywords": ["efficiency", "streamline", "build", "optimize", "schedule", "multiple", "continuous"],
        "hint": "Can you increase throughput by changing the process rather than the planes?",
        "target_transmutations": 1
    },
    
    3: {
        "title": "Singapore's Water Crisis - Vulnerability to Malaysia",
        "year": 1965,
        "domain": "Geopolitics",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are Lee Kuan Yew, Prime Minister of Singapore, 1965.

Singapore just gained independence (kicked out of Malaysia).
You are a tiny island city-state with no natural resources.

THE CONSTRAINT: Singapore has NO fresh water.
100% of your water comes from Malaysia via pipeline.
Malaysia can (and has threatened to) turn off the tap at any time.
Your entire country is hostage to your neighbor's goodwill.

You need water independence, but you have:
- No rivers
- No lakes
- Limited rainfall
- Small land area (no room for large reservoirs)
""",
        "explicit_constraint": "No natural water sources, dependent on hostile neighbor",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Achieve water independence",
        "historical_outcome": "Built desalination plants, water recycling (NEWater), rainwater collection, strict conservation. Today Singapore is water self-sufficient and EXPORTS water technology.",
        "transmutation_keywords": ["desalination", "recycle", "technology", "collection", "efficiency", "alternative source"],
        "hint": "If natural sources don't exist, can you create artificial ones?",
        "target_transmutations": 1,
        "constraint_logic_pattern": "RESOURCE CONVERSION: When natural Resource X doesn't exist, convert abundant Resource Y into X through technology. (Salt water → Fresh water, Wastewater → Clean water). The constraint (no natural source) forces innovation in conversion technology."
    },
    
    4: {
        "title": "The Bletchley Park Codebreakers - Too Much Data",
        "year": 1941,
        "domain": "Intelligence",
        "difficulty": "Beginner",
        "constraint_type": "information_asymmetry",
        "situation": """You are Alan Turing at Bletchley Park, 1941.

You've partially cracked the German Enigma code.
Every day, you intercept thousands of encrypted German messages.

THE CONSTRAINT: The Enigma machine has 159 quintillion possible settings.
Each message uses a different daily setting.
By the time you decrypt a message by hand (12-24 hours), the intelligence is useless.
You need to decrypt messages in MINUTES, not hours.

Human mathematicians can't work fast enough.
""",
        "explicit_constraint": "Decryption takes too long - intelligence becomes stale",
        "constraint_archetype": "temporal_pressure",
        "success_criteria": "Decrypt German messages in real-time",
        "historical_outcome": "Turing built the 'Bombe' - an electromechanical computer that tested thousands of settings per second. Reduced decryption time from hours to minutes. Shortened the war by 2+ years.",
        "transmutation_keywords": ["automate", "machine", "computer", "parallel", "speed", "mechanical"],
        "hint": "If humans are too slow, what else can process information?",
        "target_transmutations": 1
    },
    
    5: {
        "title": "Edison's Light Bulb - The Filament Problem",
        "year": 1879,
        "domain": "Invention",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are Thomas Edison, 1879.

You're trying to invent a practical electric light bulb.
The concept works: Heat a filament until it glows.

THE CONSTRAINT: Every filament material burns out in minutes or hours.
- Platinum: Too expensive ($500/bulb)
- Carbon rods: Burn up in 15 minutes
- Copper wire: Melts immediately

You've tested 3,000+ materials. All fail.
You need a filament that lasts 1,000+ hours AND is affordable.
No known material has both properties.
""",
        "explicit_constraint": "No material is both long-lasting AND affordable",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Create a practical, affordable light bulb",
        "historical_outcome": "Edison carbonized bamboo fiber - created ultra-thin carbon filament. Lasted 1,200 hours. Cost pennies. This constraint (need for better filament) drove decades of materials science innovation.",
        "transmutation_keywords": ["bamboo", "carbonize", "thin", "alternative material", "process", "treatment"],
        "hint": "Can you TRANSFORM a cheap material rather than finding an expensive one?",
        "target_transmutations": 1
    },
    
    6: {
        "title": "The Manhattan Project - Isotope Separation",
        "year": 1943,
        "domain": "Physics",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are J. Robert Oppenheimer, 1943.

You're building the atomic bomb.
You need Uranium-235 (the rare isotope that undergoes fission).

THE CONSTRAINT: U-235 is 0.7% of natural uranium (99.3% is useless U-238).
The two isotopes are chemically IDENTICAL (same element).
You can't separate them by chemical means.
They differ by only 3 neutrons (mass difference: 1.3%).

You need kilograms of pure U-235.
No separation method exists at industrial scale.
""",
        "explicit_constraint": "Can't chemically separate nearly-identical isotopes",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Obtain enough pure U-235 for a bomb",
        "historical_outcome": "Used multiple methods in parallel: Gas diffusion (exploiting tiny mass difference), electromagnetic separation, thermal diffusion. Built Oak Ridge facility. Separated enough U-235 in 2 years.",
        "transmutation_keywords": ["multiple methods", "parallel", "mass difference", "physical separation", "scale"],
        "hint": "If one method is too slow, can you run multiple methods simultaneously?",
        "target_transmutations": 1,
        "constraint_logic_pattern": "PARALLEL EXECUTION: When one method is too slow to meet deadline, run multiple different methods simultaneously. Even if each is individually slow, combined output reaches goal. The constraint (time pressure) forces portfolio approach rather than single solution."
    },
    
    7: {
        "title": "The Polio Vaccine - Testing Dilemma",
        "year": 1954,
        "domain": "Medicine",
        "difficulty": "Beginner",
        "constraint_type": "coordination_failure",
        "situation": """You are Jonas Salk, 1954.

You've developed a polio vaccine.
Polio is crippling 20,000 children per year in the U.S.

THE CONSTRAINT: You need to test if the vaccine works.
This requires:
- 1 million children in the trial
- Half get vaccine, half get placebo (to compare)
- Follow them for a year

Problem: Parents don't want their kids getting placebo (no protection).
Health officials are terrified of vaccine side effects (lawsuits).
One bad reaction and the whole program shuts down.

How do you convince a million families to participate?
""",
        "explicit_constraint": "Need massive trial, but parents fear placebo/side effects",
        "constraint_archetype": "social_trust",
        "success_criteria": "Conduct largest medical trial in history",
        "historical_outcome": "Positioned it as civic duty ('Polio Pioneers'). Media campaign made kids heroes. 1.8 million children participated. Vaccine worked. Polio cases dropped 99%.",
        "transmutation_keywords": ["heroes", "civic duty", "volunteers", "media", "social campaign", "narrative"],
        "hint": "Can you change the MEANING of participation from 'risk' to 'heroism'?",
        "target_transmutations": 1
    },
    
    8: {
        "title": "The Dyson Vacuum - Bagless Design",
        "year": 1983,
        "domain": "Engineering",
        "difficulty": "Beginner",
        "constraint_type": "resource_scarcity",
        "situation": """You are James Dyson, 1983.

You're frustrated with vacuum cleaners that lose suction as bags fill.
Every vacuum on the market uses bags that clog with dust.

THE CONSTRAINT: Bags are the business model.
- Vacuum companies make MORE money selling replacement bags than vacuums
- A bagless vacuum threatens their revenue stream
- No manufacturer will license your design

You need to manufacture it yourself, but you have:
- No factory
- No distribution network
- No brand recognition
- Big vacuum companies will undercut you
""",
        "explicit_constraint": "Industry won't adopt your design (threatens their bag revenue)",
        "constraint_archetype": "coordination_failure",
        "success_criteria": "Bring bagless vacuum to market",
        "historical_outcome": "Built own factory. Sold direct to consumers. Marketed the CONSTRAINT as advantage ('No bags = no loss of suction'). Dyson became billion-dollar company. Forced industry to follow.",
        "transmutation_keywords": ["direct", "own factory", "market constraint", "advantage", "vertical integration"],
        "hint": "If the industry won't help you, can you become the industry?",
        "target_transmutations": 1
    },
    
    9: {
        "title": "The Wright Brothers - Control Problem",
        "year": 1902,
        "domain": "Aviation",
        "difficulty": "Beginner",
        "constraint_type": "information_asymmetry",
        "situation": """You are Wilbur Wright, 1902.

You're trying to build a controllable aircraft.
Everyone else is focused on ENGINE POWER.

THE CONSTRAINT: You've realized the real problem isn't power - it's CONTROL.
Birds don't just flap harder to turn - they twist their wings.
You need 3-axis control (pitch, roll, yaw).

But: Aircraft wings are rigid structures.
How do you make a wing twist while maintaining strength?
No one has solved this.
""",
        "explicit_constraint": "Need flexible wing control without sacrificing structural integrity",
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Achieve controlled, sustained flight",
        "historical_outcome": "Wing warping - used cables to twist entire wing structure. Combined with movable rudder. First controlled flight Dec 1903. Flew while others with bigger engines crashed.",
        "transmutation_keywords": ["wing warping", "cables", "twist", "3-axis", "control system", "flexible"],
        "hint": "Can the ENTIRE structure flex, rather than adding separate control surfaces?",
        "target_transmutations": 1
    },
    
    10: {
        "title": "Netflix vs Blockbuster - The Late Fee Problem",
        "year": 1997,
        "domain": "Business",
        "difficulty": "Beginner",
        "constraint_type": "social_trust",
        "situation": """You are Reed Hastings, 1997.

You just paid a $40 late fee at Blockbuster for 'Apollo 13'.
You're furious. This is a terrible customer experience.

THE CONSTRAINT: Blockbuster's business model REQUIRES late fees.
- Late fees = 16% of Blockbuster's revenue ($800M/year)
- Without them, people would rent movies and never return them
- But customers HATE late fees

You want to start a rental business without late fees.
But how do you prevent people from keeping movies forever?
""",
        "explicit_constraint": "Need rentals without late fees, but must ensure returns",
        "constraint_archetype": "coordination_failure",
        "success_criteria": "Build rental service without late fees",
        "historical_outcome": "Netflix subscription model: Unlimited rentals, no due dates, just return to get next one. The constraint (wanting the next movie) became the incentive to return. Blockbuster bankrupt by 2010.",
        "transmutation_keywords": ["subscription", "unlimited", "queue", "next movie", "incentive", "self-regulating"],
        "hint": "Can customer DESIRE (wanting the next movie) replace the penalty system?",
        "target_transmutations": 1
    },
    
    # Levels 11-20: Hidden constraints - User must identify the constraint first
    
    11: {
        "title": "Apple 1997 - Near Bankruptcy",
        "year": 1997,
        "domain": "Business",
        "difficulty": "Intermediate",
        "constraint_type": "commitment_lock",
        "situation": """You are Steve Jobs, returning to Apple as CEO in 1997.

Apple is in crisis:
- Losing $1 billion per year
- Market share dropped from 16% to 4%
- Stock price at all-time low
- 50+ different product lines (Performa, PowerBook, Newton, Pippin, etc.)
- Microsoft dominates with 95% market share
- Michael Dell says Apple should "shut down and give money back to shareholders"

You have 90 days to stop the bleeding or Apple dies.

What do you do?
""",
        "explicit_constraint": None,  # User must identify
        "constraint_archetype": "commitment_lock",
        "success_criteria": "Return to profitability within 1 year",
        "historical_outcome": "Jobs killed 47 product lines, focused on 4 (Professional/Consumer × Desktop/Portable matrix). Returned to profitability in 1998. This simplification enabled the iPod, iPhone, iPad innovations later.",
        "transmutation_keywords": ["simplify", "focus", "kill products", "matrix", "core", "essential"],
        "hint": "What is the REAL constraint here? (Hint: It's not 'lack of money')",
        "correct_constraint": "Too many products = resource drain + decision paralysis",
        "target_transmutations": 2
    },
    
    12: {
        "title": "Churchill 1940 - Britain Stands Alone",
        "year": 1940,
        "domain": "Leadership",
        "difficulty": "Intermediate",
        "constraint_type": "social_trust",
        "situation": """You are Winston Churchill, Prime Minister of Britain, May 1940.

France has just fallen to Nazi Germany.
Your situation:
- The entire British Army just evacuated from Dunkirk (left all equipment behind)
- You have no allies (France defeated, Soviet Union allied with Hitler, U.S. neutral)
- Hitler controls all of Western Europe
- German invasion expected within weeks
- Many in your own cabinet want to negotiate peace

Your military advisors say Britain cannot win.
Your people are terrified.
Some politicians are calling for surrender negotiations.

What do you do?
""",
        "explicit_constraint": None,
        "constraint_archetype": "social_trust",
        "success_criteria": "Maintain British resistance",
        "historical_outcome": "Churchill's speeches reframed the constraint: 'We shall fight on the beaches... we shall never surrender.' Turned morale crisis into determination. Britain held out, eventually bringing in US/Soviet allies. Won the war.",
        "transmutation_keywords": ["morale", "speech", "narrative", "determination", "reframe", "hope"],
        "hint": "The military situation is bad, but what's the PSYCHOLOGICAL constraint?",
        "correct_constraint": "Loss of hope/will to fight (morale collapse)",
        "target_transmutations": 2
    },
    
    13: {
        "title": "SpaceX Falcon 1 - Three Failures",
        "year": 2008,
        "domain": "Aerospace",
        "difficulty": "Intermediate",
        "constraint_type": "temporal_pressure",
        "situation": """You are Elon Musk, CEO of SpaceX, September 2008.

Your situation:
- You've had THREE failed rocket launches in a row
- Each failure cost $60-90 million
- You're nearly out of money (one launch attempt left)
- Your competitors are laughing (rockets are 'too hard' for private companies)
- Your employees are demoralized
- NASA is watching (they might give you a contract, but only if you succeed)

You have ONE more rocket ready: Falcon 1 Flight 4.
If this fails, SpaceX is bankrupt.
If it succeeds, you might get the NASA contract.

What's your constraint and how do you transmute it?
""",
        "explicit_constraint": None,
        "constraint_archetype": "temporal_pressure",
        "success_criteria": "Successful orbit or bankruptcy",
        "historical_outcome": "Flight 4 succeeded (first private liquid-fuel rocket to orbit). NASA awarded $1.6B contract 2 months later. Constraint (one last chance) created radical focus. SpaceX now dominates launch market.",
        "transmutation_keywords": ["focus", "all-in", "stakes", "determination", "last chance"],
        "hint": "It's not just 'running out of money' - what does the DEADLINE create?",
        "correct_constraint": "Ultimate pressure creates ultimate focus (do-or-die clarity)",
        "target_transmutations": 2
    },
    
    14: {
        "title": "The Printing Press - Gutenberg's Debt Crisis",
        "year": 1450,
        "domain": "Technology",
        "difficulty": "Intermediate",
        "constraint_type": "resource_scarcity",
        "situation": """You are Johannes Gutenberg, 1450.

You've invented movable type printing.
Before you: Books are copied by hand (6 months per book, costs a fortune).
With your press: Books can be printed in days.

Your constraint:
- You need MONEY to build the press and print the first Bible
- You borrowed heavily from Johann Fust (a wealthy merchant)
- The loan is due, but you haven't finished printing yet
- Fust is threatening to seize your press
- Handwritten Bibles sell for 30 florins (1 year wages)
- You need to print 180 copies to break even

How do you make printing economically viable before Fust takes everything?
""",
        "explicit_constraint": None,
        "constraint_archetype": "temporal_pressure",
        "success_criteria": "Make printing press economically viable",
        "historical_outcome": "Gutenberg printed 180 Bibles. Sold for 30 florins each (same as handwritten). But production cost dropped 80%. This margin enabled mass production. Lost the press to Fust in lawsuit, but the technology spread. Changed human civilization.",
        "transmutation_keywords": ["volume", "scale", "efficiency", "margin", "mass production"],
        "hint": "The constraint isn't 'lack of money' - what economic principle does printing enable?",
        "correct_constraint": "High fixed cost / low marginal cost = need volume/scale",
        "target_transmutations": 2
    },
    
    15: {
        "title": "Linux vs Microsoft - The Free Software Paradox",
        "year": 1991,
        "domain": "Software",
        "difficulty": "Intermediate",
        "constraint_type": "coordination_failure",
        "situation": """You are Linus Torvalds, 1991.

You've created a free operating system (Linux).
You're competing against Microsoft Windows.

Your constraints:
- You have NO money (student project)
- Microsoft has billions in revenue
- Microsoft has thousands of engineers
- You're one person
- Software requires constant updates, bug fixes, new features
- Users expect professional support

How can a FREE operating system compete with a billion-dollar company?
""",
        "explicit_constraint": None,
        "constraint_archetype": "coordination_failure",
        "success_criteria": "Build competitive OS with no budget",
        "historical_outcome": "Made it open source. Turned users into developers. Thousands of volunteers contributed code. Created better OS than Microsoft for free. Today Linux runs 90% of cloud servers, all Android phones. The constraint (no money for engineers) became the advantage (infinite free engineers).",
        "transmutation_keywords": ["open source", "community", "volunteers", "distributed", "collaboration"],
        "hint": "What if your constraint (no engineers) could become your advantage?",
        "correct_constraint": "No paid engineers / Need infinite labor",
        "target_transmutations": 2
    },
    
    16: {
        "title": "Airbnb 2008 - Running Out of Money",
        "year": 2008,
        "domain": "Startup",
        "difficulty": "Intermediate",
        "constraint_type": "resource_scarcity",
        "situation": """You are Brian Chesky, Airbnb co-founder, 2008.

Your situation:
- You have a website where people rent out air mattresses in their homes
- You have $200 left in the bank
- Revenue is $200/week
- You need $40,000 for rent, food, servers
- No investors are interested ('Who wants to sleep on strangers' air mattresses?')
- The 2008 financial crisis just hit (worst time to fundraise)
- Democratic National Convention coming to Denver (hotels fully booked)

You have 2 weeks before you're bankrupt.
What do you do?
""",
        "explicit_constraint": None,
        "constraint_archetype": "temporal_pressure",
        "success_criteria": "Generate $40,000 in 2 weeks",
        "historical_outcome": "Created 'Obama O's' and 'Cap'n McCain's' cereals (political satire). Sold 800 boxes at $40 each. Made $30,000. This bought them time to get into Y Combinator. Airbnb now worth $75 billion. The constraint (imminent bankruptcy) forced creative thinking beyond the core product.",
        "transmutation_keywords": ["creative", "outside", "lateral", "merchandise", "event", "political"],
        "hint": "The constraint is time/money. Can you solve it WITHOUT your main product?",
        "correct_constraint": "Need cash NOW (can't wait for product to scale)",
        "target_transmutations": 2
    },
    
    17: {
        "title": "The Suez Canal - Ferdinand de Lesseps",
        "year": 1859,
        "domain": "Engineering",
        "difficulty": "Intermediate",
        "constraint_type": "information_asymmetry",
        "situation": """You are Ferdinand de Lesseps, 1859.

You want to build a canal connecting the Mediterranean to the Red Sea.
This would cut 7,000 km off the Europe-Asia shipping route.

Your constraints:
- The Suez isthmus is 120 km wide
- It's mostly desert (120°F heat, no water)
- You need to move 75 million cubic meters of sand
- British engineers say it's impossible (they rejected the project)
- Their reason: The Red Sea is 30 feet HIGHER than the Mediterranean
  (Building a canal would cause catastrophic flooding)
- The British have built canals before (they know what they're talking about)

Do you believe them? What's the actual constraint?
""",
        "explicit_constraint": None,
        "constraint_archetype": "information_asymmetry",
        "success_criteria": "Build canal without flooding",
        "historical_outcome": "De Lesseps commissioned independent survey. Found British measurements WRONG - the seas are at the same level. Built the canal. It opened in 1869 and revolutionized global trade. The constraint was FALSE INFORMATION, not physical reality.",
        "transmutation_keywords": ["verify", "measure", "independent", "survey", "assumptions", "data"],
        "hint": "What if the constraint itself is FALSE? How would you check?",
        "correct_constraint": "False information presented as fact",
        "target_transmutations": 2
    },
    
    18: {
        "title": "Toyota Production System - The Space Constraint",
        "year": 1950,
        "domain": "Manufacturing",
        "difficulty": "Intermediate",
        "constraint_type": "resource_scarcity",
        "situation": """You are Taiichi Ohno, Toyota engineer, 1950.

You're trying to compete with American car manufacturers.

Your constraints compared to Ford/GM:
- Toyota's factory is 1/10th the size
- You have 1/100th the capital for inventory
- American factories stock months of parts (buffer against delays)
- You can only afford a few days of inventory
- Any supply disruption stops your production line
- American factories are more efficient by every metric

How can you manufacture cars with almost no inventory space?
""",
        "explicit_constraint": None,
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Build competitive manufacturing system with minimal space/inventory",
        "historical_outcome": "Created Just-In-Time (JIT) manufacturing. Parts arrive exactly when needed. No warehouse needed. This constraint forced elimination of waste. Toyota Production System became the MOST efficient in the world. Now taught globally as 'Lean Manufacturing'.",
        "transmutation_keywords": ["just-in-time", "flow", "waste", "efficiency", "pull", "kanban"],
        "hint": "What if having NO space forced you to eliminate something American factories waste?",
        "correct_constraint": "No space for inventory storage",
        "target_transmutations": 2
    },
    
    19: {
        "title": "Spotify vs iTunes - The Piracy Problem",
        "year": 2006,
        "domain": "Business",
        "difficulty": "Intermediate",
        "constraint_type": "coordination_failure",
        "situation": """You are Daniel Ek, founder of Spotify, 2006.

The music industry is dying:
- Napster/BitTorrent have trained users that music is FREE
- iTunes charges $0.99/song (people still pirate)
- CD sales collapsed 50%
- Music labels are suing their own customers
- Labels hate technology companies

Your constraints:
- Users won't pay for music (they can pirate for free)
- Labels won't license to you (they've been burned by piracy)
- You need BOTH users AND labels to agree
- But their incentives are opposite

How do you make BOTH sides say yes?
""",
        "explicit_constraint": None,
        "constraint_archetype": "coordination_failure",
        "success_criteria": "Get users to pay and labels to license",
        "historical_outcome": "Spotify: Unlimited streaming for $10/month. Cheaper than buying 10 songs, but labels get paid per play. Freemium model (ads) converted pirates to paying users. Both sides won. Music industry recovered. Now streaming is 67% of music revenue.",
        "transmutation_keywords": ["streaming", "subscription", "unlimited", "freemium", "align incentives"],
        "hint": "Can you change the MODEL so both sides get what they want?",
        "correct_constraint": "Misaligned incentives between users and labels",
        "target_transmutations": 2
    },
    
    20: {
        "title": "The Green Revolution - Feeding India",
        "year": 1961,
        "domain": "Agriculture",
        "difficulty": "Intermediate",
        "constraint_type": "resource_scarcity",
        "situation": """You are Norman Borlaug, agricultural scientist, 1961.

India is facing massive famine:
- Population: 450 million (growing fast)
- Food production: Stagnant for 50 years
- Imports: Can't afford enough to feed everyone
- Land: Already farming all arable land (can't expand)
- Traditional wheat yields: 800 kg/hectare
- Prediction: 100 million will starve in the next decade

Your constraints:
- Can't get more farmland
- Can't import enough food
- Farmers are too poor for expensive solutions
- Traditional methods have hit a ceiling

How do you feed India without more land or money?
""",
        "explicit_constraint": None,
        "constraint_archetype": "resource_scarcity",
        "success_criteria": "Increase food production without more land",
        "historical_outcome": "Bred dwarf wheat varieties (shorter stems = more energy to grain). Yields jumped to 3,000 kg/hectare (4x increase). Combined with fertilizer and irrigation. India became food self-sufficient. Saved 1+ billion lives. Borlaug won Nobel Peace Prize.",
        "transmutation_keywords": ["breeding", "genetics", "yield", "efficiency", "dwarf", "intensive"],
        "hint": "If you can't get MORE land, can you get more OUTPUT from existing land?",
        "correct_constraint": "Fixed land area / Need more food per acre",
        "target_transmutations": 2
    }
}


def get_scenario(level, session_count=0, used_scenarios=None):
    """
    Get the appropriate scenario for the user's current level
    Prevents repeats and provides proper progression
    
    Args:
        level: User's current level (1-100)
        session_count: Total number of sessions completed
        used_scenarios: Set of scenario IDs already seen (optional)
    
    Returns:
        Scenario dictionary
    """
    import random
    
    # Determine which scenarios are available based on level
    if level <= 10:
        # Levels 1-10: Only explicit constraint scenarios (1-10)
        available = list(range(1, 11))
    elif level <= 20:
        # Levels 11-20: Mix of explicit and hidden constraints
        available = list(range(1, 21))
    else:
        # Levels 21+: All scenarios available, cycle through
        available = list(range(1, 21))
    
    # Remove already-used scenarios if provided
    if used_scenarios:
        available = [s for s in available if s not in used_scenarios]
        
        # If all scenarios have been used, reset
        if not available:
            available = list(range(1, min(level, 20) + 1))
    
    # Select scenario based on session count (deterministic but varied)
    # This ensures you cycle through all scenarios before repeating
    if available:
        # Use session_count to cycle through scenarios in order
        scenario_num = available[session_count % len(available)]
    else:
        scenario_num = 1  # Fallback
    
    return SCENARIOS.get(scenario_num, SCENARIOS[1])


def validate_constraint_identification(user_constraint, scenario):
    """
    Validate if user correctly identified the constraint in hidden-constraint scenarios
    Returns: (is_correct, feedback)
    """
    if scenario.get("explicit_constraint"):
        # Explicit constraint scenario - no identification needed
        return True, "Constraint provided"
    
    correct = scenario.get("correct_constraint", "")
    user_lower = user_constraint.lower()
    
    # Check if user's identification matches the correct constraint archetype
    archetype = scenario["constraint_archetype"]
    archetype_description = CONSTRAINT_ARCHETYPES.get(archetype, "")
    
    # Keyword matching for validation
    if archetype == "commitment_lock" and any(word in user_lower for word in ["too many", "complexity", "focus", "spread thin", "product line"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    elif archetype == "social_trust" and any(word in user_lower for word in ["morale", "hope", "will", "fear", "belief", "trust"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    elif archetype == "temporal_pressure" and any(word in user_lower for word in ["time", "deadline", "last chance", "urgency", "pressure"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    elif archetype == "resource_scarcity" and any(word in user_lower for word in ["space", "inventory", "land", "money", "capital", "resource"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    elif archetype == "coordination_failure" and any(word in user_lower for word in ["incentive", "align", "cooperat", "both sides", "conflict"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    elif archetype == "information_asymmetry" and any(word in user_lower for word in ["false", "wrong", "assumption", "data", "information", "know"]):
        return True, f"✓ Correct! This is a '{archetype}' constraint: {correct}"
    else:
        return False, f"✗ Not quite. The actual constraint was: {correct}\n   This is a '{archetype}' pattern: {archetype_description}"


def score_transmutation(transmutation, scenario):
    """
    Score a transmutation based on CONSTRAINT LOGIC PATTERNS (not domain trivia)
    Returns: (score 0-100, feedback breakdown)
    """
    trans_lower = transmutation.lower()
    
    # ===== CONSTRAINT LOGIC PATTERNS (60 points) =====
    # These are transferable patterns that work across domains
    
    logic_patterns = {
        # Parallel/Multiple approaches
        "parallel_execution": ["multiple", "parallel", "simultaneously", "at the same time", "several", "both", "all", "various"],
        
        # Conversion/Transformation
        "conversion": ["convert", "transform", "turn into", "change", "process", "adapt", "modify", "recycle"],
        
        # Resource substitution
        "substitution": ["alternative", "substitute", "replace", "instead", "different", "other", "elsewhere"],
        
        # Leverage constraints as advantages  
        "leverage": ["leverage", "exploit", "use", "advantage", "benefit", "capitalize", "harness"],
        
        # Scale/Volume approaches
        "scale": ["scale", "volume", "mass", "industrial", "large", "many", "increase"],
        
        # Systematic/Process thinking
        "systematic": ["system", "process", "method", "approach", "strategy", "framework", "structure"],
        
        # Iteration/Testing
        "iteration": ["test", "try", "experiment", "iterate", "refine", "improve", "trial"]
    }
    
    logic_score = 0
    patterns_found = []
    
    for pattern_name, keywords in logic_patterns.items():
        if any(keyword in trans_lower for keyword in keywords):
            logic_score += 10
            patterns_found.append(pattern_name)
    
    logic_score = min(logic_score, 60)  # Cap at 60 points
    
    # ===== REASONING QUALITY (30 points) =====
    reasoning_score = 0
    
    # Check for causal reasoning (because/since/therefore)
    causal_words = ["because", "since", "therefore", "thus", "so", "as a result", "which means"]
    has_reasoning = any(word in trans_lower for word in causal_words)
    if has_reasoning:
        reasoning_score += 10
    
    # Check for specificity (numbers, examples, details)
    has_specifics = any(char.isdigit() for char in transmutation) or len(transmutation.split()) > 20
    if has_specifics:
        reasoning_score += 10
    
    # Check for understanding of constraint mechanism
    constraint_keywords = scenario.get("transmutation_keywords", [])
    domain_matches = sum(1 for kw in constraint_keywords if kw in trans_lower)
    if domain_matches >= 1:
        reasoning_score += 10  # Bonus for domain knowledge, but not required
    
    reasoning_score = min(reasoning_score, 30)
    
    # ===== ACTIONABILITY (10 points) =====
    action_verbs = ["build", "create", "develop", "implement", "design", "use", "make", "establish", "run", "operate"]
    action_score = 10 if any(verb in trans_lower for verb in action_verbs) else 0
    
    # ===== TOTAL SCORE =====
    total = logic_score + reasoning_score + action_score
    
    # ===== FEEDBACK =====
    feedback = {
        "score": total,
        "logic_score": logic_score,
        "reasoning_score": reasoning_score,
        "action_score": action_score,
        "patterns_found": patterns_found,
        "breakdown": f"Logic: {logic_score}/60 | Reasoning: {reasoning_score}/30 | Action: {action_score}/10"
    }
    
    return total, feedback

