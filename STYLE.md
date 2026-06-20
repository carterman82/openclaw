# OpenClaw Editorial + SEO Style Guide

This guide exists to produce articles that feel written by a skilled human editor while maximizing search visibility, reader retention, and topical authority.

## Primary Goal

Write the article that would genuinely deserve to rank #1.

Do not write to fill a word count.
Do not write to satisfy a template.
Write to answer the searcher's question better than competing articles.

Every paragraph should either:

- teach something
- answer a question
- provide context
- provide evidence
- provide an example
- move the story forward

If a paragraph does none of those things, remove it.

---

## Before Writing: Build a One-Line Angle

Every article needs a specific point of view, not just a topic.

Bad angle: "Information about the new Pokémon GO season."
Good angle: "Why the Season 4 rebalance quietly killed three meta picks nobody is talking about yet."

Write the angle as one sentence before drafting. If the angle could apply to any article on this topic, it's too generic — sharpen it until it's specific to this piece.

---

## Brand Voice Reference

> Maintainer note: this section is a placeholder. Replace the bracketed example below with 2–3 real paragraphs pulled from your best-performing or most "on-voice" published content. A working voice anchor does more for consistency than any rule in this document — match the rhythm, vocabulary, and level of opinion shown here, not just the topic.

**Voice anchor (replace with real site content):**

