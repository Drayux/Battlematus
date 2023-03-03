import scipy.stats
import enum
import json
import matplotlib.pyplot
import numpy
import sys

# Tuple data path / min damage
global spells
spells = [
    ("data/krok/firecat.dat", 80),
    ("data/krok/frostbeetle.dat", 65),
    ("data/krok/thundersnake.dat", 105),
    ("data/krok/imp.dat", 65),
    ("data/krok/darksprite.dat", 65),
    ("data/krok/bloodbat.dat", 70),
    ("data/krok/scarab.dat", 65)
]

# API for Welford's one-pass equations
# Partially pulled from a CS423 project
class DataHandler:
    def __init__(self, name = "Welford"):
        self.name = name
        self.avg = 0.0       # Distribution mean
        self.var = 0.0       # Progressive, needs to be divided by n
        self.i = 0           # Number of elements added to the Welford object

        self.min = 0
        self.max = 1
        self.data = []

    def __str__(self):
        return f"{self.name}:\n\tx̄ = {self.avg}\n\tstd = {self.std()}\n\ti = {self.i}"

    def insert(self, x):
        try: x = float(x)
        except ValueError: return

        # Save the data in the local array
        if self.i == 0:
            self.min = x
            self.max = x
        else: self.min, self.max = min(x, self.min), max(x, self.max)

        self.data.append(x)

        # Update the statistics using welford's equations
        self.i += 1
        avg = self.avg + ((x - self.avg) / self.i)
        var = self.var + ((x - self.avg) * (x - avg))
        # var = self.var + ((self.i - 1) * ((x - self.avg) ** 2) / self.i)

        self.avg = avg
        self.var = var

    def mean(self):
        return self.avg

    def variance(self):
        return ((self.var / self.i) if self.i > 0 else 0)

    def std(self):
        return self.variance() ** 0.5

    # Get the category labels and counts as a tuple
    def categories(self):
        # Come up with a better way of doing this maybe?
        tmp = {}
        for x in self.data:
            try: tmp[x] += 1
            except KeyError: tmp[x] = 1
        # print(counts)

        # labels = [str(x) for x in list(tmp.keys())]
        labels = list(tmp.keys())
        counts = [tmp[x] for x in tmp]

        return (labels, counts)

    def plot(self):
        # The game only deals base damage here in multiples of 5
        # Thunder snake: 105 - 145

        # Plot a histogram instead
        # counts, bins = numpy.histogram(self.data)
        # matplotlib.pyplot.stairs(counts, bins)
        # matplotlib.pyplot.hist(bins[:-1], bins, weights=counts)
        # return

        labels, counts = self.categories()

        matplotlib.pyplot.bar(labels, counts)
        matplotlib.pyplot.show()

class Outcome(enum.Enum):
    PASS = 0
    FIZZLE = 1
    DAMAGE = 2

def parse(path):
    raw = "["
    with open(path, 'r') as data:
        raw += str(data.read())

    raw = raw.strip()[:-1] + "]"
    return json.loads(raw)

# Normalize damage ranges to an index on the damage scale
# Currently assumes interval of 10
def normalize(data, base):
    dataNormalized = []
    for x in data: dataNormalized.append(1 + (x - base) / 10)
    return dataNormalized

# Take the state before and the state after and use this to determine the outcome of the round
# This might not be the most practial way to handle this, but it's definitely the easiest to follow right now
# Currently returns a metric on damage dealt to opponent
# Formatted as tuple of (TYPE, value)
def extractRound(before, after):
    assert(type(before) == dict)
    assert(type(after) == dict)
    try:
        startHealth = before['opponent']['health']
        startMana = before['client']['mana']

        finalHealth = after['opponent']['health']
        finalMana = after['client']['mana']

    except KeyError:
        print("Warning: invalid round state structure (extractRound)")
        return (None, None)

    # Check that a spell was cast
    if startMana == finalMana: return (Outcome.PASS, 0)

    # Check for a fizzle (of course, flawed if the enemy has the ability to heal itself)
    if startHealth == finalHealth: return (Outcome.FIZZLE, 0)

    # Damage was dealth
    return (Outcome.DAMAGE, startHealth - finalHealth)

