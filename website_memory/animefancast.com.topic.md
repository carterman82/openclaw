# TOPIC.md — Topic & Title Selection Rules (Anime Fancast)

This file governs **what** the agent writes about for Anime Fancast. It runs
*before* STYLE.md (which governs *how* it's written). A topic must pass every
rule in this file before it's handed to the writer agent.

Anime Fancast is intentionally **character-, arc-, and story-first**. A
named, timeless anime work's characters, their psychology, and the arcs/
stories that define them are the default subject and the reason this site
exists. Craft/industry essays (studio style, sound-design theory, genre
history) are real but a small, occasional minority — the site should almost
never reach for "an element unique to the production" (a director's
technique, a composer's motif, a studio's pipeline) when a character- or
story-driven angle on the same anchor is available, which it almost always
is.

## 0. The WP category is pre-assigned — pick a topic that fits it

The user message assigns the article's WordPress category up front ("Assign
category exactly: X"), rolled at random by the pipeline. Pick an anchor +
angle that genuinely belongs in the assigned category; never force an anchor
into a category it doesn't fit.

---

## 1. Core Principle

> Evergreen = anchored in a specific, named, already-classic anime/manga work
> (a character, an arc, a studio's stylistic signature, a score, a piece of
> real industry history) whose relevance doesn't depend on anything airing
> right now. Trending = tied to a current, dated real-world event (a new
> season just aired, a studio announcement, an award ceremony this year).

A topic like "Anime Is More Than Cartoons" or "Why Anime Is So Popular" is
neither — it's a generic essay with no anchor and no time-sensitivity.
**Generic essays are disqualified regardless of category.**

**Rule: every topic must name at least one specific anchor.** Acceptable
anchors:
- a named anime/manga franchise or work (Neon Genesis Evangelion, Death Note,
  Attack on Titan, Cowboy Bebop, Fullmetal Alchemist: Brotherhood, Dragon
  Ball Z, Hunter x Hunter, My Hero Academia, Mob Psycho 100, One Piece,
  Naruto, Code Geass, Steins;Gate, Demon Slayer, Jujutsu Kaisen, Vinland
  Saga, Monster, Spirited Away, Princess Mononoke, Re:Zero, Violet
  Evergarden — see §3 for the full rotating inventory)
- a named character from one of the above
- a named studio (MAPPA, Kyoto Animation, ufotable, Madhouse, Trigger, Bones,
  Studio Ghibli) or director (Miyazaki, Hosoda, Yamada, Yuasa)
- a named composer or a specific work's score/sound design
- a named, verifiable moment in anime history (the OVA boom, a studio's
  founding, a named award)

**Rule: the angle must be non-trivially specific to that anchor.** Would the
argument change for a different anchor? If not, it's generic. "Anime Villains
Are Interesting" fails; "Light Yagami's Moral Collapse as Rationalized
Villainy" passes because the argument is specific to that character's arc.

**Rule: the article must take a defensible *position*, not just summarize.**
A plot recap is not a thesis. Every topic must carry one of these angle-types,
listed in order of preference — reach for the first one the material
genuinely supports before considering the ones below it:

- **Character-psychology angle** — why a specific character's choices make
  sense (or don't), argued from specific scenes. The default, most-reached-for
  angle on this site.
- **Structural angle (arc/story)** — why an arc, episode, or story beat works
  mechanically or emotionally (pacing, reveal order, silence, framing, how one
  arc sets up another).
- **Misread-angle** — a commonly misunderstood scene, ending, arc, or
  character motivation, corrected with specific evidence from the work
  itself.
- **Comparative angle** — two named characters, arcs, or stories compared on
  one concrete axis.
- **Craft angle (rare — reach for this last, if at all)** — a specific
  stylistic or production choice (a director's technique, a composer's
  motif, a studio's animation approach). Only pick this when the article
  genuinely cannot be told as a character or story angle; most anchors offer
  a character/arc angle instead, so this should be an occasional exception,
  not a rotating default.

---

## 2. Content Mix Ratio

- **Character, arc & story-anchored (character studies, arc/episode analysis,
  franchise story deep-dives, comparative character/story pieces): ~90%** —
  the flagship, default pick, and the reason readers come to this site.
- **Craft & industry (studio/director analysis, score theory, real anime
  history — elements unique to the production rather than the story itself):
  ~10% at most** — occasional, not a rotating category. Even these should
  ground the argument in one or two named specific works rather than staying
  abstract, and should be reached for only when no character/arc angle on the
  same anchor would work as well.

Track this as a rolling target across the site, not a strict per-article
quota. If in doubt between a craft angle and a character/story angle on the
same anchor, always pick the character/story angle.

---

## 3. Timeless Anchor Inventory

Rotate through this list — don't let the site cluster on 2-3 favorite
franchises. Pull a *different* anchor from this list than whatever appears in
the `recent_titles` avoidance list.

Neon Genesis Evangelion, Death Note, Attack on Titan, Cowboy Bebop, Fullmetal
Alchemist: Brotherhood, Dragon Ball Z, Hunter x Hunter, My Hero Academia, Mob
Psycho 100, One Piece, Naruto, Code Geass, Steins;Gate, Demon Slayer, Jujutsu
Kaisen, Vinland Saga, Monster, Spirited Away, Princess Mononoke, Re:Zero,
Violet Evergarden, Frieren, Fruits Basket, Made in Abyss, The Promised
Neverland, Erased.

Add new anchors here over time as they prove out (see §7).

---

## 4. Disqualifying Patterns (Do Not Generate)

- Generic "anime is great" essays with no named anchor.
- Pure plot-summary recaps with no analytical thesis.
- Fabricated creator/staff quotes or unverified production anecdotes.
- Gossip or unverified personal claims about real people (voice actors,
  directors, staff).
- Adult/NSFW content, regardless of a franchise's original rating.
- Listicles with no analytical spine ("Top 10 Openings" with no argument).
- Seasonal news-cycle framing ("this week in anime," airing-schedule pieces).
- Non-anime pop culture as the standalone subject (fine only as a direct
  comparison point).
- Topics that duplicate or near-duplicate something already published (§5).
- **Multi-franchise genre-survey essays wearing anchor names as camouflage.**
  A piece that names 2+ specific franchises/characters only as supporting
  examples for a thesis about the genre or category as a whole ("shonen
  protagonists," "power scaling," "anime villains," "isekai power fantasies")
  is still generic, even though it name-drops specific things. **The test:
  strip out every named example and see if the thesis survives unchanged.**
  If the argument would read the same with different examples swapped in,
  it's a genre essay, not a genuinely anchored piece — reject it and pick a
  single anchor whose specific arc/character actually drives the thesis.
  ("The Anime Protagonist Is Not the Hero. He Is the Camera." using Shiroe +
  Naruto + Eren as interchangeable examples, or "Shonen Power Scaling: Why
  Heroes Never Actually Get Stronger" using Goku + Naruto + Pain + Kaguya as
  interchangeable examples, are both this failure mode.)

---

## 5. Duplicate & Rotation Check

Before finalizing a topic, check it against `recent_titles`:

1. **Same anchor + same angle — REJECT.** If a recent title already covers
   this character/franchise from a similar angle, pick a different anchor or
   a genuinely different angle-type.
2. **Anchor reuse — avoid within the last 8-10 titles.** Don't return to the
   same franchise/character while it's still fresh in recent output; the
   inventory in §3 is large enough that this should never force a weak pick.
3. **Category over-weight — avoid 4+ of the last 10 sharing the same
   angle-type** (e.g. four character-psychology pieces in a row). Vary
   angle-types across picks.

---

## 6. Handoff to the Writer (STYLE.md + tool schema)

Once a topic passes all checks above, it drives `title`, `seo_title`, and the
article's central thesis. `focus_keyphrase` should be a long-tail, specific
phrase tied to the named anchor (e.g. `"evangelion ending explained"` rather
than `"anime endings"`; `"death note light yagami villain"` rather than
`"anime villains"`).

This file's job ends at picking a validated, specific, anchor-driven topic.
`website_memory/animefancast.com.md` (persona/tone) and `Instructions/STYLE.md`
(cross-site voice rules) take it from there.
