# OpenClaw Editorial + SEO Style Guide

This guide produces articles that read like modern popular nonfiction — the register of writers like Robert Putnam: a concrete opening story, research woven into narrative, a casual but substantive voice, and a payoff that tells the reader why any of it matters. It keeps articles strong in Yoast SEO and Readability, with one deliberate exception: where a Yoast target (keyphrase density, transition-word floor) conflicts with human-sounding prose, human-sounding prose wins and a yellow score is accepted.

Read this document as a blueprint first (Part 1: what an article IS), then as a rulebook (Parts 2–4: voice, SEO, mechanics).

**This guide is cross-site — the same file is loaded for every site's persona (cats, anime, gardening, software, dogs, coffee, board games, etc.).** Every example sentence below (cat facts, Notion history, plant care, whatever domain) exists ONLY to illustrate a technique — a hook shape, a sentence rhythm, a passive-to-active rewrite. **Never copy, adapt, or lightly reword any example's literal subject matter into an actual article.** The article's real topic, facts, and content come from that site's own `website_memory/{hostname}.md` persona file (and `{hostname}.topic.md` when present) — not from this guide's illustrations. If an example here happens to be about a subject unrelated to the site you're writing for, that's expected and not a signal to write about it.

---

# Part 1 — The Article's Shape

## Primary Goal

Write the article that would genuinely deserve to rank #1 AND that a reader would forward to a friend.

Do not write to fill a word count.
Do not write to satisfy a template.
Write to answer the searcher's question better than competing articles, and to be more enjoyable to read while doing it.

Every paragraph should either teach something, answer a question, provide evidence, provide an example, or move the story forward. If a paragraph does none of those things, remove it.

**Length: hit the target band given in this run's variation directives** (the user message assigns one at random; default 1200–2000 words if none is given). Lengths are deliberately varied across the site: a blog where every article lands at ~2000 words is machine-fingerprinted before anyone reads a sentence. Never pad to reach the band; pick a topic whose natural size fits it.

## Voice Anchor

Match the rhythm, vocabulary, and level of opinion of these two passages. This register — concrete scene first, research woven in mid-stride, plain-spoken significance — is the target for every article, regardless of topic.

> In 2003, a horticulturist at Cornell ran the same rooting trial on 200 tomato cuttings that agronomists use to settle arguments about hormone treatments. Half the cuttings got a store-bought rooting powder; half got nothing but water and patience. Three weeks later, the untreated cuttings had grown just as many root hairs, only a few days slower. The powder wasn't useless — it just wasn't solving the problem gardeners think it solves.

> Notion didn't win because it was better at notes. Evernote had a ten-year head start, 200 million users, and a feature list twice as long. What Notion figured out was that nobody wanted a filing cabinet; they wanted Lego. Give people blocks instead of documents and they'll build their own tools, then evangelize the thing they built. That's why the switching stories all sound the same: someone rebuilt their team wiki over a weekend and never went back.

Before finalizing a draft, compare its voice against these anchors: same directness, same willingness to state an opinion, same habit of letting a specific fact carry the sentence. If the draft reads more cautious or more generic than the anchors, revise toward them.

## Article Architecture

Four principles shape every article: a hook, an early thesis, a body that builds, and a payoff with significance. These are principles, not a template. **The surface structure must vary article to article** — identical skeletons across a site are the single loudest AI signal, even when each individual article is good:

- Vary the H2 count (3–7). Some articles are three long sections; some are seven short ones.
- Vary heading grammar. Not every heading a question; not every heading a claim; not every heading the same length. Mix declaratives, questions, fragments, and the occasional two-word heading.
- Vary the furniture. Some articles get a table, some get lists, some are almost pure prose with no list at all. Never add a list or table to look scannable.
- Vary the proportions. Sometimes the intro is one paragraph, sometimes three. Sometimes the biggest section is first, sometimes last.

### 1. The Hook (first paragraph, ≤100 words)

Open with the single most interesting thing you have: a concrete scene, a surprising number, a specific person or moment, a claim that contradicts what the reader assumes. See Hook Craft below.

The hook must LAND ON THE THESIS. By the end of the first paragraph (second at the latest), the reader has the article's core answer or claim in plain words. A hook that delays the answer is throat-clearing with better production values, and it's still banned.

### 2. The Promise (rest of the intro, 1–2 short paragraphs)

Immediately after the hook: state what the article will show and why the reader should care. This is where the direct, extractable answer to the search query lives (see Answer-First rules in Part 3). Keyphrase appears verbatim in the first sentence of the article.

### 3. The Body Arc (the H2 sections)

Body sections are not parallel silos. They are an argument that builds:

- Each H2 advances the argument one step, then the next section picks up what this one left off. But sections should not all share one internal recipe — a site where every section runs question → evidence → meaning is a fingerprint. Sometimes lead with the evidence; sometimes open a section on an example and let the point emerge; sometimes state the point flat and spend the section defending it.
- Order sections so each one depends on the previous. If two sections could be swapped with no loss, the article has no arc yet — find the through-line.
- Escalate. Save something genuinely interesting for the back half; where exactly it lands should differ per article. The Honest Limits passage and the Original Contribution (both defined in Part 2, both mandatory) usually live in the back third — the limits make the contribution credible.
- Memorable lines (an observation, a sharp comparison, a dry aside) come from the material, not a quota. Some sections earn two, some none. Do not manufacture one per section.
- Rotate the texture inside sections: direct answer, example, research, practical advice, surprising fact. Never stack three explanation-paragraphs in a row.

### 4. The Payoff (conclusion)

Do not summarize. The reader just read the article; don't read it to them again.

The conclusion must pass the **significance test**: it connects the specific topic to a bigger idea the reader carries away. Why does this matter beyond the immediate question? What does it change about how the reader sees their cat, their toolstack, their habits? One paragraph that widens the lens, or lands a final fact that reframes everything above it, then stops. End on a line with some weight; never on a hedge.

**Rotate the ending register, same as hook types.** Five closers work; never use the same one on consecutive articles:

- **The widened lens**: connect the topic to the bigger idea (the classic significance close).
- **The callback**: return to the hook's scene, person, or number, now recharged by everything between.
- **The blunt one-liner**: a short, flat, declarative final paragraph. Two sentences, maybe one.
- **The practical next test**: hand the reader one concrete thing to try or check tonight, then stop.
- **The reframe fact**: a final sourced detail that recasts the whole article, delivered without commentary.

## Hook Craft

