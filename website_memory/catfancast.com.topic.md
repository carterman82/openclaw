# TOPIC.md — Topic & Title Selection Rules

This file governs **what** the agent writes about for Cat Fancast. It runs
*before* STYLE.md (which governs *how* it's written). A topic must pass every
rule in this file before it's handed to the writer agent.

Every topic falls into one of two categories: **Evergreen** or **Trending**.
Both are valid — Section 2 below sets the target mix between them. Cat Fancast
is intentionally evergreen-heavy, and within evergreen, intentionally
**personality- and behavior-heavy** — fun facts, quirks, and "what does my cat
actually mean by that" content is the core of the site. Breeds are a
supporting inventory, not the default.

## 0. The WP category is pre-assigned — pick a topic that fits it

The user message assigns the article's WordPress category up front ("Assign
category exactly: X"), rolled at random by the pipeline so the site doesn't
cluster on the model's favorite picks. Topic selection must respect it:

- Pick an anchor + angle that **genuinely belongs in the assigned category**.
  Map the §3 inventories to whatever the category implies (a behavior/
  personality category → §3b/§3f; a science/biology category → §3c; a
  health category → §3d; a history category → §3e; a breed category → §3a).
- Never force an anchor into a category it doesn't fit. If the assigned
  category is History, pick a real historical cat or episode — don't dress a
  behavior explainer in historical trim.
- All other rules in this file (angle-types, credibility moat, duplicate
  checks) still apply within the assigned category.

---

## 1. Core Principle

> Evergreen = tied to a SPECIFIC domain anchor (a named behavior or
> personality trait with established terminology, a named fun-fact/biology
> question, a named breed, a named medical or care concern, or a named real
> cat from history or culture) with permanent recurring search demand.
> Trending = tied to a current real-world event in the cat world — a
> peer-reviewed study published this year, a breed-registry decision, a
> notable real-cat death/anniversary, a public-health alert, a conservation
> milestone for cat relatives.

A topic like "Why Cats Are Cool" or "Things Every Cat Owner Should Know" is
neither — it's a generic essay with no anchor keyword and no time-sensitivity.
**Generic feline-fan essays are disqualified regardless of category** (see
Section 6).

**Rule: every topic — evergreen or trending — must name at least one specific
domain anchor.** Acceptable anchors:
- a named behavior or personality trait using its real ethology term
  (kneading, slow blink, head-bunting, bunting, allogrooming, the Flehmen
  response, single-cat vs. multi-cat sociality, the "cats are aloof" myth)
- a named biological question or structure behind a fun fact (tapetum
  lucidum, vibrissae, the agouti gene, the cat genome, the righting reflex,
  why cats purr, why cats can't taste sweetness)
- a named breed (Maine Coon, Sphynx, Russian Blue, …)
- a named medical condition (chronic kidney disease, FIP, HCM, FORLs,
  hyperthyroidism)
- a named care concern with a real term (allogrooming, environmental
  enrichment, multi-cat household introduction, kitten socialization
  window)
- a named real cat from history or culture (Tama, Larry the Chief Mouser,
  Stubbs, Dewey Readmore Books, Unsinkable Sam)
- a named owner misconception or care myth tied to a specific corrective
  thesis (e.g. "cats punishing owners by peeing outside the box", "old
  cats naturally slow down", "purring means a happy cat")

**Rule: the angle must be non-trivially specific to that anchor.** A generic
angle slotted onto a random anchor fails this test. "Persian Cat Watch Guide"
is meaningless. "Sphynx Care: Are They Hypoallergenic?" is fine because the
question is genuinely tied to that specific breed's lack of fur and the
Fel d 1 allergen story. Before committing to `[Anchor] + [Angle]`, ask:
would the answer be substantively different — or even contradictory — for a
different anchor? If no, the angle is generic.

**Rule: the topic must support a single defensible thesis answerable within
the article's assigned length band** (the user message's variation directives
set a per-run target; see STYLE.md). Too narrow ("the exact shade of
Smokey-Pearl in the 2003 CFA Persian standard") starves the word count. Too
broad ("everything about cats") blows past it. The right scope is one focused
claim with room for evidence, counter-evidence, and a payoff.

**Rule: the article must take a defensible *position*, not just explain a
topic.** Idea creation beats content creation. AI can produce polished
explainers on any cat topic in minutes; what it can't fake is a specific
*take* — resolving a confusion, siding with one theory against another,
correcting a repeated misread, or naming what most articles get wrong.
Every topic must carry at least one of these five angle-types:

- **Contested-explanation angle** — competing theories exist; the article
  picks a side or ranks them by evidence strength.
- **Myth-correction angle** — a widely-repeated claim that the evidence
  doesn't actually support; the article names the source of the myth and
  the actual finding.
- **Misread-signal angle** — a behavior owners systematically
  misinterpret; the article names the correct read and its ethology
  basis.
- **Non-obvious-comparison angle** — two anchors that look similar but
  differ in a specific, load-bearing way (Russian Blue vs. Chartreux;
  purring vs. chattering; CKD vs. hyperthyroidism early signs).
- **Primary-source angle** — a specific study, registry rule, veterinary
  guideline, or historical record whose contents most owners don't know;
  the article surfaces what the primary source actually says.

An article that could be titled *"[Anchor] Explained"* with no further
hook fails this test. *"Why Cats Knead: Three Competing Theories and Why
the Nest Hypothesis Is Weaker Than People Think"* passes because the
thesis is a ranking. *"Cat Whiskers Explained"* fails; *"Why Trimming
Cat Whiskers Is Cruel — What Vibrissae Actually Sense"* passes because
the thesis is a corrective.

Generic explainers rank against dozens of DA-40+ commodity SEO sites and
lose. A specific take with evidence is what a returning reader remembers
and what distinguishes Cat Fancast from AI-generated competitor content.

---

## 2. Content Mix Ratio

### Evergreen vs. Trending

- **Evergreen: 90–95%** (default target: 92%)
- **Trending: 5–10%** (default target: 8%)

This should be tracked over a rolling window, not enforced article-by-article.

**Implementation logic (executable from the `recent_titles` list provided
in the user message):**

1. Classify each recent title heuristically: if it contains time-anchored
   language (`Study Published`, `New [Breed|Standard] Recognized`,
   `Registry Update`, `Outbreak`, `Recall`, `Just Announced`, or a specific
   recent date/year), count it as Trending. Otherwise treat it as Evergreen.
2. If Trending share of the most recent 10–20 titles is below ~5% →
   bias this pick toward Trending.
3. If Trending share is above ~10% → bias this pick toward Evergreen.
4. Otherwise, pick freely with a ~92/8 weighting toward Evergreen.

**Trending-signal block (optional):** the user message may also contain a
`<reference_data type="trending_signals">` block with currently-popular
Reddit posts and real Google autocomplete completions. Consult it for topic
inspiration when self-picking, but it does NOT override the 92/8 ratio above
and it does NOT reclassify items as "Trending" by itself. A popular Reddit
post about cat behavior, breeds, or biology is still an EVERGREEN topic —
only count something against the Trending slot when it's tied to a dated
event per §4. When this block is absent (fetch failed), fall back to the
heuristic in steps 1–4.

### Inventory weighting within Evergreen

Cat Fancast's core identity is fun facts and cat personality/behavior
content — that's what people search for repeatedly and share. Breeds are
real and valuable but should not dominate the feed.

Target inventory split across evergreen picks:
- **Behaviors & personality (§3b): ~30%** — the flagship category
- **Biology / fun-fact questions (§3c): ~20%**
- **Owner-confusion (§3f): ~15%** — the AI-resistant slot; picks whose
  entire reason to exist is correcting a specific common owner error
- **Breeds (§3a): ~15%** — present, but capped relative to the above
- **Health & care (§3d): ~10%**
- **History & culture (§3e): ~10%**

This is a rolling target, not a per-article quota. See §7 for the rotation
mechanics that keep this from drifting (e.g., breed pieces stacking up).

A perfect mix is not required per article. The goal is that *the site
overall* trends toward this ratio over time.

---

## 3. Anchor Inventories

Evergreen topics are built from items in these six parallel inventories.
Edit/expand them over time as new specific topics prove out. **Default to
§3b, §3c, or §3f first** — behaviors, quirks, fun-fact biology, and
owner-misconception corrections are the site's bread and butter. Pick from
§3a (breeds) deliberately, not by default.

### 3a. Breeds (~30 to start) — supporting inventory, not the default
Maine Coon, Persian, Siamese, Bengal, Ragdoll, British Shorthair, Sphynx,
Russian Blue, Scottish Fold, Norwegian Forest Cat, Abyssinian, Burmese,
Birman, Devon Rex, Cornish Rex, Oriental Shorthair, Savannah, Munchkin,
Manx, Turkish Van, Turkish Angora, Egyptian Mau, Tonkinese, Chartreux,
Selkirk Rex, LaPerm, Singapura, Bombay, Korat, American Shorthair,
American Curl, Japanese Bobtail, Ocicat, Siberian, Somali.

### 3b. Behaviors & personality (~30 to start) — flagship inventory
Purring (mechanics + theories), kneading ("making biscuits"), the slow
blink ("cat kisses"), head-bunting / bunting, chattering at birds, the
bunny-kick (hind-leg rabbit kick), tail language, ear positions, zoomies /
FRAPs, hiding when sick or stressed, knocking objects off surfaces,
bringing prey to owners, crepuscular hunting (dawn/dusk activity), the
Flehmen response, allogrooming between bonded cats, why cats sit in boxes,
loaf posture and why cats sit that way, sploot/cat-sprawl postures, the
"elevator butt" response to back-petting, whisker fatigue, the "cats are
aloof" myth vs. attachment-style research, why cats follow you to the
bathroom, why cats ignore commands but respond to their name, kitten play
biting vs. real aggression, scent-marking via cheek rubbing (bunting) and
why cats rub on legs, the "third eyelid" (nictitating membrane) and what
it signals, why cats stare without blinking, why cats sleep on your chest
or face, redirected aggression, the cat "slow approach / sideways body"
greeting behavior, why cats meow at humans but not at other cats, separation
anxiety in cats (it exists, contrary to popular belief), how cats actually
perceive their owners (research on attachment bonds).

### 3c. Biology / fun-fact questions (~20 to start)
Night vision and the tapetum lucidum, taste of sweetness (the Tas1r2
pseudogene), whisker function (vibrissae), the righting reflex,
retractable claws, the dewclaw, the cat genome, calico/tortoiseshell
coat genetics (X-inactivation), the agouti gene and tabby patterns,
domestic-cat lifespan and what drives it, why cats can't focus on
objects directly under their nose, terminal velocity and high-rise
syndrome, why cats sleep ~16 hours, Jacobson's organ, the role of the
Fel d 1 protein in cat allergies, why cats' eyes glow in photos/flashlight,
why cats have rough tongues (the papillae), why cats knead before lying
down (the evolutionary nest-making theory), polydactyl cats and the gene
behind extra toes, why orange cats are disproportionately male.

### 3d. Health & care topics (~15 to start)
Chronic kidney disease (CKD), FIP and the antiviral revolution,
FIV / FeLV, hypertrophic cardiomyopathy (HCM, especially in Maine
Coons and Ragdolls), dental disease and FORLs, hyperthyroidism,
diabetes mellitus, obesity, feline asthma, flea-allergy dermatitis,
indoor enrichment, litter box troubleshooting, declawing alternatives,
multi-cat household introductions, senior cat care, kitten
socialization windows (2–7 weeks).

### 3e. History & culture (~15 to start)
Egyptian sacred cats (Bastet, mummified cats, the Bubastis cemetery),
Roman ships' cats, Tama the station master, Larry the Chief Mouser
(10 Downing Street), library cats (Dewey Readmore Books), Stubbs the
mayor cat (Talkeetna, Alaska), Unsinkable Sam, the Black Death and
the cat-population myth (separating fact from internet legend),
witch-trial-era cat persecution, cats in Japanese folklore (the
maneki-neko origin story, the bakeneko folklore tradition — the real
folk history, not modern fictional cat characters), the domestication
timeline (Cyprus burial 7500 BCE, Fertile Crescent), cat-show history
(1871 Crystal Palace), early breed-registry history (NCC, CFA, GCCF
founding).

### 3f. Owner-confusion / clarity-where-confusion-exists (~16 to start) — the AI-resistant slot
Topics whose ENTIRE reason to exist is the correction of a specific
common owner error, framed as a resolution rather than an explainer.
These are the highest-value picks in the Cat Fancast inventory: they
force a defensible position (a corrective take is not a generic
explainer), and they're the pattern generic AI-generated cat content
consistently fails at because a correction requires siding against
something specific.

- "My cat is punishing me by peeing outside the box" — nearly always
  medical (UTI, crystals, CKD, arthritis) or anxiety, not spite;
  ISFM/AAFP guidance says the first step is a vet visit.
- "Cats are aloof and don't bond with owners like dogs do" — Vitale et
  al. 2019 (Current Biology) showed cats form the same secure/insecure
  attachment styles as dogs and human infants.
- "Purring means my cat is happy" — cats also purr in pain, stress,
  and terminal illness; the tuning-fork frequency theory suggests
  self-soothing / healing, not exclusively contentment.
- "Cats always land on their feet" — righting reflex is real but
  high-rise syndrome is well-documented; falls from 2-6 stories injure
  more cats than 7+ stories (terminal velocity + relaxation window).
- "Milk is a treat for cats" — most adult cats are lactose-intolerant;
  the "saucer of milk" image is a cultural relic, not a care tip.
- "Declawing is like a manicure" — declawing is amputation of the
  distal phalanx; AVMA and AAFP position statements discourage it.
- "A wagging tail means a happy cat" — opposite of dogs; a lashing
  tail signals agitation, and a fast tip-flick often precedes an
  aggressive redirect.
- "My cat is meowing because they want food" — adult cats meow
  primarily at humans (rarely at each other); the meow is a learned
  attention-seeking behavior whose specific meaning is context-dependent.
- "Old cats naturally slow down" — often masks CKD, arthritis, or
  hyperthyroidism; ISFM senior-cat guidance calls this the single most
  common missed-diagnosis pattern.
- "Indoor cats don't need vaccinations" — rabies is legally required in
  most jurisdictions regardless of indoor status; leptospirosis and
  respiratory viruses hitchhike on human clothing.
- "Grain-free food is healthier for cats" — the dog-DCM story doesn't
  transfer cleanly; cats are obligate carnivores, and grain content
  is not the meaningful axis for feline nutrition.
- "Cats hate water" — Turkish Van, Bengal, Maine Coon, and Abyssinian
  populations show water-tolerant or water-seeking behavior; the myth
  is domestic-generalization from a subset.
- "My cat brings me prey as a gift" — competing theories (teaching
  behavior, provisioning, play-object storage) with no consensus;
  probably not a gift in the human sense.
- "Cats are solitary and don't need companions" — depends heavily on
  early socialization (2-7 week window); bonded pairs and colonies are
  well-documented, and single-cat isolation causes measurable stress
  in some individuals.
- "The Black Death was worse because Europeans killed cats" — popular
  internet claim; the actual medieval evidence for large-scale cat
  culling as a plague amplifier is thin.
- "My cat is 'jealous' when I hold the baby" — resource-guarding,
  disrupted routine, or scent-territory disruption; not jealousy in
  the human emotional sense.

**Rule:** Every §3f pick must state the specific owner error it
corrects (in the first sentence of the article) AND provide the correct
read backed by at least one specific credibility source per §5. §3f
overlaps with §3b (behavior) and §3d (care): a topic that could sit in
either belongs in §3f when the ENTIRE angle is the correction, not the
explanation. Lead with the take, not the setup.

**Rule:** Lead with §3b, §3c, and §3f. Use §3a, §3d, and §3e to round
out variety, not to anchor the majority of output. The duplicate &
rotation check in Section 7 enforces this, including an explicit
breed-stacking guard.

---

## 4. Trending Topics — Definition & Sources

Trending topics are time-sensitive but should still be specific and
substantive — not a reworded press release or a single tweet. Trending
is a small minority of the feed (see §2).

**Valid trending triggers:**
- A peer-reviewed feline study just published (behavior, genetics,
  veterinary medicine) — behavior/cognition studies are especially good
  fits given the site's personality-content focus
- A breed-registry decision (new breed accepted by CFA/TICA/GCCF, a
  breed standard revised, a controversial breed delisted)
- A notable real-cat death, retirement, or meaningful anniversary —
  Tama's, Larry's, Stubbs', etc.
- A public-health alert relevant to cats or cat owners (zoonosis
  outbreak with veterinary guidance, recall of a major cat food)
- A conservation milestone for wild cat relatives (Scottish wildcat
  population update, Iberian lynx recovery) when it genuinely informs
  domestic-cat context
- A high-profile veterinary research result (FIP antiviral
  developments, lifespan or genetics findings)

**Invalid trending triggers:**
- A viral TikTok / Reels video with no underlying news
- A single tweet, rumor, or fan-theory with no primary source
- Influencer drama, breeder feuds, social-media controversy
- Anything pegged to a "currently popular" fictional cat character
  (Garfield reboot, Hello Kitty merchandise drop, etc.) — see §6

---

## 5. Proven Angle Templates

### Credibility moat (applies to every angle, evergreen or trending)

Every article — regardless of anchor or angle template — must lean on at
least ONE specific, name-able credibility source, placed in the
introduction or the first substantive paragraph (never buried in the
close). Acceptable sources:

- a named peer-reviewed study (with lead author, year, and journal or
  institution): "Vitale et al. 2019 (Current Biology)"
- a named researcher or veterinary institution: Dr. Mikel Delgado
  (UC Davis Cat Behavior Clinic), Cornell Feline Health Center, Royal
  Veterinary College, University of Lincoln (Daniel Mills' group)
- a named professional-body position statement: AAFP, AVMA, ISFM,
  WSAVA guidelines
- a specific breed-registry rule with clause: "CFA breed standard for
  the Maine Coon (revised 2019) sets…"
- a specific historical primary source: Herodotus on Egyptian cats,
  the CFA 1906 founding minutes, the 1871 Crystal Palace show catalog
- a named real cat (Tama, Larry, Stubbs, Unsinkable Sam) whose
  biography is externally documented
- a named reference book by a domain expert: "John Bradshaw's *Cat
  Sense*", "Sarah Ellis' *The Trainable Cat*"

*"Experts say"*, *"studies show"*, *"veterinarians recommend"* all
FAIL this rule — they are unattributed handwaves. Name the expert,
the study, or the guideline.

This is the moat. AI-generated competitor articles routinely skip
specific citations because they cannot ground them without
hallucinating. A named source is what distinguishes a real answer
from filler, and it's what a returning reader remembers. When the
generator does not have a real, verifiable source in mind, it should
either pick a different topic where it does, or downgrade the article
scope to what it can actually source.

### Evergreen Angles
An anchor alone isn't a topic — pair it with an angle people recurringly
search for, regardless of current events.

**Behavior & personality angles (use most often)**
| Angle Template | Example |
|---|---|
| What this behavior actually means | "What a Slow Blink Actually Means, According to the Research" |
| Competing theories | "Why Cats Knead: Three Competing Explanations and What the Evidence Says" |
| Body-language guide | "Cat Tail Language: Reading Mood from the Tail Alone" |
| Misread behavior | "Why Cats Bring You Dead Things — It's Not What You Think" |
| Quirk explainer | "Why Cats Knock Things Off Tables" |
| Myth-busting personality piece | "Are Cats Really Aloof? What Attachment Research Actually Shows" |
| "Why does my cat..." direct-answer piece | "Why Does My Cat Follow Me to the Bathroom?" |
| Posture/quirk explainer | "Why Cats Sit in Boxes, Even Empty Ones" |
| Communication explainer | "Why Cats Meow at Humans but Rarely at Each Other" |

**Biology / fun-fact angles**
| Angle Template | Example |
|---|---|
| Anatomy explainer | "Cat Whiskers: What They Actually Sense and Why Trimming Them Is Cruel" |
| Mechanism deep-dive | "How Cat Night Vision Actually Works: The Tapetum Lucidum Explained" |
| Genetics explainer | "Why Calico Cats Are Almost Always Female: The X-Inactivation Story" |
| Sense-comparison | "Can Cats Taste Sweetness? The Tas1r2 Pseudogene Story" |
| Surprising-fact deep-dive | "Why Most Orange Cats Are Male: The Genetics Behind a Real Pattern" |

**Breed angles (use deliberately, not by default)**
| Angle Template | Example |
|---|---|
| Defining-trait explainer | "Maine Coon Size: Why They Get So Large" |
| Origin & history | "Where the Bengal Cat Actually Comes From: The Asian Leopard Cat Story" |
| Breed health concerns | "Persian Breathing Problems: What Breeders Have Done About Brachycephaly" |
| First-time owner reality check | "Sphynx Care: What First-Time Owners Underestimate" |
| Multi-breed comparison | "Russian Blue vs. Chartreux vs. Korat: The Three Grey Breeds Compared" |
| Breed standard explainer | "How the CFA Defines a Show-Quality Ragdoll" |
| Energy/temperament reality | "Bengal Energy Levels Explained — Are They Really 'Like a Toddler on Espresso'?" |

**Health & care angles**
| Angle Template | Example |
|---|---|
| Early-signs guide | "Feline Chronic Kidney Disease: Early Signs Most Owners Miss" |
| Breakthrough explainer | "The FIP Breakthrough: How a Once-Fatal Disease Became Treatable" |
| Care-myth correction | "Declawing Alternatives: What Actually Works" |
| Lifestage explainer | "Senior Cat Care: What Changes at 11+ Years" |
| Enrichment guide | "Why Indoor Cats Need Enrichment, Not Just Toys" |

**History & culture angles**
| Angle Template | Example |
|---|---|
| Real-cat profile | "Tama the Station Master: How One Cat Saved a Japanese Railway" |
| Historical reassessment | "Cats in Ancient Egypt: Sacred Animal or Working Pest Control?" |
| Myth-vs-fact | "Did Killing Cats Cause the Black Death? Separating Folklore from Evidence" |
| Origin story | "How Maneki-neko Became the Worldwide Lucky Cat Symbol" |
| Institutional history | "The 1871 Crystal Palace Cat Show: How the Cat Fancy Began" |

**Owner-confusion angles (§3f — the AI-resistant slot)**
Every template here is corrective by design: the article's thesis is the
correction, not the explanation. Every one of these MUST cite a specific
source per the credibility moat rule above — that's what makes the
correction load-bearing rather than just contrarian.

| Angle Template | Example |
|---|---|
| Named-error correction | "No, Your Cat Isn't Peeing Outside the Box to 'Punish' You — What's Actually Happening" |
| Attachment-research reframe | "'Cats Are Aloof' Is Wrong: What the Vitale 2019 Attachment Study Actually Found" |
| Signal-reversal | "A Wagging Tail Means the Opposite for Cats — Reading Feline Tail Motion" |
| Missed-diagnosis surfacing | "'Slowing Down' in Senior Cats Isn't Just Age — What ISFM Flags as the Real Suspects" |
| Cultural-relic correction | "Why the 'Saucer of Milk' Image Is a Care Myth" |
| Procedure reality-check | "Declawing Isn't a Manicure — What the AVMA Position Statement Actually Says" |
| Origin-of-the-myth explainer | "Where 'Cats Always Land on Their Feet' Comes From — and What High-Rise Syndrome Shows" |

### Trending Angles
Tied to a real, named, verifiable event — not just news rephrased.

| Angle Template | Example |
|---|---|
| New study explainer | "What the 2024 [Researcher] Study Tells Us About Cat Cognition" |
| Registry decision | "TICA Recognizes the [Breed]: What the Standard Actually Requires" |
| Public-health alert | "The [Year] [Brand] Recall: What Cat Owners Need to Verify" |
| Real-cat anniversary | "Ten Years Since Tama: How Her Legacy Reshaped Japanese Rail-Cat Tourism" |
| Antiviral / treatment milestone | "The FIP Antiviral Approval: What Changed and What Owners Still Pay For" |

---

## 6. Disqualifying Patterns (Do Not Generate)

Reject any topic idea that matches these patterns, regardless of category:

- **Any topic centered on a copyrighted or fictional cat.** Auto-reject:
  Garfield, Hello Kitty, Pusheen, Tom (Tom & Jerry), Doraemon, Jiji
  (Kiki's Delivery Service), Sailor Moon's Luna/Artemis, the Cheshire Cat,
  Crookshanks, Mrs. Norris, Salem, Snowbell, the Cat in the Hat,
  viral-meme cats with living rights holders, any cat character owned by
  a studio/publisher/creator. The site is real cats only. Maneki-neko as
  a *folk tradition / cultural object* is fine; a Disney cat film tie-in
  is not.
- Generic feline-fan essays not tied to a named anchor — "Why Cats Are
  Great Pets," "The Magic of Cats," "Why I Love My Cat"
- Generic vet-craft essays — "How to Read a Veterinary X-Ray," "What
  Veterinary School Is Like"
- "Top 10 Cutest Cat Breeds" listicles without a real argument behind the
  ranking — these are commodity SEO content that fails to differentiate
  from the dozens already on every pet-content farm
- Pure speculation / clickbait with no real source (trending only)
- Topics built on a single unverified tweet, viral video, or anonymous
  forum post — credibility is part of evergreen survival
- Topics that require knowing whether something is "currently popular" or
  "newly released" to make sense — trending pieces should still have a
  story to tell once the news is old; evergreen pieces should never
  depend on recency at all
- Angles that don't fit the anchor (see §1's "non-trivially specific"
  rule) — e.g. "watch order" for a breed, "manga vs. anime" for anything
- Topics that duplicate or near-duplicate something already published
  (see §7)
- Non-cat content — dogs, exotics, general pet wellness, big-cat
  conservation as a standalone topic
- Topics about cat-themed merchandise drops, breeder-influencer drama,
  or social-media controversies

---

## 7. Duplicate & Rotation Check

Before finalizing a topic, run these checks against the `recent_titles`
list provided in the user message (this is the only published-history
signal the agent receives at generation time):

These are HARD BANS, not biases. Soft "bias toward" phrasing demonstrably
did not prevent anchor clustering; treat every check below as a rejection
rule.

1. **Same [Anchor] + [Angle] check — REJECT.** Scan recent titles for the
   same anchor in combination with a similar angle (e.g. if a recent title
   is "Why Cats Knead," then "Cat Kneading Explained" is a near-duplicate —
   reject). Re-paraphrased angles on the same anchor are the most common
   stealth-duplicate failure mode.
2. **Anchor reuse — BANNED within the last 10.** If the anchor appears in
   ANY of the most recent ~10 titles (same behavior, same breed, same
   condition, same cat), it is excluded this pick. No exceptions short of
   a real dated trending event per §4. Pick a different anchor from the
   same inventory — the inventories each hold 15–35 anchors precisely so
   this never forces a weak pick.
3. **Breed-stacking guard — BANNED past the cap.** Count how many of the
   most recent ~10 articles came from §3a (Breeds). If breeds exceed ~20%
   of that window, another breed topic is excluded — pick from §3b or §3c
   instead, even if a breed idea seems strong.
4. **Inventory over-weight — EXCLUDED past 4-in-10.** If any single
   inventory accounts for 4+ of the most recent ~10 titles, that
   inventory is excluded this pick (unless the pre-assigned WP category
   only maps to that inventory — then satisfy the check by maximizing
   anchor distance instead: different anchor family, different angle-type).
5. **Recurring-angle fatigue — REJECT on the third repeat.** The same
   angle template must not recur three picks running across different
   anchors ("What this behavior really means" three articles in a row,
   even with different behaviors). Infer the templates of the last few
   titles and pick a different one.

---

## 8. Series-Aware Selection

Cat Fancast should build value-driven series over time — clusters of
related articles that solve a real reader problem end-to-end. Series
accrue authority faster than scattered one-offs, and they give internal
linking a real spine (each new piece in a series naturally links to the
others). This is the "value-driven series" pattern: the site's identity
compounds when related articles reinforce each other, and diffuses when
articles are unrelated one-shots.

**Recognized series (add to this list as new ones prove out):**

- **Reading Your Cat** — body-language and behavior-signal series
  covering tail language, ear positions, eye contact and slow blink,
  posture (loaf/sploot/side-body), vocalization (meow/chirp/trill),
  and whisker signals. ~5–7 pieces.
- **Cat Genetics Explained** — heritable-trait and coat-pattern series
  covering calico X-inactivation, the agouti gene and tabby patterns,
  orange-male genetics, polydactyly, and the Fel d 1 allergen. ~4–5
  pieces.
- **Silent Diseases** — hard-to-detect chronic feline conditions:
  CKD early signs, HCM, hyperthyroidism, FORLs / dental disease,
  feline diabetes. ~4–5 pieces.
- **New Owner Reality Checks** — first-time-owner truth pieces on
  specific breeds (Sphynx, Bengal, Persian, Maine Coon, Ragdoll…).
  Naturally recurring.
- **Cats That Changed History** — profiles of real cats with
  documented biographies (Tama, Larry, Stubbs, Unsinkable Sam, Dewey
  Readmore Books, the ships' cats). Naturally recurring.
- **Owner Misconceptions Corrected** — §3f overflow, framed as an
  ongoing series so recurring corrections build a recognizable brand.

**Rule: when picking from `recent_titles`, look for an in-progress
series with a natural gap to fill.** If the site has recently published
*Cat Tail Language* and *Cat Ear Positions* but not *What the Slow
Blink Actually Means*, and the missing piece belongs to the Reading
Your Cat series, filling that gap is worth more than a scattered pick
of equal quality. Series completion is a higher-order signal than
individual topic novelty.

**Rule: when a topic is picked, if it belongs to a recognized series
AND at least one sibling article appears in the internal-link
candidates, the article MUST cross-link to that sibling.** This is
already required by the standard internal-linking rule ("weave 1–3 in
when relevant"), but a series sibling IS relevant by definition — the
model should not skip it. Log any such series membership in
`internal_links_used`.

**Rule: the article does not need to name the series in body text**
(no need for "This is part of our Reading Your Cat series…"). The
cross-links between sibling articles build the series identity
implicitly. A future improvement could add a visible series-header
block; for now, the linking discipline is the mechanism.

**Rule: don't force a series membership that isn't real.** A cat-genetics
article is a series member; a general "cats are curious" essay is not.
Series discipline exists to make good picks more valuable, not to
retrofit shape onto weak picks.

---

## 9. New Anchors Outside the Existing Inventories

If a behavior / condition / historical cat / breed keeps generating
strong recurring traffic over time (multiple pieces performing well
across months), flag it for promotion to the appropriate inventory in
§3. Once approved, add it so future evergreen topic generation can use
it directly. New behavior and fun-fact anchors should be prioritized for
addition over new breed anchors, given the site's weighting in §2.

---

## 10. Handoff to the Writer (STYLE.md + tool schema)

Once a topic passes all checks above, it becomes the source for these
fields in the `submit_article` tool call:

- **Domain anchor + angle** → drives `title`, `seo_title`, and the
  article's central thesis. STYLE.md governs the actual phrasing.
- **Target search phrase** → goes into `focus_keyphrase` (2–4 words a
  cat-curious reader would actually type into Google: e.g.
  `cat slow blink`, `why cats knead`, `feline chronic kidney disease`,
  `maine coon size`).

  **Long-tail preference:** Cat Fancast is a newer site; broad head terms
  (`cat grooming`, `cat breeds`) are dominated by high-DA publications.
  The practical path to ranking is specificity. Prefer question-format
  or qualified keyphrases over noun-chunk head terms whenever the article
  answers a direct question or targets a specific sub-angle:

  - Question format: `"why cats lick you"` > `"cats licking"`;
    `"do cats recognize their owners"` > `"cat recognition"`
  - Qualified noun phrase: `"bengal cat energy levels"` > `"bengal cat"`;
    `"feline kidney disease early signs"` > `"CKD cats"`
  - Angle qualifiers that lower competition and match real intent:
    `"explained"`, `"what it means"`, `"for first-time owners"`,
    `"early signs"` — especially effective on behavior and biology topics
    where commodity listicle farms produce shallow results

  When a topic originates from a Google Suggest completion (e.g.
  `"why does my cat lick me"`), keep the question phrasing rather than
  compressing it — the completion *is* the low-competition long-tail form
  real users type.
- **Search phrase, hyphenated** → goes into `slug`.
- **Category (Evergreen / Trending)** → governs how the writer handles
  time-anchored language. Evergreen: zero time references, zero recency
  language. Trending: time-anchored phrases are allowed when they're
  load-bearing to the news angle, but write so the article still has
  value once the news is no longer fresh.

This file's job ends at picking a validated, categorized, specific topic.
STYLE.md + the base rules in `generator.py` take it from there.

---

## 11. Quick Validation Checklist

Before a topic is approved, it should pass all of these:

- [ ] Names at least one specific domain anchor (behavior/personality
      trait, biology/fun-fact question, breed, medical condition, care
      concern, real cat, or named owner misconception)
- [ ] Angle is non-trivially specific to that anchor (would not apply
      cleanly to a different anchor)
- [ ] Supports a single defensible thesis in 700–1200 words
- [ ] **Article takes a defensible *position*, not just an explainer**
      (§1): matches one of the five angle-types — contested-explanation,
      myth-correction, misread-signal, non-obvious-comparison, or
      primary-source. Would fail the "*[Anchor] Explained*" filler test.
- [ ] **Credibility moat source planned** (§5): at least one specific
      named source (peer-reviewed study with author/year, named
      researcher or institution, professional-body position statement,
      breed-registry clause, historical primary source, named real cat,
      or named expert-authored reference) is committed to appear in the
      introduction or first substantive paragraph. Not "experts say".
- [ ] Clearly categorized as Evergreen or Trending
- [ ] If Evergreen: anchor is in §3 (or flagged for inventory addition
      if not), and §3b / §3c / §3f (behavior, personality, fun facts,
      owner-confusion) was the first inventory considered before
      reaching for §3a (breeds)
- [ ] **§3f (Owner-confusion) considered**: is this a topic whose
      entire reason to exist is the correction of a specific common
      owner error? If yes, framed as a correction not an explainer.
- [ ] If Trending: tied to a real, current trigger (study, registry
      decision, public-health alert, real-cat anniversary), not
      speculation; story survives once the news is stale
- [ ] Paired with a proven angle template from §5 for its anchor type
- [ ] **Series membership checked** (§8): if the topic belongs to a
      recognized series (Reading Your Cat, Cat Genetics Explained,
      Silent Diseases, New Owner Reality Checks, Cats That Changed
      History, Owner Misconceptions Corrected), and a sibling article
      appears in the internal-link candidates, that sibling is queued
      for cross-linking. Series membership is not forced onto weak
      picks.
- [ ] Not a duplicate/near-duplicate of a `recent_titles` entry (same
      anchor + similar angle = reject)
- [ ] **Not centered on a copyrighted fictional cat** (hard ban, §6)
- [ ] Not a generic feline-fan essay or commodity listicle
- [ ] Inventory rotation respected (no 2+ consecutive breed picks, no
      3+ consecutive picks from any single inventory, and breeds stay
      under ~20% of the recent_titles window)
- [ ] Pick is consistent with the ~92/8 Evergreen/Trending bias, or
      deliberately corrects the recent_titles mix toward it
- [ ] `focus_keyphrase` uses a long-tail or question-format phrasing
      rather than a broad head term (see §10 long-tail preference)