<!-- markdownlint-disable MD034 MD036 -->

# AyushBot Brand System V2 (Legendary Edition)

**Document owner:** Product + Design Leadership  
**Applies to:** AyushBot App, AyushBot Gateway, AyushBot Sense, AyushBot Insight  
**Primary audience:** CEO/PM, Design Leads, Partnerships, Training, Communications  
**Status:** Canonical brand reference (strategy-level)

---

## 0) How to use this document

This document defines **why AyushBot should look, sound, and feel the way it does**.

- This is the authoritative source for: brand strategy, trust posture, voice and tone, naming, visual philosophy, governance, and brand quality metrics.
- This is **not** the implementation source for dp/sp values, component anatomy, or Compose behavior.
- Implementation-level decisions live in:  
  `android/docs/ayushbot-design-specs-legendary.md`

### Non-redundancy contract

- **Brand guide owns:** strategic intent, identity, principles, narratives, standards.
- **Design specs owns:** executable UI tokens, layouts, states, motion, accessibility implementation.

---

## 1) Brand north star

### 1.1 Brand one-liner

**AyushBot is the calm, evidence-grounded clinical co-pilot that helps ASHA workers make safer decisions for every family they serve.**

### 1.2 Mission

Enable frontline workers in low-connectivity regions to deliver safer triage decisions through offline-first AI, clear evidence, and local-language support.

### 1.3 Vision

A future where no ASHA worker makes life-critical decisions unsupported, and where advanced healthcare intelligence is available in every village—not only where the internet is strong.

### 1.4 Brand promise

AyushBot converts advanced AI and IoT into a practical field tool that is:

- **Available** (offline-first)
- **Understandable** (plain language + voice)
- **Trustworthy** (cited evidence + transparent uncertainty)
- **Respectful** (supports, never replaces, ASHA judgment)

### 1.5 Brand personality

AyushBot is:

- **Calm** under pressure
- **Competent** in clinical clarity
- **Caring** in human tone

Three words to remember: **Calm · Competent · Caring**.

---

## 2) Strategic positioning

### 2.1 Category

AyushBot is a **clinical decision support and triage system for frontline community health work**, not a generic chatbot and not a telemedicine substitute.

### 2.2 Positioning statement

For ASHA workers serving rural communities, AyushBot is an offline-first clinical co-pilot that combines sensor-driven triage, guideline-grounded recommendations, and multilingual assistance so critical decisions are safer, faster, and explainable in the field.

### 2.3 Core differentiators

1. **Offline-first by design** (not a degraded fallback).
2. **Evidence-linked recommendations** with source context.
3. **Sensor + symptom fusion** for stronger triage quality.
4. **Federated/privacy-preserving learning posture**.
5. **Indian language + context adaptation** for usability at the last mile.

### 2.4 Messaging angle

**“Global-grade clinical intelligence, built for the last mile.”**

---

## 3) Brand principles for executive decisions

Use these principles whenever a tradeoff appears:

1. **Safety over speed**  
   If a faster interaction risks clinical misunderstanding, choose safer clarity.
2. **Clarity over cleverness**  
   A simple, obvious flow beats a novel but ambiguous interaction.
3. **Evidence over aesthetics alone**  
   If it looks great but lowers comprehension, it fails.
4. **Local relevance over trend compliance**  
   Village context beats global app-fashion.
5. **Human agency over AI spectacle**  
   The interface must communicate: *“You decide; AyushBot assists.”*

### 3.1 Board-level go/no-go test

A proposed change is approved only if it passes:

- Does it reduce risk of incorrect action in high-pressure scenarios?
- Does it improve comprehension in local-language use?
- Does it preserve confidence without overclaiming AI certainty?
- Can an ASHA complete the task faster **and** more accurately?

---

## 4) Verbal identity system

### 4.1 Voice

- Plain, direct, respectful
- Clinically disciplined but never robotic
- Helpful without being patronizing

### 4.2 Tone by scenario

- **Routine:** calm and collaborative  
  “Let’s check a few things together.”
- **Caution/monitor:** focused, specific  
  “The child needs close observation. Please follow these steps.”
- **High risk/refer:** urgent but controlled  
  “Refer to PHC today. Give first-dose treatment before transfer.”
- **Critical/emergency:** unambiguous command language  
  “This is an emergency. Call 108 now and refer immediately.”
- **Uncertainty:** honest and bounded  
  “The available information is insufficient for confident classification. Follow referral protocol.”

### 4.3 Mandatory writing rules

- Action-first: **what to do**, then why.
- Use active voice.
- Use short sentences and short sections.
- Replace jargon unless it is clinically necessary.
- If technical term is unavoidable, define it where used.
- Do not use blame framing (“you failed to…”).

### 4.4 Language behavior (multilingual)

- Prefer locally understandable terms over direct literal translation.
- Preserve clinical accuracy when simplifying wording.
- Keep high-risk messages semantically stable across languages.