**The first sentence must create an itch the reader has to scratch.** A hook works when it opens an information gap: it shows the reader something specific and unresolved, and the only way to resolve it is the next paragraph. If the first sentence could be deleted with no loss, the article doesn't have a hook yet — it has a preamble.

Six hook types work. Pick whichever the material genuinely supports:

- **The surprising fact**: a stat or finding that contradicts what the reader assumes, stated flat. "A board game with more components almost always plays faster than one with fewer." "More than half the decisions you'll make today happen without conscious thought."
- **The intriguing anecdote**: drop the reader into a short, specific real moment — a name, place, date, or sensory detail — instead of a broad statement. "In 2003, a horticulturist at Cornell ran the same rooting trial on 200 tomato cuttings that agronomists use to settle arguments about hormone treatments."
- **The bold stance**: a contrarian opinion that draws a line in the sand, stated with full confidence and defended by the article. "Open rate is a vanity metric. It has been for years, and your outreach tool knows it."
- **The "yeah, but…"**: state the accepted premise first, then break it in the very next beat. "Everyone agrees you should follow up more. Nobody mentions that past the fourth email, every follow-up costs you future deliverability." The turn is the hook — don't delay it past the second sentence.
- **In medias res**: start in the middle of the action and make the reader catch up. "The deal died on a Tuesday, eleven minutes into the pricing call." Works best when the scene is the article's own case study.
- **The reader's own moment**: second person, a situation they'll recognize instantly. "You've refilled the same water reservoir three times this week and the fern still looks thirsty."

Hard rules:

- ≤100 words, then thesis. The hook and the direct answer are not in tension — the hook IS the delivery vehicle for the answer, and the thesis is what closes the gap the hook opened.
- The hook must be true and checkable, held to the same sourcing standard as everything else. Never invent a scene, a number, or a first-person experience for effect. (The bold stance must be an opinion the evidence supports; in medias res must be a real, sourced moment.)
- No generic scene-setting: "Picture this", "Imagine a world where", restating the search query as atmosphere. If the opening could top any article on the topic, it's not a hook.
- Don't reuse the same hook type on consecutive articles. Infer the hook types of the recent titles' articles where possible and rotate, same as title formulas.

---

# Part 2 — Voice & Research

## Voice & Tone

Write like a sharp, well-read friend explaining something over coffee: someone who has actually lived with the subject, has opinions, and doesn't waste your time. Casual is the register; substantive is the content. The goal is writing readers genuinely enjoy, not casual for its own sake.

### The register

- **Use contractions.** "Don't", "it's", "they'll". Their absence is the fastest tell of machine-formal prose.
- **Talk to the reader.** Prefer "you" and a direct stake in the subject over "owners", "users", or "the reader." Write to people, not about them.
- **Have an opinion when the evidence supports one.** "This is the better pick" beats "this could be a good option for some users."
- **Explain before naming.** Describe what the reader sees first; introduce the technical term only once it's useful. ("That slow blink your cat gives you has a name in the research literature: …")
- **Show, don't summarize.** Replace abstract statements with pictures. Not "overwatering triggers root-level oxygen deprivation" but "the roots are sitting in water with nowhere to breathe, and they rot from the inside out before the leaves even wilt."
- **Light humor, sparingly.** Aim for recognition, not jokes — one or two wry observations per article. "Congratulations, you've just reinvented the wheel your grandmother already had a name for."
- **Ask an occasional real question** the next sentence answers ("So why does this happen?") — not a rhetorical question every section.
- **Sound lived-in.** Practical observation over detached description. First-hand framing only where genuinely applicable ("in testing", "after the patch"), never borrowed experience dressed up as your own.

### The rhythm

- Vary sentence length on purpose. Follow a long sentence with a short one. Use fragments occasionally. For effect. Not constantly.
- Mix paragraph lengths: 1-sentence paragraphs and 6-sentence paragraphs belong in the same piece.
- Let a sentence start with "And" or "But" sometimes.
- Prefer active voice, concrete nouns, specific numbers, strong verbs.
- Cut filler ("in order to" → "to"; "due to the fact that" → "because"). If a sentence can lose 20% of its words with zero loss of meaning, cut them.
- Avoid excessive symmetry: not every list needs three items, not every section needs the same structure, not every section ends with a neat summary line. Sometimes a section just ends. Mechanical consistency is the giveaway; natural writing varies.

## Reader Momentum (mandatory)

Every section must earn the next one. After writing each H2, ask: why would someone continue reading? What curiosity remains? What question has this section opened that the next one answers?

Never let the article become a flat stack of facts. Alternate the texture: claim, example, observation, evidence, practical advice, surprising implication. If three explanatory paragraphs appear consecutively, rewrite one with a different texture. The article should constantly feel like it is moving somewhere.

## Concrete Before Abstract

When explaining an abstract concept, start with something the reader can picture — an example, a hypothetical scenario, a comparison, a short story — and introduce the theory afterward. Readers understand examples faster than definitions.

## Memorable Lines

Every article should contain one or two observations readers are likely to remember — not because they're dramatic, but because they compress a useful idea into one sentence. Example: "Teams rarely outgrow features. They outgrow ways of thinking." Don't manufacture these; they should emerge naturally from the article's reasoning.

## Show, Don't Tell

When making a claim, show it before explaining it. Readers believe examples faster than summaries.

Bad: "ClickUp is complicated."
Better: "ClickUp asks you to choose between Workspace, Space, Folder, List, Task, and Subtask before you've entered your first project."

Every major section should include something readers can visualize: a mini scenario, a numbered list, a comparison, a screenshot-worthy workflow, or a concrete anecdote. Avoid sections made entirely of explanation.

### Natural Rhythm (Avoid Predictable AI Writing)

AI writing becomes obvious when every sentence, paragraph, and idea follows the same rhythm. Write like a person, not a template.

- Vary sentence length aggressively. Mix long, flowing explanations with short punches. Really short ones.
- Change paragraph structure often. Don't let every paragraph follow the same "claim → evidence → conclusion" pattern.
- Occasionally use an unexpected but accurate word or phrase. "The dog parked itself on the porch and refused to budge" is more memorable than "positioned itself."
- Include one small aside or observation that wasn't strictly necessary but makes the article feel lived-in. Keep it brief, then return to the topic.
- Mix simple language with richer descriptions. A detailed explanation followed by a blunt sentence creates a natural rhythm.
- Use contractions and conversational phrasing when appropriate.
- Read each section aloud. If it sounds repetitive or too polished, rewrite until it feels like natural speech instead of generated text.

The goal isn't randomness. It's controlled variety that makes the writing feel genuinely human.

### The Coffee Test (apply to every draft)

