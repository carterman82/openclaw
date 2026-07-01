# IMAGE_GENERATOR.md

## Purpose

This file governs how cover image prompts are generated for catfancast.com articles. It exists so every cover feels like a premium editorial/nature-photography visual instead of generic AI art. Use this alongside `STYLE.md` (which governs the article copy) — this file governs the **image prompt** handed to the image generation API.

**Subject scope:** real cats only. Photorealistic or painterly depictions of real domestic-cat breeds, behaviors, anatomy, and named historical real cats are the entire visual world of this site. Fictional/copyrighted cat characters are out of scope — see "Agent Workflow" step 5.

---

## Standard Spec for Every Cover

- **Aspect ratio:** 16:9
- **Layout:** Split composition — left ~35–40% reserved as clean negative space for the headline/site branding overlay; right ~60–65% holds the cinematic scene.
- **Opening line of every prompt:**
  `Create a cinematic 16:9 cover illustration for an editorial article titled "[ARTICLE TITLE]."`
- **Closing line of every prompt:** a negative-space instruction (never "no text" — instead describe the space the text will occupy).

---

## The 12 Rules (apply in this order of importance)

1. **Lead with composition/purpose, not subject.** Open with what kind of image this is (editorial cover, movie poster, hero banner) and how it's framed — not "a boy on a beach."
2. **Mood before objects.** State the emotional goal of the scene before listing what's in it. AI converts emotion into lighting/composition surprisingly well.
3. **Think in layers.** Describe foreground → midground → background. This creates automatic depth.
4. **One clear focal point.** Pick a single hero subject. Everything else supports it — never list five "main" things.
5. **Specify lighting explicitly.** Vague prompts get flat lighting. Always name a lighting style (see bank below).
6. **Use a controlled color palette.** Name 2–3 specific colors, never just "colorful."
7. **State scale.** Use explicit scale language so large elements actually read as large.
8. **Add environmental storytelling.** Every background detail should hint at a story, not just exist.
9. **State the image's purpose/format** (editorial hero image, key visual, poster) — the model understands these layouts well.
10. **Use quality descriptors sparingly.** A few precise terms beat a wall of "masterpiece, 8k, ultra-detailed, amazing."
11. **Mention depth explicitly** (atmospheric perspective, depth of field, volumetric fog) — this is what separates flat AI images from professional ones.
12. **Describe negative space instead of forbidding text.** "Generous negative space for editorial headlines" works far better than "no text."

**The thumbnail test:** before finalizing a prompt, ask — would this still be striking as a small thumbnail in search results or social media? If not, it's missing a clear silhouette, a single focal point, a tight palette, or visual hierarchy. Fix the prompt, don't just add adjectives.

---

## Prompt Construction Formula

Build every prompt in this order:

```
[Purpose + format]
[Composition / split-layout note]
[Main subject — one focal point, named or described as fits the scene]
[Supporting characters/environment, foreground → midground → background]
[Lighting]
[Mood]
[Color palette — 2–3 named colors]
[Scale]
[Environmental storytelling detail]
[Negative space instruction for headline]
[Art style + rendering quality, used sparingly]
```

---

## Reference Banks

**Composition / purpose openers:**
editorial magazine cover · theatrical movie poster · hero banner composition · rule-of-thirds composition · establishing shot · low-angle cinematic perspective · symmetrical composition · dynamic diagonal composition · premium website hero image · Blu-ray key visual · AAA game splash screen

**Lighting:**
cinematic lighting · volumetric lighting · golden hour · soft rim lighting · dramatic backlighting · moonlit atmosphere · overcast diffused lighting · glowing ambient light · global illumination · atmospheric haze

**Scale:**
towering · colossal · endless horizon · immense · dwarfing the characters · stretching into the distance

**Depth:**
atmospheric perspective · foreground framing · depth of field · volumetric fog · layered environment · aerial perspective

**Quality descriptors (pick 2–3 max):**
highly detailed digital painting · premium concept art · cinematic color grading · professional key visual · production-quality illustration · sharp focus

---

## Worked Example

**Article:** "Maine Coon Size: The Genetics and History Behind the Largest Domestic Breed"

**Generated prompt:**

> Create a cinematic 16:9 cover illustration for an editorial article titled "Maine Coon Size: The Genetics and History Behind the Largest Domestic Breed." The composition should be split with bold magazine-style typography on the left and a hero nature-photography scene on the right. A massive long-haired brown-tabby Maine Coon stands in profile on a weathered wooden porch railing, full body visible, lynx-tipped ears erect, plumed tail draped behind. A smaller domestic shorthair cat sits on the porch floor in the midground for scale contrast, eclipsed by the Maine Coon's body length. Behind them, a New England farmhouse and pine forest recede into soft morning mist. The atmosphere should feel quiet, grounded, and faintly majestic, with soft directional golden-hour backlighting, warm earth tones (amber, deep forest green, weathered grey), reflective dew on the railing, and a premium National Geographic-style aesthetic. Leave generous negative space on the left for headlines and article branding. Highly detailed photorealistic illustration, cinematic color grading, sharp focus, professional editorial cover design.

Notice how this prompt hits every rule: format stated first, split layout, one focal subject as the hero (the Maine Coon), a layered scene (Maine Coon → smaller cat for scale → farmhouse → forest), explicit lighting and palette, explicit scale (smaller cat for size contrast — never just say "big," show the comparison), environmental storytelling (porch + New England backdrop tied to the breed's Maine origins), and negative space described rather than forbidden.

---

## Agent Workflow

When generating a cover image prompt for a new article, follow these steps in order:

1. **Read the article title/topic** and identify the breed, behavior, anatomical feature, condition, or named real cat at the center of the article's thesis.
2. **Pick one focal point** — usually a single cat (or the named real cat the article is about). Resist the urge to fill the frame with multiple cats unless the article is explicitly comparative or about a multi-cat behavior (e.g. allogrooming).
3. **Choose a mood** that matches the article's emotional angle (curious, regal, quietly powerful, playful, melancholic for end-of-life care pieces, scholarly for historical pieces) — this drives lighting and color choices.
4. **Choose 2–3 colors** that reinforce that mood. Cats benefit from grounded natural palettes — golden hour, cool overcast, warm interior lamplight, deep forest, soft window light.
5. **Real cats only — name the breed, describe the cat physically.** Use the actual breed name (e.g., "a chocolate-point Siamese," "a blue British Shorthair on a windowsill," "a torbie Maine Coon mid-stretch"), and for historical real cats use their name + accurate physical description ("Tama the calico stationmaster wearing her conductor's cap at Kishi Station"). **NEVER depict copyrighted fictional cat characters** — no Garfield, Hello Kitty, Pusheen, Tom (Tom & Jerry), Jiji, Luna, Cheshire Cat, Crookshanks, Mrs. Norris, Salem, Snowbell, the Cat in the Hat, anime cat characters, or any cat owned by a studio/publisher/creator. Named real cats from history (Tama, Larry, Stubbs, Dewey, Unsinkable Sam) are fine — they are real animals, not copyrighted characters.
6. **Build the prompt** using the formula above, in order.
7. **Run the thumbnail test** before finalizing — if it fails, fix the focal point/palette/silhouette rather than piling on adjectives.
8. **Confirm the spec**: 16:9, split layout, negative space line included, opening line states the article title verbatim, no fictional/copyrighted cat character anywhere in the prompt.