### 4.5 Disallowed patterns

- “AI diagnosed…”
- “Guaranteed accurate”
- Fear-based copy and panic language
- Vague action copy (“handle accordingly”)

---

## 5) Trust architecture (brand-level)

AyushBot trust is built through five visible commitments:

1. **Evidence visibility** – recommendation is grounded, not magical.
2. **Uncertainty disclosure** – confidence limits are stated, not hidden.
3. **Risk semantics consistency** – the same risk level always means the same urgency.
4. **Human authority preservation** – ASHA remains decision-maker.
5. **Failure transparency** – offline/sync constraints are clearly communicated.

### 5.1 Confidence language ladder

- **High confidence:** “Likely diagnosis…”
- **Moderate confidence:** “Possible diagnosis; monitor + reassess.”
- **Low confidence:** “Insufficient confidence; follow protocol referral.”

### 5.2 Privacy-language commitments

All user-facing privacy copy must avoid hype and be explicit:

- “Your visit data is saved locally first.”
- “Sync happens when gateway is available.”
- “Patient-level details are handled with privacy safeguards.”

---

## 6) Brand architecture and naming system

### 6.1 Product family

- **AyushBot App** — frontline Android interface for ASHA workers
- **AyushBot Gateway** — PHC edge orchestration layer
- **AyushBot Sense** — sensor pack and vitals capture ecosystem
- **AyushBot Insight** — analytics and program visibility layer

### 6.2 Naming grammar

Feature names must describe intent, not internal mechanics.

- Good: `Safe Referral`, `Case History`, `Offline Visit`, `Read Aloud`
- Avoid: `Edge Sync`, `RAG Query`, `Federated Round`, `Inference Fallback`

### 6.3 Naming checklist

A candidate feature name is accepted if it is:

- understandable by a non-technical frontline user,
- pronounceable in major Indian language contexts,
- no more than 2–3 words when possible,
- action-oriented.

---

## 7) Visual identity strategy (brand-level)

> Implementation tokens and exact component mappings are specified in the design specs document.

### 7.1 Visual intent

AyushBot visual language should communicate:

- **Clinical confidence** (structured, stable, disciplined)
- **Human warmth** (not cold or intimidating)
- **Field readiness** (usable under stress, sunlight, interruptions)

### 7.2 Logo strategy

Logo concept should unify:

- care/protection motif (heart/shield),
- subtle health signal (waveform),
- grounded rural context motif (village silhouette),
- abstract “A” reference.

### 7.3 Color philosophy

- Teal-led core identity for trustworthy calm.
- Saffron used intentionally for warm emphasis, never visual noise.
- Red reserved for critical/error semantics only.
- Clinical risk colors are semantic assets—not decorative palette.

### 7.4 Typography philosophy

- Noto Sans as primary multilingual backbone.
- Noto Serif reserved for guideline/evidence context.
- Monospaced numeric style for vitals stability.

### 7.5 Imagery strategy

- Prioritize illustrations and real field realism over polished stock aesthetics.
- Represent ASHA agency and dignity.
- Avoid trauma-centric visual storytelling.

### 7.6 Motion personality

- Calm and purposeful.
- Motion must orient, confirm, or warn—not entertain.
- Critical transitions prioritize urgency clarity over flourish.

---

## 8) Experience standards across touchpoints

### 8.1 In-app experience

- First screen should communicate confidence and simplicity.
- High-risk outputs must be unmistakable in words, symbols, and urgency.
- Voice experiences should sound supportive, not mechanical.

### 8.2 Training and documentation

- Step-by-step orientation over dense theoretical material.
- Localized examples with practical field scripts.
- Always include “what to do if offline” playbooks.

### 8.3 Public communications

- Lead with outcomes for workers and families.
- Avoid techno-centrism (“our model architecture…” first messaging).
- Highlight partnerships and evidence legitimacy.

### 8.4 Donor/policy communications

- Link clinical and operational outcomes.
- Frame reliability, explainability, and inclusion as system strengths.

---

## 9) Accessibility and inclusion commitments (brand-level)

AyushBot brand quality includes accessibility as a non-negotiable standard.

- Never encode meaning by color alone.
- Ensure plain-language alternatives for technical phrasing.
- Respect voice-first and low-literacy use contexts.
- Prefer progressive disclosure over dense cognitive load.

### 9.1 Inclusion doctrine

Brand quality is successful only if people with varied abilities, literacy levels, and language backgrounds can safely act on guidance.

---

## 10) Governance model

### 10.1 Ownership

Final approval authority (brand council): Product + Design lead, with clinical safety review input for high-risk communication patterns.

### 10.2 Change tiers

- **Tier 1 (minor):** copy refinements, minor visual polish; sprint-level approval.
- **Tier 2 (major):** color hierarchy, typography stack, logo changes; council approval with evidence.
- **Tier 3 (critical):** any change affecting risk semantics, emergency language, or trust disclosures; requires safety review and pilot validation.