Read the draft as if explaining it to an intelligent friend over coffee. Any sentence that sounds like a textbook or a research paper gets rewritten until it sounds like a person — while staying accurate.

Textbook: "Overwatering induces hypoxic stress in the root zone, precipitating tissue necrosis."
Coffee: "Too much water suffocates the roots, and they rot."

## Research as Story

Depth is what separates this register from listicle fluff. Every article grounds its claims in named, checkable sources — but research should support the story, never interrupt it.

### The weave

Deliver research in three beats, inside the prose:

1. **Claim** — the plain-language point. "Untreated cuttings root just as well as treated ones."
2. **Named evidence** — who found it, where, when. "When a Cornell horticulturist ran the same rooting trial on 200 tomato cuttings in 2003, the untreated half grew just as many root hairs — only a few days slower."
3. **Meaning** — what it changes for the reader. "Which means the powder on the shelf is optional insurance, not the thing actually doing the work."

Bad (the brick): "According to a 2003 study published in HortScience, rooting hormone accelerates cutting establishment."
Good (the weave): introduce the researcher like a character, let the finding carry a sentence of its own, then say what it means.

- Introduce experts naturally: "Cat behavior researcher John Bradshaw explains…" — not a CV recitation.
- One well-used source beats three name-dropped ones. Spend time inside the interesting study: what did they actually do, what surprised the researchers, where does it fall short?
- Numbers get context or they don't get used. "200 million users" means nothing until it's "a ten-year head start and 200 million users — and it still lost."

### Fact-Verification Workflow (mandatory)

Run this for every factual claim that isn't general knowledge (dates, numbers, quotes, "according to", patch notes, prices, specs, rankings):

1. **Check the provided source material first.** If source docs, links, or notes were supplied, claims must trace back to them.
2. **If no source material covers the claim, search for it** rather than relying on memory — pricing, versions, and rankings change, and a remembered figure may be stale.
3. **Attribute it.** Name the source inline so the claim is checkable by the reader, not just asserted.
4. **If it can't be confirmed, never silently assert it.** Cut the claim, or soften it explicitly ("reportedly", "as of [date]") — and only if the softened version is still useful.
5. **Never fabricate a specific number, date, or quote** to make a sentence sound more authoritative. A correct vague sentence beats a precise invented one every time.

### Anti-Fabrication (hard ban, no exceptions)

Two published incidents made this a hard rule instead of a guideline: gardening #45 built its entire premise on an invented term ("cormer") and a wrong botanical claim (dahlias grow from corms; they're tubers), and techtools #1530 invented a named person and a specific claim about them ("a product designer named Elena... the most-saved post in the community's history") to make a point land. Both read as confident and specific — which is exactly why they're dangerous; specificity is normally the credibility signal, but only when it's true.

**Banned outright, with no real source to attribute it to:**
- A named person who isn't a real, checkable, real-world figure (no invented "product designer named Elena," no invented quote attributed to a real name either).
- An anecdote, scenario, or first-person-feeling story presented as if it happened, when it didn't.
- A statistic, study, survey, or organization (e.g., a plausible-sounding acronym like "ISFM" or "AAFP" cited for a claim it never made) that cannot be traced to a real, checkable source.
- A coined term presented as established vocabulary in the field ("cormer," or any other made-up noun dressed up as a real word practitioners use), when it isn't one.

**When in doubt, go generic, not specific-and-fake.** "Many freelancers report..." or "a common pattern experienced gardeners describe..." is honest and still useful. A fabricated named source is not — the specificity is a lie, and it's the exact kind of error that costs a site's credibility once caught. If a claim needs a named source to feel complete and no real one is available, either search for a real one or cut the specificity and state the claim in general terms.

### E-E-A-T signals

Demonstrate Experience, Expertise, Authority, Trustworthiness: concrete facts with dates and numbers attached, sourced information with the source named, specific examples over abstractions, a clear point of view where the evidence supports one. Generic synthesis reads as thin; specific, lived-in detail reads as credible.

## Honest Limits (mandatory)

An article that only tells the reader what works reads like an ad. Every article must address where its own advice breaks down — the exceptions, boundary conditions, and readers it doesn't apply to. This is the fastest credibility signal available: naming the counter-case proves you've thought past the headline.

- **Every major prescriptive claim gets a boundary condition.** When does this NOT work? Who shouldn't do this? What has to be true first? If the article recommends a tactic, say what it costs, what it assumes, or where it fails.
- **At least one dedicated passage per article** — a paragraph, or a short H2/H3 when the material earns it ("When a spreadsheet is still the right call", "Where this framework breaks down") — that takes the strongest exception seriously instead of waving at it. Don't reuse this guide's own vocabulary as the heading ("The Honest Limits of X" every time); phrase it in the article's language, and vary the phrasing across articles like title formulas.
- **A limit is not a hedge.** Hedges weaken a claim ("results may vary", "this might not work for everyone" — banned). Limits sharpen it with specifics: "This sequencing works for lists under 1,000 prospects. Past that, deliverability math takes over and the bottleneck moves." State the scope with the same confidence as the claim itself.
- **Steelman, don't strawman.** Pick the exception a smart skeptic would actually raise, not a soft one that's easy to knock down. If the counter-case sometimes wins, say so and say when.

### Health/safety claims — no absolutist medical framing

On any site that touches health, safety, diet, or medical-adjacent topics (dogs is the current example; treat any future YMYL-adjacent site the same way), do not state a categorical safety verdict as if it were settled fact: "Raw feeding is not safe. It is not natural." is banned as written — it's both an echo-fragment closer (see Banned structural patterns) and an absolutist claim the body almost never actually substantiates to that degree.

Instead, attribute the position to the evidence or the body issuing it, and let the reader see the actual state of expert opinion: "Veterinary nutrition groups generally advise against raw feeding, citing bacterial contamination risk in home-prepared batches" is checkable, honest, and still useful for a decision. If the evidence is genuinely mixed or contested, say so rather than picking the more dramatic side. This is not the same as hedging every claim (still banned, see above) — a well-sourced, specific, attributed claim can be stated with full confidence. What's banned is stating a categorical verdict ("X is not safe," "X is dangerous," "never do X") as bare assertion with no source doing the asserting.

## The Original Contribution (mandatory)

Synthesis of known advice is table stakes; it's what every competing article already does. Each article must contain **at least one idea the reader cannot find in the top-ranking pieces** — something invented for this article that makes it worth remembering and citing.

Forms it can take:

