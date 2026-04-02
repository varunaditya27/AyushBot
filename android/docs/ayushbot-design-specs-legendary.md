<!-- markdownlint-disable MD022 MD024 MD032 MD034 MD060 -->

# AyushBot Android Design Specs V2 (Legendary Edition)

**Document owner:** Android Design + Frontend Engineering  
**Applies to:** `android/app` Jetpack Compose implementation  
**Primary audience:** Android engineers, UI/UX designers, QA, accessibility testers  
**Status:** Canonical implementation specification

---

## 0) Scope and non-redundancy contract

This document defines **how AyushBot is implemented visually and interactively on Android**.

- Authoritative source for: design tokens, component anatomy, interaction states, accessibility semantics, screen layouts, and QA gates.
- Strategic rationale (positioning, brand governance, naming architecture) is owned by:  
  `android/docs/ayushbot-branding-guide-legendary.md`

### Boundaries

- **Brand doc owns:** identity strategy and messaging philosophy.
- **Design specs owns:** measurable UI behavior and implementation constraints.

---

## 1) Product and field constraints

AyushBot must operate safely in contexts that are:

- interruption-heavy,
- low-connectivity,
- multilingual,
- low-end Android hardware,
- high cognitive stress (triage urgency).

### 1.1 Primary UX mandate

Every critical screen must answer in this order:

1. **What is the risk right now?**
2. **What should the ASHA do now?**
3. **Why is this recommended?**
4. **What if data is incomplete/offline?**

### 1.2 Platform constraints

- Kotlin + Jetpack Compose + Material 3
- Min SDK 26
- Offline-first data model
- Single-activity navigation with predictable back stack

---

## 2) Information hierarchy model

All core workflows use a strict, repeatable hierarchy:

1. **State banner** (risk/offline/error)
2. **Primary action block**
3. **Context/evidence block**
4. **Secondary actions**
5. **Advanced details (collapsed)**

This hierarchy is mandatory for:

- Recommendation screen
- Sensor capture decision points
- Referral and follow-up flows

---

## 3) Design token system (implementation contract)

> Existing implementation anchors currently live in `ui/theme/Color.kt`, `Type.kt`, and `Shape.kt`.

## 3.1 Color system

### 3.1.1 Core palette (light theme)

| Role | Token | Hex | Usage |
|---|---|---:|---|
| Primary | `primary` | `#006874` | High-emphasis actions, active controls |
| On Primary | `onPrimary` | `#FFFFFF` | Text/icons on primary |
| Primary Container | `primaryContainer` | `#97F0FF` | Selected cards/chips |
| On Primary Container | `onPrimaryContainer` | `#001F24` | Text/icons on primary container |
| Secondary | `secondary` | `#4A6267` | Secondary controls/info |
| Tertiary | `tertiary` | `#7D5700` | Accent and educational callouts |
| Error | `error` | `#BA1A1A` | Error and destructive semantics |
| Background/Surface | `background/surface` | `#FAFDFD` | App canvas |
| Surface Variant | `surfaceVariant` | `#DBE4E6` | Low-emphasis containers |
| Outline | `outline` | `#6F797A` | Important boundaries |
| Outline Variant | `outlineVariant` | `#BFC8CA` | Dividers/decorative boundaries |

### 3.1.2 Clinical risk semantic palette (non-decorative)

| Semantic Token | Hex | Meaning | Required redundant cues |
|---|---:|---|---|
| `stateSafe` | `#1B6E2C` | Stable / low risk | Label + icon |
| `stateCaution` | `#B45309` | Monitor | Label + icon |
| `stateHigh` | `#C2410C` | Refer today | Label + icon |
| `stateCritical` | `#9B1C1C` | Emergency | Label + icon + haptic/audio |

**Rule:** risk semantics must never be repurposed for decorative emphasis.

### 3.1.3 Dynamic color policy

- Dynamic color is not used for risk semantics.
- Baseline static scheme is default to preserve semantic consistency across devices.
- Optional future enhancement: dynamic neutral surfaces only, with locked clinical tokens.

### 3.1.4 Contrast policy

- Small text: target at least 4.5:1
- Large text: target at least 3:1
- Non-text interactive boundaries: target at least 3:1 where applicable
- High contrast mode should maintain clinical meaning without hue ambiguity