> [Paste 2–3 paragraphs of actual published copy here — ideally a section that got good engagement and that you'd point to and say "more like this." Pick something with a clear opinion and concrete detail, not a generic intro paragraph.]

When generating an article, briefly compare the draft's voice against this anchor before finalizing: same level of directness, same vocabulary register, similar willingness to state an opinion. If the draft reads noticeably more cautious or more generic than the anchor, revise it closer to the anchor's voice.

---

## Human Writing Style

Write like an experienced journalist, enthusiast, or subject-matter expert explaining something to an intelligent friend who is smart but doesn't have time to waste.

The reader should never feel they are reading AI-generated content.

### Banned words and phrases

Never use these. They are the most common tells of generated text:

- "In today's [digital age / fast-paced world / ever-evolving landscape]"
- "It's important to note that..." / "It's worth noting that..."
- "When it comes to..."
- "Whether you're a [X] or a [Y]..."
- "Let's dive in" / "Let's explore" / "Let's unpack"
- "In conclusion" / "To sum up" / "Overall"
- "Unleash" / "Elevate" / "Unlock" / "Game-changer" / "Seamless"
- "Not only X, but also Y"
- "However" / "Moreover" / "Additionally" / "Furthermore" as paragraph openers, more than once per article
- Any sentence that restates the heading in slightly different words as its first line

### Banned structural patterns

- The "rule of three" used reflexively (lists of exactly three adjectives, three examples, three clauses) — vary it; sometimes one, sometimes five
- Every paragraph being 3–4 sentences. Real writing has 1-sentence paragraphs and 7-sentence paragraphs in the same piece
- Every section being the same length
- Symmetrical conclusions that mirror the introduction's wording
- Hedging every claim ("may," "could," "potentially") when the source material actually supports a direct statement
- Em dashes used as the default punctuation for every aside — use commas, parentheses, or a new sentence instead; reserve the em dash for when it's genuinely the best tool

### What to do instead

- Vary sentence length on purpose. Follow a long sentence with a short one.
- Use fragments occasionally. For effect. Not constantly.
- Mix short and long paragraphs.
- Include specific, checkable observations rather than vague praise or criticism.
- Use concrete details: real numbers, real names, real dates, not "many" or "various."
- Drop in one unexpected but relevant piece of context per section — the kind of thing a generalist writer wouldn't think to include but a specialist would.
- Let a sentence start with "And" or "But" sometimes. Real editors allow this.
- Have an opinion when the evidence supports one. "This is the better pick" is more useful than "this could be a good option for some players."

The writing should feel naturally imperfect rather than mechanically polished. Polish kills voice.

---

## Reader Experience

Assume the reader arrived from Google with a specific question.

Answer that question quickly.

Do not force long introductions. Skip scene-setting throat-clearing like "Picture this" or restating the obvious premise of the search query.

Deliver useful information within the first 100–150 words.

The reader should never need to scroll halfway through the article to find the answer.

Front-load value. Save broader context, history, and nuance for after the core answer.

---

## Search Intent

Before writing, identify:

- what the searcher wants
- why they searched
- what follow-up questions they likely have

Answer all three.

A successful article solves the entire search journey. Do not answer only the title. Answer the surrounding questions too — these often become the article's subheadings.

---

## Topical Authority

Cover the topic completely.

Include:

- important facts
- related concepts
- relevant entities
- historical context when useful
- practical implications
- common misconceptions

Do not artificially limit coverage. If a competitor would reasonably include information, consider whether readers need it — but don't pad just to match length. Depth is not the same as word count.

---

## Entity Optimization

Mention relevant entities naturally. An entity is any named, specific thing search engines can map to a real-world concept — not a generic noun.

Before writing, identify entities for the current topic across these categories. Not every category applies to every article — use what's relevant:

- **People**: creators, developers, players, executives, named experts
- **Organizations**: studios, publishers, companies, teams
- **Products/versions**: specific titles, models, releases, patches, editions
- **Related concepts/terminology**: the technical or in-universe vocabulary a real expert would use without explaining it
- **Competitors/alternatives**: the other named things a reader is implicitly comparing this to
- **Time markers**: release dates, patch dates, event dates — specific, not "recently"
- **Place/platform**: regions, platforms, storefronts, where relevant

Pull these from the source material and research for the specific article — do not reuse a fixed list across unrelated topics. Mention them naturally within prose, in context, where they'd actually come up. Never keyword stuff, and never name-drop an entity that isn't actually relevant just to tick the box.

> Maintainer note: replace this method with a fixed entity checklist specific to your content vertical once it's defined (e.g., if every article covers indie games, hard-code "engine, publisher, platform, release window, Steam tags" as required categories). A fixed list outperforms a general method once the niche is narrow.

---

## SEO Fundamentals

Include the primary keyword naturally in:

- the title (ideally in the first half)
- the opening section
- at least one H2
- the meta description
- the URL slug
- the conclusion, when it fits naturally

Use semantic variations naturally. Write for topics, not keyword density. Search engines and AI Overviews parse meaning, not keyword counts. Do not repeat the exact keyword phrase mechanically.

### Required metadata for every article

Generate these alongside the body copy:

- **Title tag**: under 60 characters, includes the primary keyword, makes a specific promise
- **Meta description**: under 155 characters, includes the primary keyword, states the concrete payoff, written to earn the click rather than just describe the article
- **URL slug**: short, lowercase, hyphenated, keyword-focused, no stop words
- **Suggested internal links**: 2–4 natural anchor-text opportunities to other relevant articles on the site, where genuinely relevant — never forced
- **Suggested external link(s)**: 1–2 citation-worthy outbound links to primary sources (official documentation, studies, original announcements) when a factual claim benefits from one

### Yoast Field Requirements (mandatory)

Generating the title tag, meta description, and slug as text is not sufficient — they have to actually be entered into the corresponding Yoast SEO fields on the post. Writing good metadata that never makes it into the plugin's fields produces exactly the same Yoast warnings as not writing it at all:

- **Focus keyphrase**: set explicitly in Yoast's Focus Keyphrase field on every post. Never leave it blank. A missing keyphrase is the single most common cause of cascading Yoast failures — without it, the title, slug, intro, and meta-description checks all fail by default regardless of how the writing reads.
- **SEO title field**: populate with the title tag, keyphrase as close to the start as possible. Check against Yoast's pixel-width limit (roughly 60 characters / ~600px), not character count alone — wide characters can overflow even under 60 characters.
- **Meta description field**: populate with the generated meta description. Never leave it blank — Yoast will otherwise auto-pull a snippet from the body, which usually won't contain the keyphrase.
- **Slug**: must contain the focus keyphrase.
- **Keyphrase reuse**: don't reuse a focus keyphrase already used on another published post on the site; use a more specific variant if the broad term is taken.
- **At least one image per article, mandatory**: every article needs a minimum of one image with alt text that naturally includes the keyphrase or a close synonym. An article with zero images will always fail both the Images check and the Keyphrase-in-alt-attributes check, independent of how good the body copy is.

---

## Answer-First / AI Overview Optimization

Search increasingly surfaces direct answers before a click ever happens (featured snippets, AI Overviews). Structure content to win that placement without giving away the reason to keep reading:

- Give a direct, complete answer to the core question within the first 1–3 paragraphs, in plain declarative sentences
- Follow the direct answer with the "why" and "how" — the part that requires actually reading the article
- For any clearly answerable sub-question, use a short, extractable 2–4 sentence paragraph or a tight definition right under its heading
- Where it fits the topic, include a short FAQ section near the end addressing 3–5 real follow-up questions, each with a direct 1–3 sentence answer
- Use comparison tables when the content is inherently comparative (stats, pricing, specs, pros/cons) — tables get pulled into snippets more often than prose

---

## Headings

Create headings that communicate value and could stand alone in a search result.

Bad:

- Overview
- Introduction
- Conclusion
- Final Thoughts

Good:

- Why Shadow Dialga Is Still a Top Dragon Attacker
- What the Season 4 Trailer Reveals
- How Evolution Changed the Franchise

Headings should make readers want to continue, and should make sense if read as a standalone list (this is how they often appear in search results and tables of contents).

Use a clean hierarchy: one H1 (the title), H2 for main sections, H3 for sub-points within a section. Don't skip levels.

---

## E-E-A-T Signals

Demonstrate Experience, Expertise, Authority, and Trustworthiness — this matters more, not less, as more web content is AI-assisted. Generic synthesis reads as thin; specific, lived-in detail reads as credible.

Use:

- concrete facts, with dates and numbers attached
- sourced information — name the source ("according to [outlet/study/official source]") rather than asserting facts as if from nowhere
- specific examples and comparisons, not abstractions
- a clear point of view where the evidence supports one
- first-hand framing where genuinely applicable ("in testing," "after the patch," "based on the patch notes") rather than borrowed, secondhand phrasing dressed up as experience

Avoid unsupported claims. Never invent information, statistics, quotes, or sources. If a fact cannot be verified from the provided source material or research, do not present it as fact — flag it as uncertain or omit it.

### Fact-Verification Workflow

Run this for every factual claim that isn't general knowledge (dates, numbers, quotes, "according to," patch notes, prices, specs, rankings):

1. **Check the provided source material first.** If the user supplied source docs, links, or notes, claims must trace back to them.
2. **If no source material covers the claim, search for it.** Use the web search tool rather than relying on memory — pricing, rosters, patch details, and rankings change, and a remembered figure may be stale.
3. **Attribute it.** Name the source inline ("according to [outlet/official source]") so the claim is checkable by the reader, not just asserted.
4. **If search can't confirm it either, do one of two things — never silently assert it:**
 - Cut the claim entirely, or
 - Soften it explicitly: "reportedly," "as of [date]," "unconfirmed but widely cited" — and only if the softened version is still useful to the reader
5. **Never fabricate a specific number, date, or quote to make a sentence sound more authoritative.** A correct vague sentence beats a precise invented one every time.

---

## Examples

Use examples frequently. Readers remember examples more than explanations.

Whenever explaining a concept, ask: "Can I show this instead of merely describing it?" If yes, add an example — a specific scenario, a real number, a before/after, a short case.

---

## Sentence Craft

Prefer:

- active voice
- concrete nouns
- specific numbers
- strong verbs

Avoid:

- excessive adverbs
- filler phrases ("in order to" → "to"; "due to the fact that" → "because")
- corporate language
- academic padding

Cut words aggressively. Every sentence should earn its place. If a sentence can lose 20% of its words with zero loss of meaning, cut them.

### Readability Targets

These are hard ceilings/floors, not stylistic suggestions — they keep the variation encouraged elsewhere in this guide from drifting into something that actually reads worse:

- **Passive voice: under 10% of sentences.** Default to active voice. Passive is fine when the actor is genuinely unknown or irrelevant ("the patch was released Tuesday" when who released it doesn't matter) — not as a default register.
- **Long sentences: sentences over ~20 words should be under 25% of all sentences.** Variety still matters (see "What to do instead" above) — get it by alternating short and medium sentences, not by defaulting to long ones and occasionally cutting one short.
- **Transition/connector words: at least 30% of sentences should contain one.** This is *not* in tension with the banned-phrases list above — that list bans a narrow set of clichéd openers used repetitively ("However," "Moreover," "Additionally," "Furthermore" as crutch sentence-starters). It does not ban transitions generally. Use natural connectors instead: because, so, but, for example, first/then/finally, as a result, in fact, that said, meanwhile, which means. These aid both flow and machine readability scoring without sounding robotic.

---

## Formatting for Skimmability

WordPress readers skim before they read. Structure for that:

- Short paragraphs (2–5 sentences is normal; 1 sentence is fine sometimes)
- Bold key terms or the direct answer to a sub-question — sparingly, not every paragraph
- Use bullet lists only for genuinely list-like content (steps, options, specs) — don't convert prose into bullets just to look scannable
- Use a table when comparing 3+ items across 2+ attributes
- Break up any section longer than ~150 words with a subheading, list, or table

---

## AI Detection Avoidance

Do not intentionally write like AI. Beyond the banned words/patterns above:

- Allow occasional short paragraphs and the occasional run-on, the way a human writing quickly would
- Allow occasional opinionated observations when supported by facts
- Avoid excessive symmetry — not every list needs the same number of items, not every section needs the same structure
- Avoid concluding every section with a neat little summary sentence; sometimes a section just ends

Natural human writing contains variation. Mechanical consistency is the giveaway.

---

## Conclusion Strategy

Do not summarize the article.

Instead:

- provide a final insight
- connect back to the opening
- explain why the topic matters
- highlight future implications

Leave the reader with something to think about, not a recap of what they just read.

---

## Competitive Coverage

Before finalizing the article, identify the 3–5 most likely competing articles (mentally, based on what would plausibly rank for this query).

Ensure the article contains every major piece of information a reader would reasonably expect to find in those articles.

Then add at least one useful insight, example, comparison, or piece of context they are unlikely to include.

The goal is not to match competitors. The goal is to be the most complete and useful result on the page.

---

## Output Checklist Per Article

Every article should ship with:

1. Focus keyphrase set in the Yoast Focus Keyphrase field
2. Title tag, entered into the Yoast SEO title field (not just present in the body)
3. Meta description, entered into the Yoast meta description field
4. URL slug containing the focus keyphrase
5. Body copy with proper H1/H2/H3 hierarchy
6. A direct answer within the first 150 words, with the keyphrase in the opening section
7. 2–4 suggested internal links (anchor text + target topic)
8. 1–2 suggested external/source links, where a claim benefits from one
9. An FAQ section, where the topic supports follow-up questions
10. At least one image, with alt text naturally containing the keyphrase or a close synonym

---

## Final Quality Check

Before finishing, verify:

- Would a human editor publish this without edits?
- Does every paragraph earn its place?
- Is the main question answered within the first 150 words?
- Are there banned words, phrases, or structural patterns anywhere in the draft?
- Is paragraph and sentence length actually varied, or did it default to a uniform rhythm?
- Are important entities included naturally?
- Are all facts and figures verifiable from source material — nothing invented?
- Are the title, meta description, and slug all present and within length limits?
- Is the focus keyphrase actually set in Yoast's field — not just present in the text?
- Is there at least one image with keyphrase-relevant alt text?
- Is passive voice under 10% of sentences, and long sentences (20+ words) under 25%?
- Is there a natural connector/transition word in roughly a third of sentences?
- Is the article genuinely better than the top-ranking competitors, not just longer?

If not, improve it before publishing.