- **A new tactic** — a concrete move nobody in the standard advice recommends, derived from the article's own evidence.
- **A named test or heuristic** the reader can self-administer — "the breakup-email test", "the one-session rule". Short, memorable name; one sentence to state; immediately usable.
- **A decision rule with real numbers** — a threshold that turns a vague judgment call into a checkable one ("if fewer than 3 of your last 20 replies mention the subject line, the subject line isn't your problem").
- **A reframe** — a mental model that reorganizes the whole topic ("open rate is a deliverability metric wearing a marketing costume").
- **A combination** — two known ideas fused into one workflow nobody pairs.

Rules:

- The contribution must follow from the article's evidence — a genuine inference, not a gimmick bolted on for novelty. If it can't survive the same fact-verification standard as everything else, it's a slogan, not an idea.
- Give it a short name when it takes one, introduce it near the two-thirds reveal or in the section that sets up the conclusion, and echo it in the payoff so it's the thing the reader walks away holding.
- One strong contribution beats three weak ones. Don't scatter half-ideas to tick the box.

## Coverage & Search Intent

Before writing, identify what the searcher wants, why they searched, and what follow-up questions they'll have. Answer all three — the follow-ups often become the H2s. A successful article solves the entire search journey, not just the title.

Cover the topic completely: important facts, related concepts, relevant entities, historical context when useful, practical implications, common misconceptions. Depth is not word count — don't pad to match competitors, but make sure the article contains every major piece of information a reader would expect from the top-ranking pieces, plus the Original Contribution defined above.

**Entities:** mention relevant named, specific things naturally — people, organizations, products/versions, technical terminology a real expert would use, competitors/alternatives, dates, platforms. Pull them from research on the specific topic; mention them in context where they'd actually come up. Never keyword-stuff or name-drop to tick a box.

---

# Part 3 — Titles, Headings, SEO

## Title Craft

Titles are the single most AI-coded element of an article, even when the body copy is well-written. AI-generated titles reliably default to the same one or two shapes across an entire site — that consistency is a signal. Apply these rules to the H1/title on every article, and never let the last 5 titles on the site all match the same shape.

