import urllib.request
import random
import os

PREVIOUS_WORDS_STR = """
halt think get twist define leg mouth spit mad actually
different anxious neat dead fail chocolate knife quit feel slow
thin push daughter be recognize rub dangerous scarcely barely present
request where earth calm split thirsty everything awake especially crack
free smell cook morning perhaps i row crawl punch shoot
fruit prepare worker drive around such seek basic loose win
leap can attempt war along shop leave create provide thanks
ours scrub sign cure sing peek bent through wither sometimes
squint safe cowardly pass acquire joke shoe hopeless sound untie
game kick underneath soon construct own open alive swallow son
understand live saturday window closed happy february attend flatter red
educate hostile tear toe he top real wink salt upon
sleep table since treat serve sniff aunt alert afternoon inhale
badly really born hospital floor apple sudden milk piece draw
nourish bye run believe talk sport any high chicken triangle
polite explore journey new crooked serious tumble count rich sour
their submit catch curved hat immediately thursday exit manage which
resume soar sugar eavesdrop vacuum there husband bitter star play
wine essential phone peace heal smirk various mine subtract main
assemble truce green match several gather fly travel man hear
cat expand brother gasp massive sweat grow declare purple now
gray train by end help accelerate simply forgive us enough
itch simple harm april october glance note how wednesday truly
quite everywhere heavy cousin bag argue month cover healthy need
tidy digest dust to sunday blue rapid offer dinner hard
compel loud does forget butter even scratch peel type cost
mold down blame invent neglect rest foot huge remember soul
sort whisper fold moan bread reply dream crucial microscopic who
confess history risk mean permit meat perish side strike beat
wrong bloom desire sun true blossom slice idea may groan
wail word near another finger vegetable fade hop within sweep
yours come obviously guide whom primary line girl tuesday hello
orange conclude giggle boss beautiful point our park watch no
release during short before from work color blind bake rule
defeat announce will hers bicycle upward shape all eye thank
carelessly often hey multiply chair inside bow family dash dance
bad slender fact colors tea coat nice school save fry
merely something initial almost sail tow today skip plan hurry
child grandparent both ok apart swap hardly pardon fill fifth
commence could anybody state glide friendly ear are off doubt
you bowl been attach week quarter test over doubtful chuckle
pick time hunt protect clothes sick false insult wipe next
unpack exist tired sorry fine important cruel fight crash participate
crush bring produce drink unlocked nose friday half uncle sketch
student unwrap cool hold on sit behind better continue snow
tighten lack search compare fart control terrible design increase surrender
resist kitchen her glare must rain nervous connect govern improve
some had plate warm accuse wash pack still survive messy
rice bathroom single ban hot back ignore want language basically
exhibit book fat bleed snatch people inquire stir guilty separate
put definitely sure forbid happen sister my wait between lock
ceiling noise box cheese carry locked somebody reduce swim strong
shirt possible quick notice uncover finish rough whose carve parent
dark fundamental money remain decay against nowhere flat repair year
load steer kind would grandfather write begin recommend punish internet
body front unlock suggest make narrow touch unload chase persuade
never group warn display just kneel approve mend theirs young
raise form yes funny onto anymore upset know rotate break
paper always unfold incorrect interested salad finally succeed in tour
tooth wish grip delicious find june someone coffee unlikely sob
wander chop has pout keep part mix frown rude nephew
brake usually do fish hide this deaf very bend lower
whip bird tie corner easy white arrange maybe fork particularly
soft out thick weep pant flip toss with why large
team claim wind plant too agree nobody awful outward most
quickly float police praise smash go describe arise fast store
chew stand achieve stroke beyond goodbye quiet these sad we
answer despite she complete old welcome doctor gossip tomorrow jog
escape categorize smile him whole shall thing exchange pursue living
under roast receive return supply proud ahead blink flee good
way they street more past race map completely every skinny
roam mop silent small face ready anticipate introduce ugly admit
spicy miss enormous organize correct sink room stain long spin
fall rip mark excited pink menu weak bet november father
brown dart road after weigh january enemy tickle depart stroll
without alone black confused restaurant then difficult worse debate slide
cough hopeful deny innocent rot hug grandmother juice eventually square
fewest hurl head accomplish possess bedroom pasta bored stop downward
multiple plane major stupid suddenly direct prohibit backward world office
yawn clear fire wife minor respond discover devour night anything
were home stay allow revolve yield wring horse visit defend
at certain reveal inspect squeeze sibling haul peer manufacture about
asleep sock sell ride excellent pants cry waste loosen those
empty shocked like force bed beneath moon together hour double
was guard detach gamble day record wake burp accept did
realize movie consume tall many totally memorize edge press door
pork embrace destroy chat sprout absolutely see either throw village
dice advise soil wet light neither cross rather shout throughout
city die feed secure till consider reward full pencil glad
when hope already except second blend let pepper damage previous
stale nothing mind ruin excuse distribute somewhere ponder outside early
august low circle observe likely everybody above sweet seal demand
classify september restore grill show set class soup invite certainly
rinse song pause cut up tongue silence slap pet exhausted
necessary december center me first unseal say pen sigh change
seize them boy boat round little forth niece banana listen
angry across add hate recall capture starve divide convince please
fourth list straight computer might scream turn complex sneeze creep
should fasten examine treaty aim noisy third apologize anyway sky
bus dry cup ill snack give wall anyone for unfasten
"""

EXCLUDED_WORDS = set(PREVIOUS_WORDS_STR.split())

def main():
    print("Downloading words list...")
    url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            all_words_text = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to download: {e}")
        return

    lines = all_words_text.splitlines()
    print(f"Downloaded {len(lines)} total words.")

    # Filter
    valid_words = []
    for line in lines:
        parts = line.strip().split()
        if not parts: continue
        w = parts[0].strip().lower()
        # Keep words that are 3-10 chars long usually to avoid extremely weird words, but any length >= 3 is fine
        if len(w) >= 3 and w.isalpha() and w not in EXCLUDED_WORDS:
            valid_words.append(w)
    
    print(f"Valid words after filtering: {len(valid_words)}")

    if len(valid_words) < 10000:
        print("Not enough words!")
        return

    selected_words = valid_words[:10000]
    random.shuffle(selected_words)
    
    output_path = os.path.join(r"c:\Users\User\Desktop\Signify\aws", "10k_words.txt")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WORDS = [\n")
        
        # Write 10 words per line
        for i in range(0, len(selected_words), 10):
            chunk = selected_words[i:i+10]
            line = "    " + ", ".join(f'"{w}"' for w in chunk)
            if i + 10 < len(selected_words):
                line += ","
            f.write(line + "\n")
        f.write("]\n")
        
    print(f"Successfully wrote 10,000 words to {output_path}")

if __name__ == "__main__":
    main()