---

## 3.2 Typography system

### 3.2.1 Typeface stack

- Primary: Noto Sans
- Citation/source: Noto Serif
- Numeric-vitals: JetBrains Mono (tabular stability)

### 3.2.2 Type scale

| Style | Size / Line Height | Typical usage |
|---|---|---|
| Display Large | 57 / 64 | Rare hero states |
| Headline Large | 32 / 40 | Screen title |
| Headline Medium | 28 / 36 | Risk headline |
| Headline Small | 24 / 32 | Section heading |
| Title Large | 22 / 28 | Card title |
| Title Medium | 16 / 24 | Card subtitle/field label |
| Body Large | 16 / 24 | Core explanatory text |
| Body Medium | 14 / 20 | Secondary explanation |
| Body Small | 12 / 16 | Metadata/captions |
| Label Large | 14 / 20 | Buttons/CTA labels |
| Label Medium | 12 / 16 | Chip/status labels |

### 3.2.3 Locale/script adjustments

Use locale-aware line height multipliers:

- Devanagari/Bengali: ×1.25–1.30
- Tamil/Telugu/Kannada: ×1.20
- Latin-heavy screens: ×1.10–1.15

### 3.2.4 Numeric rendering

Vitals must use tabular numeric rendering to avoid jitter and improve scan speed.

---

## 3.3 Spacing and layout tokens

### 3.3.1 Base grid

- Base unit: 4dp
- Horizontal page padding: 16dp
- Major vertical section gap: 24dp
- Card content padding: 16dp

### 3.3.2 Recommended spacing tokens

| Token | Value |
|---|---:|
| `spaceXs` | 4dp |
| `spaceSm` | 8dp |
| `spaceMd` | 12dp |
| `spaceLg` | 16dp |
| `spaceXl` | 24dp |
| `space2xl` | 32dp |

### 3.3.3 Touch target

All interactive targets must be at least `48dp × 48dp`.

---

## 3.4 Shape and surface tokens

| Shape role | Radius |
|---|---:|
| Extra small | 4dp |
| Small | 8dp |
| Medium | 12dp |
| Large | 16dp |
| Extra large | 28dp |
| Banner (risk) | 0dp |
| Pill action | fully rounded |

### 3.4.1 Elevation strategy

Use tonal hierarchy first, shadow second.

- Base surfaces: `surface/background`
- Containers: `surfaceContainer*` or `surfaceVariant`
- FAB may use explicit shadow for affordance

---

## 3.5 Interaction state layer model

### 3.5.1 Overlay opacities

| State | Layer opacity |
|---|---:|
| Hover | 8% |
| Focus | 10% |
| Press | 10% |
| Drag | 16% |
| Disabled (content treatment) | reduced emphasis |

### 3.5.2 State inheritance rules

- Apply states to actionable child elements, not large non-action containers.
- Disabled elements must not accept focus/press/drag behavior.
- Pressed states should include ripple and optional elevation shift for actionable components.

---

## 4) Accessibility implementation contract

## 4.1 Mandatory baseline

- All screens tested with TalkBack and switch-style traversal assumptions.
- All actionable icons include localized descriptions.
- Decorative visuals are hidden from accessibility announcements.

## 4.2 Semantics requirements by type

- **Headers:** mark section headlines as headings.
- **Alert/status updates:** use live region semantics appropriately.
  - Polite for routine updates.
  - Assertive only for emergency-critical updates.
- **Progress controls:** expose progress range info.
- **Error fields:** include expanded error semantics.
- **Collections:** provide collection and item metadata for long lists.

## 4.3 Traversal and grouping

- Use traversal grouping for logical card/section groups.
- Use traversal index only when geometric layout breaks reading sequence.
- Avoid unintended merge collisions in nested clickables.

## 4.4 Merge/clear/hide rules

- Use `mergeDescendants` when children form one logical action unit.
- Use `clearAndSetSemantics` sparingly for true custom composites.
- Use `hideFromAccessibility` for decorative/redundant elements.

## 4.5 Scalable content

- Support system font scaling at least to 1.5× without clipping primary content.
- Preserve reflow; avoid two-dimensional pan dependence.
- Keep action controls reachable and visible at enlarged text scales.

## 4.6 Accessibility testing gates

