# IMAGE_GENERATOR.md — Anime Fancast

## Purpose

This file governs how cover image prompts are generated for animefancast.com
articles. It exists so every cover feels like genuine anime key art — the
character(s) the article is actually about, rendered in an anime/manga
illustration style — instead of a generic stock photo or an unrelated scene.
Use this alongside `STYLE.md` (article copy) and `animefancast.com.topic.md`
(topic selection) — this file governs only the **image prompt** handed to the
image generation API.

**Subject scope.** Covers should depict the specific named character(s) the
article is actually about, in a style evocative of anime/manga illustration
(cel-shaded linework, expressive eyes, dynamic anime-key-visual
composition) — not photorealistic, not generic silhouettes. The article
names a real franchise and character critically (fair-use commentary); the
cover image should match that specificity rather than deflect into
symbolism. Depict the character(s) doing something true to their canonical
role in the story the article discusses (the scene, mood, or moment the
article is actually analyzing) rather than an invented, unrelated pose.

---

## Standard Spec for Every Cover

- **Aspect ratio:** 16:9
- **Layout:** Full-bleed composition — the scene fills the entire frame. No
  reserved blank areas.
- **Opening line of every prompt:**
  `Create a cinematic 16:9 anime-style key visual for an article titled "[ARTICLE TITLE]," featuring [NAMED CHARACTER(S)] from [FRANCHISE].`
- **Closing line of every prompt:** an anime-art-quality descriptor (e.g.
  "Detailed cel-shaded anime illustration, dynamic linework, vibrant color
  grading, key-visual composition.").
- **No text, ever — hard constraint.** The image generator renders text,
  letters, numbers, signage, and logos as garbled artifacts. Never imply a
  title treatment, caption, sign, book cover, poster text, or nameplate. If a
  scene naturally suggests a text-bearing object, drop it or mark it
  explicitly blank/unmarked.
- **Name the character(s) and franchise explicitly in the prompt**, and
  describe their canonical design (hair, outfit, signature pose/expression)
  so the render is recognizably them, not a generic figure.

---

## The 12 Rules (apply in this order of importance)

1. **Lead with composition/purpose, not subject.** Open with what kind of
   image this is (anime key visual, poster-style character art, dynamic
   action still) and how it's framed.
2. **Character and mood together.** State who the character is and the
   emotional beat of the scene in the same breath — the article's thesis
   should be legible in the character's expression or pose.
3. **Think in layers.** Foreground (character) → midground → background, for
   automatic depth.
4. **One clear focal point.** The named character (or a small named group
   when the article is genuinely about their dynamic) — never a crowded
   ensemble shot unless the article is explicitly comparative.
5. **Specify lighting explicitly.** Name a lighting style (see bank below);
   vague prompts get flat lighting.
6. **Use a controlled color palette.** Name 2–3 specific colors that echo the
   franchise's actual palette or the article's mood.
7. **State scale.** Explicit scale/framing language (close-up, waist-up,
   full-body, wide shot) so the composition is unambiguous.
8. **Add environmental storytelling.** Background details should place the
   character in a setting true to their story (their canonical setting, or
   the specific scene/arc the article discusses).
9. **State the image's purpose/format** (key visual, poster-style character
   art, dynamic still) — the model understands these layouts well.
10. **Use quality descriptors sparingly.** A few precise terms beat a wall of
    "masterpiece, 8k, ultra-detailed."
11. **Mention depth explicitly** (atmospheric perspective, depth of field,
    volumetric fog/haze, dynamic action lines) — this separates flat AI
    images from professional key art.
12. **Fill the frame.** Full-bleed, no reserved blank zones for text overlay.
13. **Favor anime/manga illustration style over photorealism.** Describe the
    render explicitly as anime-style: cel-shading, clean linework,
    expressive/stylized eyes, dynamic anime-key-visual framing. Avoid
    photographic language (film grain, DSLR, bokeh) — this is illustration,
    not photography.

**The thumbnail test:** would this still be striking and instantly
recognizable as this character/franchise as a small thumbnail? If not, it's
missing a clear silhouette, a recognizable design detail, a tight palette, or
visual hierarchy — fix the prompt, don't pile on adjectives.

---

## Prompt Construction Formula