# Currently just processing an array of damage values
# Subject to change to a more complex interface
# data is array of arrays of dicts consistent the collection format
def process(data):
    damageStats = DataHandler("Damage Stats")
    fizzleStats = DataHandler("Fizzle Stats")

    for x, battle in enumerate(data):
        if len(battle) < 2:
            print(f"Warning: entry {x} has less than 2 rounds, data may be corrupt (skipping)")
            continue

        # Get the damage from the difference in boss health
        # startHealth = battle[0]['opponent']['health']
        # prevMana = battle[0]['client']['mana']
        # assert(startHealth == 550)      # Obviously this should be removed for later development
        #
        # for round in battle:
        #     currentMana = round['client']['mana']
        #     currentHealth = round['opponent']['health']
        #
        #     if startHealth != currentHealth:
        #         damageStats.insert(startHealth - currentHealth)
        #         break
        #
        #     # No damage but a cast attempt was made
        #     elif prevMana != currentMana: fizzles += 1
        #     prevMana = currentMana

        for x in range(len(battle) - 1):
            startRound = battle[x]
            afterRound = battle[x + 1]
            outcome = extractRound(startRound, afterRound)

            # Debugging
            # print("Outcome:", outcome[0], outcome[1])

            if outcome[0] == Outcome.PASS: continue
            if outcome[0] == Outcome.FIZZLE:
                fizzleStats.insert(0)
                continue

            # Damage was done but throw this in there to be sure something didn't go wrong
            assert(outcome[1])      # Damage dealt != 0
            damageStats.insert(outcome[1])
            fizzleStats.insert(1)
            break

    return (damageStats, fizzleStats)

if __name__ == "__main__":
    # Create an aggregate trial
    # Definitely not the prettiest way to do this, but I am not super sure how often we might look at the data in this way

    # aggregate = DataHandler("Aggregate")
    # for entry in spells:
    #     print("Processing:", entry)
    #     data = parse(entry[0])
    #     stats = process(data)[0]       # Get just the damage stats from the tuple
    #     aggregate.data += normalize(stats.data, entry[1])
    #     aggregate.i += stats.i
    # print(aggregate)
    #
    # damageCSQ = scipy.stats.chisquare(aggregate.categories()[1])
    # print("Chisquare Test P-value:", damageCSQ.pvalue)
    #
    # aggregate.plot()
    # exit()

    ###########################

    if len(sys.argv) < 2:
        print("Usage: {sys.argv[0]} <file.dat>")
        exit(1)

    data = parse(sys.argv[1])
    stats = process(data)       # Currently returns tuple, likely to change

    print(stats[0])
    print(stats[1])
    # print(f"Cast rate: {entries - stats[1]} / {entries} ({(entries - stats[1]) / entries}%)")

    # Shift damage values to indicies
    stats[0].data = normalize(stats[0].data, stats[0].min)

    # -- Perform a chisquare test --
    # Data here should be uniform
    damageCSQ = scipy.stats.chisquare(stats[0].categories()[1])
    print("[DAMAGE] Chisquare Test P-value:", damageCSQ.pvalue)

    # Data here is not
    castChance = 0.75
    cats = stats[1].categories()
    a, b, i = cats[0][0], cats[0][1], stats[1].i
    # print("a", abs(b - castChance) * i, "b", abs(a - castChance) * i)
    # print(cats[0], cats[1])
    fizzleCSQ = scipy.stats.chisquare(cats[1], f_exp=[abs(b - castChance) * i, abs(a - castChance) * i])
    print("[FIZZLE] Chisquare Test P-value:", fizzleCSQ.pvalue)

    # -- Plot the distribution
    stats[0].plot()
    # stats[1].plot()