- Manual: TalkBack flow completion for key journeys.
- Automated: Compose accessibility checks in UI tests.
- Validation dimensions:
  - labels/descriptions,
  - contrast,
  - touch target size,
  - traversal order.

---

## 5) UX writing implementation rules

### 5.1 Action-first composition

Use this copy order in all clinical guidance:

1. Action
2. Timing
3. Reason
4. Escalation condition

### 5.2 Plain-language rules

- Active voice
- Present tense where possible
- One primary idea per sentence
- Minimal jargon; define unavoidable terms in-place

### 5.3 Numeric context rule

Vitals must include interpretation:

- `SpO₂ 89% (low)`
- `Temp 39.1°C (high fever)`

### 5.4 List formatting rule

- Ordered lists for procedure steps
- Bullets for options/alternatives
- Include lead-in sentence before list

---

## 6) Component library specifications

## 6.1 Top App Bar

**Purpose:** orientation + key action access

**Anatomy:**
- navigation icon
- title
- optional contextual action(s)

**States:** default, scrolled, disabled action, error-context indicator

**Rules:**
- Avoid making full bar a state layer target.
- Apply interaction states to actionable icons only.

---

## 6.2 Bottom Navigation

**Purpose:** stable root-level navigation

**Destinations:** max 4 in core phone layout

**Rules:**
- Labels always visible
- Active state must use shape + icon + label emphasis
- Keep bar height optimized for one-thumb use

---

## 6.3 Risk Badge (critical component)

**Purpose:** immediate clinical urgency communication

**Anatomy:**
- full-width banner
- left accent strip
- risk icon
- risk title
- short action subtitle

**Priority behavior:**
- For critical: multimodal urgency signal (visual + haptic + optional audio)
- Keep copy explicit and command-oriented

**Accessibility:**
- Never rely on color alone
- Provide role/state semantics and concise announcement text

---

## 6.4 Vitals Gauge

**Purpose:** rapid vitals scan + threshold interpretation

**Anatomy:**
- circular ring
- value + unit center
- label
- signal quality indicator

**Behavior:**
- animated value transitions (non-distracting)
- threshold-based color interpretation
- disable confirm action if signal quality is unreliable

---

## 6.5 Symptom Card

**Purpose:** structured symptom capture with low cognitive load

**Anatomy:** icon + label + selectable state + check indicator

**States:** default, selected, focused, disabled

**Rules:**
- Group cards by clinical categories.
- Ensure selected state is visible via fill + border + icon cue.

---

## 6.6 Primary Diagnosis Card

**Purpose:** communicate current primary hypothesis safely

**Anatomy:**
- diagnosis title
- confidence marker
- short explanation
- citation snippet

**Rules:**
- Keep explanation concise and action relevant.
- Use source-styled text for evidence context.

---

## 6.7 Action Plan Card

**Purpose:** explicit treatment/referral/counsel sequence

**Behavior:**
- expandable sections allowed
- numbered procedural steps required for treatment/referral flows

**States:** collapsed, expanded, unavailable action, escalated action

---

## 6.8 Evidence & Source Card

**Purpose:** trust and traceability

**Rules:**
- show source reference context visibly
- differentiate source text style from generated explanation

---

## 6.9 Voice controls

### Voice input button
- large target
- clear listening state
- visible transition between idle/listening/processing

### Voice output button
- full-width action in recommendation context
- playback progress visibility
- pause/resume support

---

## 6.10 Form fields and selection controls

- labels mandatory
- helper text contextual
- error text actionable
- dropdowns use explicit affordances
- switches for binary toggles; checkboxes for multi-select

---

## 6.11 Sync and offline status components

- explicit status chip/banner for connectivity mode
- avoid hidden background-failure semantics
- pending-sync counts visible where relevant

---

## 6.12 Skeleton and loading placeholders

- prefer structured skeletons to global blocking spinners
- preserve layout geometry to avoid shift on resolve

---

## 7) Screen blueprint library + state matrices

> Blueprints are low-fidelity structural maps; exact styling is governed by tokens above.