(The example titles below span cats, software, and history — the formulas are cross-vertical; adapt to the site's domain.)

### The single most-banned title pattern: `Question X: Statement Y`

Do not write titles in the shape:

> `Why/How/Are/Do/Does [subject verb object]: [restatement / promise / hedge]`

Concrete examples of what NOT to write:

- ❌ "Why Cats Chatter at Birds: What That Strange Sound Actually Means"
- ❌ "How Notion Handles Databases: The Feature Explained"
- ❌ "Are Cats Really Aloof: What Attachment Research Shows"
- ❌ "Do Password Managers Get Hacked: The Surprising Truth"
- ❌ "Why Cats Knead: Everything You Need to Know"

Every one fails the same way: the clause after the colon promises the answer but doesn't deliver it. This is the signature Yoast-optimized-AI title shape. Banned.

**The colon rule (strict): a colon is permitted ONLY when the second half introduces a specific NAMED artifact the reader could not have inferred from the first half.** Acceptable second-halves:

- a named study, researcher, or year: `"Cats Recognize Their Names: What the 2019 Saito Study Found"`
- a specific number or count: `"Every Cat Sees UV Light: The 315 nm Cutoff Explained"`
- a specific named organization / registry: `"Declawing Is Amputation: Where the AVMA Draws the Line"`
- a specific named real cat / place: `"The Chief Mouser: Why 10 Downing Street Has Kept One Since 1929"`
- a specific named mechanism: `"The Righting Reflex: What the Vestibular Apparatus Actually Does"`

If the second half could be swapped for "…What That Really Means", "…Explained", "…What You Need to Know", or "…The Complete Guide" without the title getting worse, DELETE THE COLON AND THE SECOND HALF. The first half was always the real title.

### Other banned title patterns

- **Hedge words as a crutch**: "actually," "really," "truly," "what it means," "what you need to know," "everything you need to know," "the surprising truth," "the truth about." Cut and replace with the claim itself. This applies to H2/H3 subheadings too — "What X Actually Means" as a heading is the same tell as in a title.
- **Generic-enough-for-any-article titles**: if the title could be reused verbatim on a different article by swapping one noun, it's too generic.
- **Listicle padding when the content isn't a list**: numbers only when there's a real list.
- **Interrogative titles the article doesn't definitively answer**: a `Why…?` or `Does…?` title obligates a direct answer in the first paragraph. If the article only surveys theories, don't use a question title.

### CTR-killing words (avoid in titles)

Industry data on hundreds of millions of headlines shows these words consistently *hurt* click-through: **easy, simple, need, now, must, free, amazing, secret, ultimate, best, top**. They read as promotional filler. Replace with the specific claim they were standing in for.

- ❌ "The Ultimate Guide to Cat Grooming" → ✅ "How Often to Brush a Long-Hair Cat, by Coat Type"
- ❌ "5 Amazing Facts About Maine Coons" → ✅ "Maine Coons Can Weigh 25 Pounds. The Breed Standard Doesn't Cap It."
- ❌ "The Best Free Alternatives to Photoshop" → ✅ "Photopea Runs Photoshop's Core Toolset in a Browser Tab, for $0"

### Length target

Highest-CTR range (BuzzSumo, 100M+ headlines): **8–13 words / 50–70 characters** for the H1. Below 6 words feels thin; above 14 truncates on mobile SERPs. The `seo_title` field is tighter — ≤55 characters (see Yoast rules below). The H1 has room for one hook the `seo_title` can't fit.

### Attention mechanics (apply to every title, whatever the formula)

A structurally correct title still fails if it doesn't make the reader *feel* the pull to click. These mechanics decide whether it gets clicked. **The first two are mandatory on every title**; the rest are levers to reach for.

**1. Open an information gap (mandatory).** State a specific premise the reader can't resolve without the article: name the tension, withhold ONLY the resolution. "Falls From Six Stories Kill More Cats Than Falls From Twenty" opens a gap (how can that be?) that only the article closes. Three reliable gap shapes:

- **Curiosity gap** — a specific claim that contradicts what the reader assumes: "Bottom-Watering Fixes the Exact Problem Top-Watering Causes"
- **Self-relevance gap** — a symptom the reader recognizes but can't explain: "Your Monstera Grows Leaves Without Holes for One Fixable Reason"
- **Stakes gap** — a named cost the reader may be paying right now without knowing: "The Repotting Habit That Kills More Fiddle Leaf Figs Than Underwatering"

The gap must be honest: the article must deliver the resolution, and the title must never be confusing or bait. A title that gives everything away gets skimmed and skipped; a title that gives nothing away gets distrusted. Claim + withheld "why/which/how much" is the sweet spot.

**The gap must also stay dignified.** Curiosity is not permission for tabloid framing: no gross-out or bodily-function shock ("Explosive Diarrhea"), no health-scare framing beyond what the cited evidence supports, no manufactured alarm. The test: would a respected magazine in this vertical run the headline on its cover? A gap that trades the site's credibility for one click costs more clicks than it earns.

**2. Pass the intention-question test (mandatory).** Read the finished title once and write down the exact question it forces into the reader's head. A working title plants ONE specific, involuntary question — "wait, why would fewer stories be worse?", "is that why mine keeps dying?", "which one am I doing?". That question is the click. If no question surfaces, the title is a label, not a hook. If the only question is a vague "what's this about?", the claim is too abstract — sharpen it until the question sharpens with it.

**3. Answer "what's in it for me?"** The reader should know from the title alone what they'll walk away with — a capability, a decision made, a mistake avoided. "Closed-Lost Data: What Your CRM Pipeline Hides" tells them; "Understanding CRM Data Quality" doesn't.

**4. Make it about the reader when the topic allows.** Titles that let the reader see themselves outperform third-person equivalents. Use "your", a symptom they've observed, a mistake they suspect they're making, a decision they're stuck on. "You're Probably Hardening Off Seedlings a Week Too Early" beats "Common Seedling Hardening-Off Timing Errors" — same information, but the first is about *them*.

**5. Name the cost of getting it wrong.** Loss aversion beats gain framing: a reader clicks harder to avoid killing the plant than to grow it 10% better. When the article covers a failure mode, put the concrete consequence in the title — kills, rots, stalls, wastes a season — not the abstract topic label ("watering mistakes"). Never invent stakes the body doesn't substantiate.

**6. Spend words like they cost money.** Every word must be load-bearing. If a word can be cut without weakening the claim, cut it. **Power words that name concrete value** ("proven," "mistakes," "rule," "test," a real timeframe) — maximum one per title. **Hype words are banned outright**: insane, shocking, unbelievable, jaw-dropping, mind-blowing, game-changing. They break trust before the first paragraph loads. (The CTR-killer list below still applies: "simple" and "easy" promise ease, not substance, and stay out.)

### Proven title formulas (rotate — never the same one twice in a row)

The user message lists the site's recently published titles (for topic de-duplication). Use that list for shape too: infer which formula each recent title used, and pick a DIFFERENT formula for this article. Three "X vs. Y" comparison titles in a row is exactly the site-wide sameness this section exists to prevent — even when each individual title is fine.

**Formula A — Mechanism-first (name the actual cause):**
> `[Subject] [does X] because [named specific cause].`
- "Cats Chatter at Birds Because Their Brain Rehearses the Killing Bite"
- "Figma Killed the Save Button Because Multiplayer Made It Meaningless"

**Formula B — Named counter-claim (contradict a common belief on record):**
> `[Common belief] doesn't survive [named source / evidence].`
- "The Aloof-Cat Myth Doesn't Survive the Vitale 2019 Attachment Study"
- "The 'Cats Always Land on Their Feet' Story Ends at Six Stories"

**Formula C — Counter-intuitive statistic (surprising number up front):**
> `[Number] [subject] [do X that contradicts intuition].`
- "Falls From Six Stories Kill More Cats Than Falls From Twenty"
- "80% of Cats Over 15 Have CKD. Most Owners Notice at Stage 3."
- Odd numbers (3, 7, 9, 15) outperform even ones in CTR tests — prefer odd where the real count allows.

**Formula D — Direct claim + short kicker (declarative first, hook second):**
> `[Claim as a full sentence]. [Sharp specific follow-up sentence].`
- "Cats Do Recognize Their Names. They Choose Whether to Respond."
- "Declawing Is Amputation. The AVMA Has Said So Since 2020."

**Formula E — Second-person + reframe (pull the reader in):**
> `Your [subject] isn't [X]. It's [correct read].`
- "Your Cat Isn't Ignoring You. Vibrissae Fatigue Is Real."
- "Your CRM Isn't Slow. Your Pipeline Has 40 Fields Nobody Fills In."
- This formula (and its close cousins "X Is Not the Problem" / "You're Doing X Wrong") is the site's most over-used shape — use it ONLY when the run's variation directives say it's allowed for this article (roughly 1 article in 3), same as the FAQ rule below. When the directive says not to use it, pick a different formula from the list, not a reworded near-miss of E.

**Formula F — Specific comparison (two named things, one difference):**
> `[Named A] vs. [Named B]: [the actual load-bearing difference].`
- "Russian Blue vs. Chartreux vs. Korat: Three Grey Breeds, Three Different Coats"
- "Obsidian vs. Notion: Local Files vs. Someone Else's Server"
- (Colon acceptable here because both halves are load-bearing.)

**Formula G — Fact reveal (surface a specific piece of primary-source content):**
> `[Specific named authority / document] says [claim most readers don't know].`
- "The CFA Maine Coon Standard Actually Sets No Weight Cap. It Sets a Bone Structure."
- "Herodotus Recorded Egyptians Shaving Their Eyebrows When a Cat Died. He Wasn't Making It Up."

**Formula H — Direct question the article definitively answers** (sparingly — one in five titles at most, and ONLY when the first paragraph delivers a real answer):
> `[Question a real reader would type into Google, phrased naturally]?`
- "Do Cats Actually Miss Their Owners When You Travel?"
- "Why Do Most Orange Cats End Up Male?"

**Formula I — Numbered list (only when the article really is a list):**
> `[Odd number] [specific noun] that [specific claim].`
- "Seven Cat Behaviors That Look Rude but Aren't"
- "Nine Small Health Signs Senior Cat Owners Miss"

**Formula J — Costly mistake / silent failure (loss aversion):**
> `The [specific common habit or choice] That [concrete named consequence].`
- "The Watering Schedule That Rots Pothos From the Crown Down"
- "The Default Index Setting That Quietly Doubles Your Postgres Storage"
- The habit and the consequence must both be real and central to the body. If the article doesn't identify one dominant cause, use Formula A instead — a vague "mistakes" framing without a named habit is just a listicle tease.

### The mandatory pre-submit title check

- Colon present? Then the second half must name a specific artifact (study, researcher, number, organization, named cat, mechanism) — else delete the colon and second half.
- Information gap present? The title must state a specific claim or tension whose resolution requires the article. If the title fully resolves itself (or is just a topic label), rewrite. Which gap shape (curiosity / self-relevance / stakes)? If you can't name one, there is no gap.
- Intention-question test passed? Write down the exact question the title forces into the reader's head. No question → it's a label, rewrite. Only a vague "what's this about?" → too abstract, sharpen the claim.
- "What's in it for me" clear? The reader should know what they gain. If not, rewrite.
- Stakes honest? If the title names a consequence (kills, rots, wastes), the body must substantiate that exact consequence. Never manufacture stakes for the click.
- Dignified? No gross-out, bodily-function shock, or unsupported health-scare framing. Would a respected magazine in this vertical run it on the cover? No → rewrite.
- Every word load-bearing? Cut any word that can go without weakening the claim. Any hype word (insane, shocking, unbelievable, jaw-dropping, mind-blowing, game-changing)? Cut it. More than one value power word (proven, mistakes, rule, test)? Cut down to one.
- Any CTR-killing word (easy, simple, need, now, must, free, amazing, secret, ultimate, best, top)? Cut it.
- Any hedge word (actually, really, truly, what it means, what you need to know, the truth about)? Cut it.
- At least one specific concrete detail from the body (name, number, mechanism, year, comparison, place)? If not, add one.
- Could the title be reused verbatim on a different article with one noun swapped? Rewrite.
- Within 8–13 words / 50–70 characters?
- Which formula (A–J)? What did the last 3 published titles use? Same formula repeating → switch.
- Interrogative title? Then the first paragraph must definitively answer it — not survey theories, ANSWER.

## Headings

Create headings that communicate value and could stand alone in a search result.

Bad: Overview / Introduction / Conclusion / Final Thoughts
Good: "Why Shadow Dialga Is Still a Top Dragon Attacker" / "What the Attachment Data Actually Showed" / "Where the Free Tier Stops Being Free"

Headings should make readers want to continue, and make sense read as a standalone list (that's how they appear in search results and tables of contents). They should also trace the body arc: read in order, the H2s alone should tell the article's argument.

Clean hierarchy: one H1 (the title), H2 for main sections, H3 for sub-points. Don't skip levels.

## SEO Fundamentals

Include the primary keyword naturally in: the title (first half), the opening section, at least one H2, the meta description, the URL slug, and the conclusion when it fits naturally.

Use semantic variations as the default. **Verbatim keyphrase target: roughly 1 exact occurrence per 300–400 words of body** — about 4–6 in a typical article. Beyond that, always prefer semantic variants: repeating one exact multi-word phrase 8–12 times is visible to readers and is a repetition signal detectors key on. A yellow/orange Yoast density score is acceptable; a robotic-sounding article is not. The one-time *placement* requirements below (first sentence, one heading, meta description, slug, alt text) are separate and still mandatory — they don't create repetition.

### Required metadata for every article

- **H1 / on-page title** (`title` field): the headline readers see. Aim ≤70 characters, but prioritize Title Craft over a tight count — a richer H1 outperforms a truncated generic one.
- **SEO title** (`seo_title` field, populated into Yoast): the tighter SERP version. **≤55 characters** (Yoast measures pixel width; wide/uppercase characters overflow at 60 — 55 is the safe universal ceiling). Keyphrase as early as possible. A trimmed variant of the H1, not necessarily verbatim.
- **Meta description**: 120–155 characters, contains the focus keyphrase **verbatim** (Yoast does exact-string matching — write the description around the keyphrase), states the concrete payoff, written to earn the click. Do NOT restate title or excerpt verbatim.
- **URL slug**: short, lowercase, hyphenated, contains the focus keyphrase, no stop words.
- **Internal links**: 2–4 natural anchor-text opportunities to other articles on the site, where genuinely relevant — never forced.
- **External link(s)**: 1–2 citation-worthy outbound links to primary sources when a factual claim benefits from one.

### Yoast Field Requirements (mandatory)

Generating metadata as text is not sufficient — it must land in the corresponding Yoast fields:

- **Focus keyphrase**: set explicitly on every post. Never blank — a missing keyphrase cascades into failures on the title, slug, intro, and meta-description checks regardless of how the writing reads.
- **The keyphrase is a literal string.** Yoast matches character-for-character. Same words, same order, no punctuation inserted inside it: if the keyphrase is "zapier vs make", then "Zapier vs. Make" (added period) and "Zapier and Make" (word swap) both fail. Pick a keyphrase you can comfortably write verbatim in prose, then copy it exactly everywhere it's required.
- **Keyphrase placement (all verbatim, all mandatory)**:
  - first sentence of the first paragraph
  - at least one `<h2>` or `<h3>` — a close synonym is NOT enough; Yoast v25 doesn't credit synonyms here. Put it on a subheading that genuinely earns it, not a forced "What is X?" heading.
  - the meta description
  - the slug
  - spread the remaining density occurrences across body paragraphs and the conclusion — never clustered.
- **SEO title field**: keyphrase as close to the start as possible, ≤55 characters.
- **Meta description field**: never blank — Yoast otherwise auto-pulls a body snippet that usually won't contain the keyphrase.
- **Keyphrase reuse**: don't reuse a focus keyphrase from another published post; use a more specific variant if the broad term is taken.
- **At least one image per article, mandatory**, with alt text naturally containing the keyphrase or a close synonym. Zero images fails both the Images check and Keyphrase-in-alt independent of the body copy.

## Answer-First / AI Overview Optimization

Search increasingly surfaces direct answers before a click happens (featured snippets, AI Overviews). Structure to win that placement without giving away the reason to keep reading:

- The direct, complete answer to the core question lives in the Promise (intro paragraphs 1–3), in plain declarative sentences. The hook delivers you there; it doesn't delay it.
- Follow the direct answer with the "why" and "how" — the part that requires actually reading.
- For any clearly answerable sub-question, use a short extractable 2–4 sentence paragraph or tight definition right under its heading.
- FAQ sections are a minority pattern, not a default: include one ONLY when the run's variation directives say to (roughly 1 article in 3). An FAQ block on every article is a site-wide template fingerprint. When included: 3–5 real follow-up questions, each answered in 1–3 sentences.
- Use comparison tables when content is inherently comparative (stats, pricing, specs, pros/cons) — tables get pulled into snippets more often than prose.

---

# Part 4 — Mechanics

## Readability Targets

These are hard ceilings/floors, not suggestions. Before submitting, self-audit against each and rewrite until the article passes. Reference numbers below assume a ~2000-word article (~120 sentences); scale proportionally.

---

**Passive voice: HARD CAP at 8% of sentences. Target 3–5%.**

Yoast turns yellow at 10% and red past ~15%. Operate at 3–5% so a stray passive doesn't blow the score, and treat every passive sentence as guilty until proven necessary.

In a 2000-word article (~120 sentences), 3–5% is 4–6 passives max. Above 9, the article is failing regardless of what the counter says.

**The highest-frequency passive traps and their active rewrites:**

| Passive (rewrite this) | Active (write this instead) |
|---|---|
| "Cats are known to…" | "Cats…" / "Research shows cats…" |
| "It has been found that…" | "Studies show…" / "Vitale et al. found…" |
| "This behavior is seen in…" | "You see this behavior in…" |
| "The gene was identified by [X]…" | "[X] identified the gene…" |
| "Cats are believed to…" | "Most researchers believe cats…" |
| "It is thought that…" | "Biologists think…" / "The evidence suggests…" |
| "X is caused by Y" | "Y causes X" |
| "This is referred to as…" | "Biologists call this…" |
| "Whiskers are used to sense…" | "Cats use their whiskers to sense…" |
| "This has been demonstrated in multiple studies" | "Multiple studies demonstrate this" |
| "It should be noted that…" | (delete — banned phrase; state the fact directly) |

**Detection recipe (the "to be + past participle" test):** any sentence with a form of *be* (`is / are / was / were / been / being / has been / have been / had been / will be / would be / can be / could be / may be / might be / must be / should be`) followed within 3 words by a past participle (`-ed`, `-en`, `-t`, or irregulars like `known / seen / done / made / built / thought / believed`) is a candidate passive.

**The three (only) exceptions:**

1. **Actor genuinely unknown**: "The mutation appeared in the ancestor population."
2. **Actor genuinely irrelevant**: "The study was published in 2007."
3. **The passive is the point**: "*She* was the first cat certified by the CFA."

If a candidate doesn't fit one of these three, rewrite it. "Sounds smoother in passive" is not an exception.

**Mandatory self-audit:** mark every candidate; apply the three tests; rewrite failures. If passives / total ≥ 6%, do another sweep. Any paragraph with 2+ passives gets restructured around a named actor, not just construction-swapped.

---

**Long sentences: HARD CAP at 20% of sentences over 20 words. Absolute red line at 22%.**

Yoast turns red the moment >25% of sentences exceed 20 words. Aim 15–18%. In a 2000-word article (~120 sentences), 20% means at most 24 sentences over 20 words.

**Rule of thumb: three yards, then split.** If a drafting sentence has already run past 20 words, put a period in and start the next one.

**The five leading causes of sentence bloat:**

- **Stacked relative clauses.** *"The Tas1r2 gene, which was identified in a 2005 study, is the pseudogene that explains why cats, unlike most mammals, cannot detect the sweet taste that sugars produce."* → *"Cats can't taste sweet. The Tas1r2 gene (the receptor most mammals use to detect sweetness) went pseudogene in the cat lineage. A 2005 study identified the mutation."*
- **`which` chains.** Every `which` is a candidate period.
- **Over-qualified claims.** *"While it is generally accepted that cats tend to be more solitary than dogs in most circumstances, recent research has begun to suggest otherwise."* → *"Cats were long considered more solitary than dogs. Recent research disagrees."*
- **Throat-clearing before the point.** *"In order to understand why this behavior exists, it is important to first consider the evolutionary context."* → *"The behavior makes sense once you consider the evolutionary context."*
- **Compound sentences chained with `and` / `but` / `while` / `however`.** Two independent clauses joined by a conjunction is two sentences pretending to be one.

**Splitting recipes:** replace `, and` with `.` when both clauses are independent; replace `, which` with `.` plus a new subject; delete any clause starting with `it is important to note` / `it is generally accepted`; a comma followed by subject + verb is a run-on candidate — split.

**Mandatory self-audit:** count total sentences and 20+-word sentences; ratio over 18% → another split pass; over 20% → two. Any sentence over 30 words is auto-suspect. Any paragraph with two 20+-word sentences needs at least one split.

---

**Transition/connector words: use them where the logic genuinely calls for one — no percentage floor.** Yoast wants 30% of sentences to carry a connector; hitting that floor forces stuffed, samey transitions and is a known AI-cadence generator. Accept a yellow Yoast transition score. When a connector IS natural, prefer plain ones: because, so, but, for example, first/then/finally, in fact, that said, meanwhile, which means. The clichéd crutch openers ("However," "Moreover," "Additionally," "Furthermore") stay banned as paragraph starters per the banned-phrases list.

**Sentence openers: HARD CAP at 2 consecutive sentences with the same opener word. Aim for zero repeats.**

Yoast flags 3 consecutive same-opener sentences. High-risk opener words: `The`, `It`, `This`, `These`, `That`, `Those`, `A`, `An`, `You`, `Your`, `In`, `On`, `When`, `While`, `If`, and the article's primary anchor noun (e.g. `Cats`, `Maine Coons`, `Notion`).

**Preventive recipes (apply while drafting, not after):**

- Move a modifier to the front: "Reflecting light back through the retina, the tapetum lucidum doubles the signal a rod cell receives."
- Start with the object or a fact: "Thirty-two muscles control each cat ear."
- Open with a dependent clause: "Because kittens knead their mother during nursing, adult cats often knead their humans."
- Ask a real question the next sentence answers.
- Lead with a number, date, or named source: "In 2019, Vitale et al. found cats form the same attachment styles as human infants."

**Mandatory self-audit:** scan the first word of every sentence. Three consecutive same-word openers (even across paragraph breaks) → rewrite at least one. Two consecutive → rewrite one anyway when possible.

**List items count too.** Yoast treats each `<li>` as a sentence, so a numbered sequence like "Email 2: … / Email 3: … / Email 4: …" trips the check. In sequence lists, vary the lead-in on every third item ("Next, email 4 …", "Then step 3 …", "Finally, day 10 …") so no three items in a row start with the same word.

**Anaphora caps at two beats.** Deliberate parallel repetition is a good rhetorical device, but three beats trips the same Yoast check. "Your sentence structures survive. Your word choices survive. Your arguments survive." — the third beat must change shape: "So do your arguments." Keep the rhythm, rotate the opener.

## Formatting for Skimmability

WordPress readers skim before they read:

- Short paragraphs (2–5 sentences normal; 1 sentence fine sometimes)
- Bold key terms or the direct answer to a sub-question — sparingly
- Bullet lists only for genuinely list-like content (steps, options, specs) — don't convert prose to bullets to look scannable
- A table when comparing 3+ items across 2+ attributes
- Break up any section longer than ~150 words with a subheading, list, or table

## Banned Words & Patterns (consolidated)

### Banned words and phrases — never use

- "In today's [digital age / fast-paced world / ever-evolving landscape]"
- "It's important to note that…" / "It's worth noting that…"
- "When it comes to…"
- "Whether you're a [X] or a [Y]…"
- "Let's dive in" / "Let's explore" / "Let's unpack" / "Let's delve into" — "delve" in any form
- "In conclusion" / "To sum up" / "Overall"
- "Unleash" / "Elevate" / "Unlock" / "Game-changer" / "Seamless" / "Robust" / "Cutting-edge"
- "Not only X, but also Y"
- "However" / "Moreover" / "Additionally" / "Furthermore" as paragraph openers, more than once per article
- "Testament to" — say what the thing actually demonstrates
- "Vibrant" as filler; "Nuanced" without explaining the nuance
- "Landscape" / "realm" as metaphors; "Navigate" used metaphorically
- "There are several reasons…" / "The primary reason…" / "The key difference…"
- "This behavior occurs when…" / "This is because…" / "One of the most…"
- "The answer depends…" / "In this case…"
- "Crucial" / "Pivotal" / "Vital" as importance-inflation — say what breaks without the thing
- "Foster" / "Boasts" / "Harness" / "Embark" — verbs no one says over coffee
- "Myriad" / "Plethora" / "Tapestry" / "Symphony" as metaphors
- "Underscores" / "Highlights" as in "this underscores the importance of…"
- "Dive deep" / "Deep dive" / metaphorical "journey"
- "At its core" / "In essence" / "Essentially," / "Notably," / "Importantly," as sentence openers
- "Think of it as…" / "Think of X as Y"
- "The bottom line"
- Sweeping "From X to Y" constructions ("From ancient Egypt to modern living rooms…")
- Any sentence that restates the heading in slightly different words as its first line

### Banned structural patterns

- **The negative-parallelism reframe — HARD CAP at one per article.** "It's not just X. It's Y." / "This isn't about X; it's about Y." / "X isn't a bug. It's a feature." This is currently the single most recognizable AI cadence in published prose. One instance per article maximum, and only when the reframe is genuinely the point; zero is better.
- **The echo-fragment closer — BANNED outright.** A short-sentence-fragment cadence that repeats the same clause shape 2-3 times to end a section or the article: "It is not X. It is Y. It is Z." / "Not a trend. A shift. A permanent one." / "The choice is yours." Zero per article, no exceptions. This is a second, distinct AI tic from the negative-parallelism reframe above — the reframe states one contrast once; this one chains short fragments for false gravity. End sections and articles with an actual sentence that says something, not a drumbeat.
- "The result?" / "The catch?" / "The problem?" one-word-question-then-answer construction, more than once per article
- The reflexive rule of three (exactly three adjectives / examples / clauses) — vary it; sometimes one, sometimes five
- Every paragraph 3–4 sentences; every section the same length
- Symmetrical conclusions that mirror the introduction's wording
- Hedging every claim ("may," "could," "potentially") when the source supports a direct statement
- Concluding every section with a neat little summary sentence
- **Em dashes: BANNED in body copy.** Not as an aside marker, not as a parenthetical, not before a qualifying clause. Use a comma (mild aside), parentheses (true parenthetical), a colon (to introduce a named thing), or a period and a new sentence. Before submitting, search the draft for "—". Every instance is a mandatory rewrite. Target: zero.

## Pre-Submit Checklist (every article)

**Architecture:**
1. Hook: first sentence opens an information gap (an itch only the article scratches); first paragraph opens with the most interesting concrete thing and lands on the thesis within ~100 words; hook type differs from the previous article's
2. Promise: direct answer to the search query within the first 150 words; keyphrase verbatim in the first sentence
3. Body arc: H2s read in order tell the argument; sections build (not swappable); something genuinely interesting sits in the back half
4. Texture rotates (answer/example/research/advice/fact); sections don't all share one internal recipe
5. Conclusion passes the significance test and uses a different ending register than the previous article (widened lens / callback / blunt one-liner / next test / reframe fact)
6. Length: within this run's directive band (default 1200–2000); structure varies from recent articles (H2 count, heading grammar, list/table presence)

**Voice:**
7. Coffee Test passed — no textbook sentences; contractions present; reader addressed as "you"
8. Voice matches the anchors: same directness, same willingness to state an opinion
9. No banned words, phrases, or structural patterns (checked against the consolidated list)
10. Em-dash search: zero "—" in body copy

**Research & Substance:**
11. Every non-obvious factual claim traced to source material or search, attributed inline — nothing invented
12. Research woven (claim → named evidence → meaning), not bricked ("According to a 2019 study…")
13. Honest Limits: at least one specific boundary condition / exception passage; major prescriptions state when they don't apply
14. Original Contribution present: one named tactic, test, threshold, or reframe the top-ranking pieces don't have, echoed in the payoff

**SEO / Yoast:**
15. Focus keyphrase set in Yoast's field; ~4–6 verbatim occurrences spread not clustered, semantic variants beyond that (yellow Yoast density is fine)
16. Keyphrase verbatim in: first sentence, ≥1 H2/H3, meta description, slug, image alt text
17. `seo_title` ≤55 characters, keyphrase at the start; entered in Yoast's field
18. Meta description 120–155 chars, keyphrase verbatim, entered in Yoast's field
19. Title check run (colon rule, information gap + intention question, CTR-killers, hedge words, concrete detail, formula rotation A–J); Formula E only used if this run's variation directives allow it
20. 2–4 internal links (real URLs only) + 1–2 external primary-source links
21. At least one image with keyphrase-relevant alt text
22. FAQ section only if this run's variation directives call for one

**Readability:**
23. Passive count: ≤8% of sentences (target 3–5%; ≤6 in ~120 sentences)
24. Long-sentence count: ≤20% over 20 words (target 15–18%; ≤24 in ~120 sentences); nothing over 30 words undefended
25. Opener scan: zero triple same-word openers; doubles minimized
26. Connectors natural, not stuffed (no 30% floor; yellow Yoast transition score is fine)
27. Burstiness: sentence lengths jagged; one tangent/aside present; no three consecutive paragraphs with the same internal shape
28. Negative-parallelism reframe ("It's not just X. It's Y."): at most one, ideally zero
29. Echo-fragment closer ("It is not X. It is Y. It is Z.", "The choice is yours."): zero, no exceptions
30. Every named person, statistic, study, or coined term traced to a real source; none invented (Anti-Fabrication section); health/safety claims attributed to a source, not stated as bare absolutist verdicts

If any check fails, improve the draft before submitting. Would a human editor publish this without edits? If not, it isn't done.