### 10.3 Brand debt operations

Track and periodically resolve:

- inconsistent risk labels,
- off-system colors,
- unclear copy,
- icon/terminology drift.

---

## 11) Brand performance scorecard

### 11.1 Leading indicators

- Time to identify primary action on recommendation screen
- Correct interpretation rate of risk level
- Completion rate for referral workflow
- Perceived trust and clarity scores (field interviews)

### 11.2 Guardrail indicators

- Misinterpretation incidents in high-risk flows
- “What does this mean?” support burden by message type
- Language comprehension issues by locale

### 11.3 Outcome framing

The brand is successful when ASHAs report: “I understand what to do immediately, and I trust why the system is saying it.”

---

## 12) Future-facing expansion strategy

As AyushBot expands to more districts/regions:

- Preserve core values and risk semantics globally.
- Localize language and cultural expression without changing safety meaning.
- Build regional communication variants while maintaining one clinical trust core.

---

## Appendix A — Research foundation (separate citation appendix)

### A1) Material Design 3 and system design

- Material 3 color system overview:  
  https://m3.material.io/styles/color/overview
- Color system internals (“how it works”):  
  https://m3.material.io/styles/color/system/how-the-system-works
- Color roles and contrast-safe pairing guidance:  
  https://m3.material.io/styles/color/the-color-system/key-colors-tones
- Choosing static vs dynamic schemes:  
  https://m3.material.io/styles/color/choosing-a-scheme
- Dynamic color overview:  
  https://m3.material.io/styles/color/dynamic-color/overview
- Typography overview + applying type:  
  https://m3.material.io/styles/typography/overview  
  https://m3.material.io/styles/typography/applying-type
- States and state layers:  
  https://m3.material.io/foundations/interaction/states/overview  
  https://m3.material.io/foundations/interaction/states/state-layers  
  https://m3.material.io/foundations/interaction/states/applying-states
- Accessible design overview:  
  https://m3.material.io/foundations/accessible-design/overview

### A2) Android/Compose accessibility guidance

- Compose accessibility overview:  
  https://developer.android.com/develop/ui/compose/accessibility
- API defaults (touch targets, labels, interactive semantics):  
  https://developer.android.com/develop/ui/compose/accessibility/api-defaults
- Semantics:  
  https://developer.android.com/develop/ui/compose/accessibility/semantics
- Traversal order:  
  https://developer.android.com/develop/ui/compose/accessibility/traversal
- Merging and clearing semantics:  
  https://developer.android.com/develop/ui/compose/accessibility/merging-clearing
- Scalable content:  
  https://developer.android.com/develop/ui/compose/accessibility/scalable-content
- Accessibility testing in Compose:  
  https://developer.android.com/develop/ui/compose/accessibility/testing
- Android accessibility principles and app guidance:  
  https://developer.android.com/guide/topics/ui/accessibility/principles  
  https://developer.android.com/guide/topics/ui/accessibility/apps

### A3) Standards and readability

- WCAG quick reference (2.1):  
  https://www.w3.org/WAI/WCAG21/quickref/
- Plain language guide series (principles/writing/design/testing):  
  https://digital.gov/guides/plain-language/
- Writing for understanding:  
  https://digital.gov/guides/plain-language/writing
- Clear and short writing rules:  
  https://digital.gov/guides/plain-language/writing/clear-short
- Avoid jargon principles:  
  https://digital.gov/guides/plain-language/principles/avoid-jargon
- Design for understanding (headings, lists):  
  https://digital.gov/guides/plain-language/design  
  https://digital.gov/guides/plain-language/design/headings  
  https://digital.gov/guides/plain-language/design/lists

### A4) Mobile and inclusion context

- Mobile limitations and strengths (interruptions, small screens, connectivity):  
  https://www.nngroup.com/articles/mobile-ux/
- Noto multilingual type system:  
  https://fonts.google.com/noto
- WHO assistive technology fact sheet:  
  https://www.who.int/news-room/fact-sheets/detail/assistive-technology
- WHO global report on assistive technology:  
  https://www.who.int/publications/i/item/9789240049451
- WHO global strategy on digital health 2020–2025:  
  https://www.who.int/publications/i/item/9789240020924

---

## Appendix B — Brand voice quick reference cards

### B1) Action-first template

`[Immediate action] + [timing] + [reason/evidence] + [fallback if uncertain]`

### B2) Emergency message template

- “This is an emergency.”
- “Call 108 now.”
- “Refer immediately to [facility].”
- “Give [first action] before transfer, if available.”

### B3) Uncertainty template

- “Available information is insufficient for confident classification.”
- “Please follow standard referral protocol.”
- “Reassess if [specific signs] worsen.”

### B4) Numeric context template

- “SpO₂ is 89% (this is low).”
- “Temperature is 39.1°C (high fever).”

These cards should be localized, validated, and reused across app, training, and support flows.