## 7.1 Home screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: AyushBot + ASHA name          │
├─────────────────────────────────────────────┤
│ Today Summary Row (Visits | Pending | Alert)│
├─────────────────────────────────────────────┤
│ Quick Actions Grid (2×2)                    │
│ [New Visit] [Case History]                  │
│ [Voice Ask] [Emergency Referral]            │
├─────────────────────────────────────────────┤
│ Recent Cases List                            │
│ [Case Card]                                  │
│ [Case Card]                                  │
├─────────────────────────────────────────────┤
│ Bottom Navigation                             │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Primary CTA | Copy behavior |
|---|---|---|---|
| Normal | Full summary + recent cases | `New Visit` active | concise daily status |
| Loading | Summary skeleton + list skeleton | CTA still enabled | “Loading local dashboard…” |
| Empty | no case cards | `Start First Visit` emphasized | encouraging plain text |
| Offline | persistent offline chip | `New Visit` unchanged | “Working offline. Sync later.” |
| Error | non-blocking error card | CTA retained | “Couldn’t load recent history. Try refresh.” |
| Critical pending | critical strip appears above list | `Emergency Referral` emphasized | unambiguous urgency copy |

---

## 7.2 New Visit flow (4-step wizard)

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: New Visit                      │
│ Stepper: [1 Patient][2 Sensor][3 Symptoms][4 Review] │
├─────────────────────────────────────────────┤
│ Step Content Area                            │
│ (form / gauges / symptom grid / summary)     │
├─────────────────────────────────────────────┤
│ Bottom Action Row                            │
│ [Back]                          [Next/Submit]│
└─────────────────────────────────────────────┘
```

### State matrix

| Flow state | Visual treatment | CTA behavior | Guardrail |
|---|---|---|---|
| Step active | current step highlighted | Next enabled on valid input | input validation visible |
| Sensor reading | live gauge + signal bars | Next disabled until minimum quality | quality reason shown |
| Offline gateway | local mode badge | Continue local capture | no cloud dependency blocking |
| Validation error | inline field/symptom errors | Next blocked | action-oriented corrective text |
| Submit processing | review skeleton + progress text | Submit disabled | avoid duplicate submission |
| Critical detection | emergency banner interrupt | `Emergency Referral` surfaced | bypass non-essential steps |

---

## 7.3 Recommendation screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: Recommendation                  │
├─────────────────────────────────────────────┤
│ Risk Badge (full width)                      │
├─────────────────────────────────────────────┤
│ Primary Diagnosis Card                       │
├─────────────────────────────────────────────┤
│ Action Plan Card (Treat/Refer/Counsel)       │
├─────────────────────────────────────────────┤
│ Evidence & Source Card                        │
├─────────────────────────────────────────────┤
│ Voice Playback CTA                            │
│ Secondary Actions (Referral Slip / Share)     │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Primary action | Copy behavior |
|---|---|---|---|
| Normal | full card stack | follow action plan | action-first explanation |
| Loading recommendation | skeleton cards | actions disabled until ready | “Preparing recommendation…” |
| Evidence unavailable | diagnosis + action still shown | referral-safe fallback | “Evidence detail unavailable; follow protocol.” |
| Offline mode | offline status retained | local recommendation visible | transparent offline language |
| Critical | critical badge + urgency cues | `Call 108` + referral | command language, no ambiguity |
| Low confidence | confidence marker lowered | protocol fallback surfaced | explicit uncertainty message |

---

## 7.4 Case History screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: Case History                   │
├─────────────────────────────────────────────┤
│ Search Field                                 │
│ Filter Chips: All | Today | Critical | Unsynced │
├─────────────────────────────────────────────┤
│ Case List                                    │
│ [Case Card + Risk Chip + Sync Status]        │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Interaction | Copy behavior |
|---|---|---|---|
| Normal | searchable list | open case details | compact metadata |
| Loading | list skeleton | search disabled briefly | “Loading case history…” |
| Empty | empty illustration/card | clear filters or start visit | “No matching cases yet.” |
| Offline | unsynced chips visible | view local cases only | “Showing local records.” |
| Error | retry card/banner | retry + keep cached list | non-technical error text |

---

## 7.5 Voice Query screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: Voice Ask AyushBot             │
├─────────────────────────────────────────────┤
│ Conversation Thread (messages + citations)   │
├─────────────────────────────────────────────┤
│ Input Row                                    │
│ [Text field] [Mic button] [Send]             │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Input behavior | Copy behavior |
|---|---|---|---|
| Idle | thread + inactive mic | text or mic available | prompt examples shown |
| Listening | pulsing mic ring | send disabled until transcript | “Listening…” |
| Processing | assistant typing/skeleton bubble | input optionally paused | “Thinking…” |
| Offline fallback | local guidance mode chip | restricted capabilities explained | explicit capability note |
| Error | message-level failure chip | retry visible | “Couldn’t process audio. Try again.” |

---

## 7.6 Settings screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: Settings                       │
├─────────────────────────────────────────────┤
│ Profile Card                                 │
├─────────────────────────────────────────────┤
│ Sections: Language | Gateway | Offline | Sync│
│          Accessibility | About               │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Behavior | Copy behavior |
|---|---|---|---|
| Normal | section cards | toggle/select controls | concise labels |
| Loading | section placeholders | temporary lock | “Loading settings…” |
| Save success | subtle confirmation | persist state | “Saved locally.” |
| Save failure | inline error row | retry option | actionable fix guidance |

---

## 7.7 Sensor Management screen

### Blueprint

```text
┌─────────────────────────────────────────────┐
│ Top App Bar: Sensor Management              │
├─────────────────────────────────────────────┤
│ Connection Status Card                       │
├─────────────────────────────────────────────┤
│ Live Vitals Gauge Grid                        │
├─────────────────────────────────────────────┤
│ Battery + Signal Diagnostics                  │
├─────────────────────────────────────────────┤
│ Self-Test Button + Results                    │
└─────────────────────────────────────────────┘
```

### State matrix

| State | Visual treatment | Primary action | Safety behavior |
|---|---|---|---|
| Connected stable | green status | self-test optional | capture allowed |
| Connecting | progress indicator | wait/retry | no false-success display |
| Disconnected | warning card | retry pairing | manual entry fallback available |
| Noisy signal | caution indicators | reposition guidance | block unreliable capture confirmation |
| Hardware fault | error diagnostics card | guided troubleshooting | referral to manual protocol |

---

## 8) Motion and feedback grammar

## 8.1 Navigation transitions

- Forward: slide/fade with controlled duration
- Back: reverse transition, slightly shorter
- Modal sheets: upward motion + dimmed scrim

## 8.2 Component micro-interactions

- Press feedback: subtle scale/ripple
- Expand/collapse: smooth size + opacity transition
- Risk changes: controlled cross-fade, avoid abrupt flashing

## 8.3 Safety constraints for motion

- Do not use high-frequency flashing visual effects.
- Keep critical animations informative, not distracting.
- Offer reduced-motion friendly behavior where possible.

---

## 9) Performance and resilience UX requirements

### 9.1 Offline-first behavior

- Core triage flow must be operable without internet.
- Sync state must be explicit and non-blocking where safe.

### 9.2 Low-end device readiness

- Avoid heavy visual effects in always-on contexts.
- Prioritize responsiveness of primary actions over ornamental animation.

### 9.3 Error communication standard

Error text must include:

1. What happened
2. What user can do now
3. Whether data is safe/saved

---

## 10) QA and release checklist

## 10.1 Design-system compliance

- [ ] Token usage consistent with this spec
- [ ] No ad hoc colors for risk semantics
- [ ] Typography scale correctly applied
- [ ] Spacing and touch targets meet minimums

## 10.2 Accessibility compliance

- [ ] Contrast checks passed
- [ ] TalkBack path validated for key flows
- [ ] Semantics labels and roles complete
- [ ] Traversal order validated in complex layouts
- [ ] Custom components expose proper actions/state

## 10.3 Workflow reliability

- [ ] Offline path tested end-to-end
- [ ] Sensor-noise path tested
- [ ] Critical escalation path tested
- [ ] Loading/empty/error states present and readable

## 10.4 Content clarity

- [ ] Action-first copy pattern upheld
- [ ] Plain language and anti-jargon rules upheld
- [ ] Numerical values carry interpretation context

---

## 11) Handoff notes for engineering

### 11.1 Existing implementation alignment

Current implementation references:

- `ui/theme/Color.kt`
- `ui/theme/Type.kt`
- `ui/theme/Shape.kt`
- `ui/components/RiskBadge.kt`
- `ui/components/VitalGauge.kt`
- `ui/screens/RecommendationScreen.kt`

### 11.2 Recommended next implementation hardening

1. Introduce centralized spacing/motion token files.
2. Add explicit semantic utilities for alert/error/progress components.
3. Add automated accessibility checks in Compose UI tests.
4. Add locale-aware typographic line-height helper utility.

---

## 12) Versioning policy

- **Minor version:** copy/layout refinements without semantic changes.
- **Major version:** risk semantics, token architecture, accessibility contract changes.
- Any change touching critical-state UI must include safety review notes.

---

## Appendix A — Research foundation (separate citation appendix)

### A1) Material Design 3

- Color system overview:  
  https://m3.material.io/styles/color/overview
- Color internals/how it works:  
  https://m3.material.io/styles/color/system/how-the-system-works
- Color roles and pairing rules:  
  https://m3.material.io/styles/color/the-color-system/key-colors-tones
- Scheme selection (static vs dynamic):  
  https://m3.material.io/styles/color/choosing-a-scheme
- Dynamic color overview:  
  https://m3.material.io/styles/color/dynamic-color/overview
- Typography overview + applying type:  
  https://m3.material.io/styles/typography/overview  
  https://m3.material.io/styles/typography/applying-type
- States overview, layers, and application:  
  https://m3.material.io/foundations/interaction/states/overview  
  https://m3.material.io/foundations/interaction/states/state-layers  
  https://m3.material.io/foundations/interaction/states/applying-states
- Accessible design overview:  
  https://m3.material.io/foundations/accessible-design/overview

### A2) Android and Compose accessibility

- Compose accessibility overview:  
  https://developer.android.com/develop/ui/compose/accessibility
- API defaults:  
  https://developer.android.com/develop/ui/compose/accessibility/api-defaults
- Semantics:  
  https://developer.android.com/develop/ui/compose/accessibility/semantics
- Traversal order:  
  https://developer.android.com/develop/ui/compose/accessibility/traversal
- Merging and clearing:  
  https://developer.android.com/develop/ui/compose/accessibility/merging-clearing
- Scalable content:  
  https://developer.android.com/develop/ui/compose/accessibility/scalable-content
- Accessibility testing:  
  https://developer.android.com/develop/ui/compose/accessibility/testing
- Android accessibility principles/apps guidance:  
  https://developer.android.com/guide/topics/ui/accessibility/principles  
  https://developer.android.com/guide/topics/ui/accessibility/apps

### A3) Standards and plain-language guidance

- WCAG 2.1 quick reference:  
  https://www.w3.org/WAI/WCAG21/quickref/
- Plain language main guide:  
  https://digital.gov/guides/plain-language/
- Writing for understanding:  
  https://digital.gov/guides/plain-language/writing
- Clear and short writing:  
  https://digital.gov/guides/plain-language/writing/clear-short
- Principles (short/simple + avoid jargon):  
  https://digital.gov/guides/plain-language/principles/short-simple  
  https://digital.gov/guides/plain-language/principles/avoid-jargon
- Design for understanding (headings/lists):  
  https://digital.gov/guides/plain-language/design  
  https://digital.gov/guides/plain-language/design/headings  
  https://digital.gov/guides/plain-language/design/lists

### A4) Inclusion and field context

- Noto multilingual type ecosystem:  
  https://fonts.google.com/noto
- Mobile UX constraints and strengths:  
  https://www.nngroup.com/articles/mobile-ux/
- WHO assistive technology fact sheet:  
  https://www.who.int/news-room/fact-sheets/detail/assistive-technology
- WHO global report on assistive technology:  
  https://www.who.int/publications/i/item/9789240049451
- WHO global strategy on digital health 2020–2025:  
  https://www.who.int/publications/i/item/9789240020924

---

## Appendix B — Screen-level test scenarios (minimum set)

### B1) Recommendation critical path

- Given: critical risk classification  
- Verify: badge urgency, command language, emergency actions, accessibility announcement

### B2) Offline triage continuity

- Given: no gateway connection  
- Verify: triage flow remains operable, status clear, no hidden failure

### B3) Low-vision readability

- Given: high font scale and bright ambient conditions  
- Verify: no clipping of primary actions, contrast remains sufficient

### B4) Traversal integrity

- Given: TalkBack navigation through complex cards  
- Verify: logical order, merged groups correct, no decorative noise