```
[Purpose + format: anime key visual]
[Full-bleed composition note]
[Named character(s) + franchise + canonical design detail — the one focal point]
[Supporting environment, foreground → midground → background]
[Lighting]
[Mood / expression tied to the article's thesis]
[Color palette — 2–3 named colors, franchise-appropriate]
[Scale / framing]
[Environmental storytelling detail tied to the character's actual story]
[No-text call-out, if the scene has any object that could imply text]
[Anime-illustration quality descriptor, used sparingly]
```

---

## Reference Banks

**Composition / purpose openers:**
anime key visual · poster-style character art · dynamic action still ·
rule-of-thirds composition · low-angle heroic perspective · close-up
character portrait · dynamic diagonal composition · Blu-ray box art
composition

**Lighting:**
cinematic anime lighting · volumetric lighting · golden hour · cold
blue-hour light · dramatic backlighting · moonlit atmosphere · overcast
diffused lighting · flickering neon glow · atmospheric haze

**Scale / framing:**
close-up portrait · waist-up · full-body · wide establishing shot · dwarfed
by the environment · dynamic low-angle hero shot

**Depth:**
atmospheric perspective · foreground framing · depth of field · volumetric
fog · layered environment · dynamic speed lines · aerial perspective

**Quality descriptors (pick 2–3 max):**
detailed cel-shaded anime illustration · dynamic linework · vibrant anime
color grading · key-visual composition · expressive eyes · clean digital
inking

---

## Worked Example

**Article:** "Light Yagami's Moral Collapse as Rationalized Villainy" (Death
Note character study)

**Generated prompt:**

> Create a cinematic 16:9 anime-style key visual for an article titled "Light Yagami's Moral Collapse as Rationalized Villainy," featuring Light Yagami from Death Note. Full-bleed composition — the scene fills the entire frame with no reserved blank areas. Light stands alone at a rain-streaked window at night, in his school uniform, sharp cold eyes and a faint, self-assured smile, the Death Note held closed in one hand. In the midground, scattered papers and a dim desk lamp cast long shadows; through the window in the background, a city skyline blurs into cold, wet neon. His expression carries quiet, chilling conviction — a mind certain of its own righteousness. Lighting is cold blue-hour light mixed with a single warm desk-lamp glow, palette of deep navy, charcoal grey, and a single warm amber accent. Framed waist-up, with the vast city stretching out behind him. No text, signage, or logos anywhere in the frame. Detailed cel-shaded anime illustration, dynamic linework, vibrant anime color grading, key-visual composition, expressive eyes.

Notice this prompt names the character and franchise up front, describes
Light's canonical design (uniform, cold expression, the Death Note itself),
and renders the whole scene as anime illustration rather than photography —
the cover is instantly recognizable as Death Note's Light Yagami, matching
the article's specificity.

---

## Agent Workflow

When generating a cover image prompt for a new article, follow these steps in
order:

1. **Read the article title/topic** and identify the specific named
   character(s) and franchise at the center of the article's thesis.
2. **Pick the character(s) to depict.** Usually the single character the
   article is about; a small named group only when the article is
   explicitly comparative or about their dynamic together.
3. **Recall their canonical design** — hair, outfit, signature expression or
   pose — and describe it concretely so the render is recognizably them.
4. **Choose a mood/expression** that matches the article's emotional angle
   (defiant, isolated, triumphant, quietly cracking) and 2–3 colors that
   reinforce it, ideally echoing the franchise's actual palette.
5. **Ground the scene in their actual story** — the setting or moment the
   article discusses — rather than an invented, unrelated backdrop.
6. **Build the prompt** using the formula above, in order, describing it as
   anime/manga illustration (cel-shading, linework, expressive-eyes
   language), never as live-action photography.
7. **Scan for text-bearing objects** and either cut them or mark them
   explicitly blank/unmarked.
8. **Run the thumbnail test** before finalizing — is this instantly
   recognizable as the character/franchise at thumbnail size?
9. **Confirm the spec**: 16:9, full-bleed, opening line states the article
   title verbatim and names the character(s) + franchise, canonical design
   details present, no text/letters/numbers/logos in the image, rendered as
   anime illustration rather than photorealistic.
