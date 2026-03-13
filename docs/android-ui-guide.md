This is a rich design conversation — let me go deep across every dimension of the visual system. Here is the complete AyushBot design language documented as a living design spec.

***

# AyushBot — Visual Design System & UX Language
## Brand Identity · Color · Typography · Layout · Motion · Accessibility

***

## 1. Design Identity: What AyushBot Must *Feel* Like

Before a single color is chosen or a typeface is picked, the emotional contract with the user must be defined. AyushBot is used by women working alone in remote villages, assessing sick children under time pressure, often with a phone in one hand and a child in the other. The app's personality must answer this situation directly.

**Four emotional words govern every design decision:**

- **Calm.** The visual environment must not add stress to an already stressful situation. No jarring transitions, no competing visual noise, no anxiety-inducing red dominating the interface.
- **Trustworthy.** Every screen must feel like it was built by someone who understands medicine. Clinical precision in layout, conservative typography, citations always visible. Nothing that looks like a consumer chat app.
- **Immediate.** The most important information on any screen must be readable in under 2 seconds without searching for it. Hierarchy is everything.
- **Human.** This is not a robot. It is a co-pilot that speaks the ASHA's language, uses her script, and addresses her by name. Warmth must exist underneath the clinical precision.

These four words are the design north star. When a decision is ambiguous, ask: does this feel calm, trustworthy, immediate, and human? If the answer is no to any of them, the decision is wrong. [naskay](https://naskay.com/blog/color-psychology-in-healthcare-ui-2025/)

***

## 2. The Color System

AyushBot uses the **Material Design 3 color role architecture** — not a flat palette, but a dynamic token-based system where colors are defined by their purpose (role) and generated from a small set of seed colors via the HCT (Hue-Chroma-Tone) color space. [m3.material](https://m3.material.io/styles/color/overview)

### 2.1 Seed Color Selection and Philosophy

**Primary Seed — Teal (H: 186°, C: 40, T: 35)**
`#006874` in light mode — the foundation of the brand.

Teal is the deliberate choice over the obvious medical blue for three specific reasons:

1. Blue dominates healthcare apps globally — teal differentiates AyushBot while retaining the psychological associations of calm and trust that blue-family hues carry. Blue-family apps show 20% higher user retention in healthcare settings. [naskay](https://naskay.com/blog/color-psychology-in-healthcare-ui-2025/)
2. Teal reads as both modern and clinical. It bridges the warmth of green (associated with healing, nature, life) and the professionalism of blue (calm, trust, authority) in a single hue.
3. In many Indian cultural contexts, teal and turquoise carry deeply positive associations — used in traditional jewelry, temple architecture, and textile arts.

**Secondary Seed — Warm Saffron (H: 38°, C: 35, T: 40)**
`#7D5700` in light mode.

Saffron is the visual signal for "attention but not emergency." It is used for medium-risk states, follow-up reminders, and pending sync indicators. It is also the only color with strong Indian cultural resonance — grounding the app in its geographic context without being clichéd.

**Tertiary Seed — Forest Green (H: 130°, C: 25, T: 35)**
`#386A20` in light mode.

Green encodes confirmed safety, successful actions, and low-risk outcomes. It is never used decoratively — only for positive clinical state confirmation.

**Error / Emergency — Deep Red**
`#BA1A1A` in light mode. This is the Material 3 default error color, retained because it carries universal emergency meaning. Used only for Critical risk states, DANGER alerts, and destructive actions. Never used as a brand color.

### 2.2 Complete Light Mode Token Set

```
Primary:          #006874   (teal, main interactive elements)
OnPrimary:        #FFFFFF   (text/icons on primary)
PrimaryContainer: #97F0FF   (soft teal, card backgrounds)
OnPrimaryContainer: #001F24

Secondary:        #4A6267   (muted teal for secondary labels)
SecondaryContainer: #CCE8ED
OnSecondaryContainer: #051F23

Tertiary:         #7D5700   (saffron, attention/medium risk)
TertiaryContainer: #FFDDB3
OnTertiaryContainer: #281900

Error:            #BA1A1A   (red, emergency/critical only)
ErrorContainer:   #FFDAD6
OnErrorContainer: #410002

Background:       #FAFDFD   (near-white, warm undertone)
Surface:          #FAFDFD
SurfaceVariant:   #DBE4E6   (card surfaces, list items)
OnSurface:        #191C1D   (primary text)
OnSurfaceVariant: #3F484A   (secondary text, labels)
Outline:          #6F797A   (borders, dividers)
OutlineVariant:   #BFC8CA
```

### 2.3 Clinical State Color Palette (Outside Material 3 Roles)

These four colors exist as a standalone semantic system for risk communication. They sit outside the brand palette and must never be used for decorative purposes: [microsoft](https://www.microsoft.com/en-us/research/publication/designing-mobile-interfaces-for-novice-and-low-literacy-users/)

| Risk Tier | Color Token | HEX | Psychological Rationale |
|---|---|---|---|
| Low / Safe | `StateGreen` | `#1B6E2C` | Strong enough green to be unambiguous on any background |
| Medium / Monitor | `StateAmber` | `#B45309` | Amber rather than orange — less alarming, clearly non-safe |
| High / Refer | `StateDeepOrange` | `#C2410C` | Urgent without triggering panic — red-orange, not red |
| Critical / Emergency | `StateCrimson` | `#9B1C1C` | Reserved exclusively for true emergencies |

Every risk state also carries a **non-color indicator**: an icon, a text label, and (for Critical) a haptic and audio signal. Color is never the sole carrier of meaning. [dx.plos](https://dx.plos.org/10.1371/journal.pone.0290923)

### 2.4 Dark Mode

The dark mode palette is generated from the same four seed colors via the M3 tonal palette system. Key tokens in dark mode:

```
Primary:          #4FD8EB   (bright teal on dark surface)
PrimaryContainer: #004F58   (dark teal container)
Background:       #191C1D   (near-black, warm dark)
Surface:          #191C1D
SurfaceVariant:   #3F484A
OnSurface:        #E1E3E3
```

Dark mode is offered as an option in Settings, defaulting to the system preference. Given that many ASHA workers visit homes at dawn or dusk, dark mode is a genuine usability feature and not merely cosmetic.

### 2.5 Dynamic Color — Opt Out

Material 3's Dynamic Color system (Android 12+, wallpaper-derived palette) is **explicitly disabled** in AyushBot. The reason is clinical: the risk state color palette (green, amber, deep orange, crimson) must remain absolutely invariant regardless of the user's wallpaper. Dynamic Color could theoretically override `StateGreen` to a color indistinguishable from `StateAmber` on a particular wallpaper. In a medical context, this is unacceptable. The static, hardcoded palette always wins.

***

## 3. Typography

### 3.1 Typeface Selection

**Primary Typeface — Noto Sans (Display, Heading, Body)**

Noto Sans is the definitive choice for a multilingual Indian health app. Its single design rationale: it is the only widely available typeface that renders all 22 scheduled Indian languages — Devanagari, Bengali, Tamil, Telugu, Kannada, Odia, Gurmukhi, and all others — with equal quality, equal visual weight, and equal optical sizing. This is non-negotiable for an app that serves 13+ Indian language communities.

Beyond multilingual support, Noto Sans is:
- Commissioned by Google specifically to eliminate the "tofu" (□□□) rendering problem for missing glyphs
- Humanist in character — a warm, open sans-serif that reads as approachable without being childish
- Hinted for small screen rendering at low DPI, making it legible on older Android phones with 360dp or lower screen widths

**Secondary Typeface — Noto Serif (Callouts, Citations, Protocol Text)**

When displaying retrieved clinical protocol text — the raw passage from an IMCI or MoHFW document that underpins a diagnosis — Noto Serif is used. The typographic shift from sans to serif signals to the ASHA that she is reading a source document, not a system-generated statement. This is a subtle but powerful trust indicator. It says: *this is not what the app invented — this is what the textbook says.*

**Monospace — JetBrains Mono (Vitals Display)**

The live numeric displays for SpO₂ (%), Heart Rate (BPM), Temperature (°C), and Weight (kg) use JetBrains Mono. Monospace ensures that numbers never shift horizontally as values change — a critical stability requirement for readings updating every 5 seconds. Watching "98" jump to "97" should not cause the surrounding layout to reflow.

### 3.2 Type Scale (Material 3 + Custom Extensions)

The complete type scale with specific sizes, weights, and line heights for AyushBot:

| Role | Font | Size | Weight | Line Height | Use |
|---|---|---|---|---|---|
| `displayLarge` | Noto Sans | 57sp | 400 | 64sp | Splash/Onboarding headlines |
| `displayMedium` | Noto Sans | 45sp | 400 | 52sp | Empty state headlines |
| `headlineLarge` | Noto Sans | 32sp | 600 | 40sp | Screen titles (Recommendation screen) |
| `headlineMedium` | Noto Sans | 28sp | 600 | 36sp | Risk badge label text |
| `headlineSmall` | Noto Sans | 24sp | 600 | 32sp | Card section headers |
| `titleLarge` | Noto Sans | 22sp | 600 | 28sp | Bottom nav labels (active) |
| `titleMedium` | Noto Sans | 16sp | 600 | 24sp | Card titles, form labels |
| `titleSmall` | Noto Sans | 14sp | 600 | 20sp | Chip labels, tab labels |
| `bodyLarge` | Noto Sans | 16sp | 400 | 24sp | Primary body text, checklists |
| `bodyMedium` | Noto Sans | 14sp | 400 | 20sp | Secondary body text, captions |
| `bodySmall` | Noto Sans | 12sp | 400 | 16sp | Citation tags, timestamps |
| `labelLarge` | Noto Sans | 14sp | 500 | 20sp | Buttons, FAB labels |
| `labelMedium` | Noto Sans | 12sp | 500 | 16sp | Badge labels, status chips |
| `vitalDisplay` | JetBrains Mono | 48sp | 700 | 56sp | Live SpO₂/HR/Temp readings |
| `vitalUnit` | JetBrains Mono | 16sp | 400 | 20sp | Unit labels (%, BPM, °C) |
| `sourceText` | Noto Serif | 14sp | 400 | 22sp | Protocol citation passages |

All sizes are specified in **sp (scale-independent pixels)**, ensuring the entire type scale responds to the system font size accessibility setting. [coldfusion-example.blogspot](https://coldfusion-example.blogspot.com/2025/01/handling-font-scaling-in-jetpack.html)

### 3.3 Language-Specific Typography Adjustments

Different Indian scripts have different optical size characteristics. A 16sp Devanagari character appears visually larger than a 16sp Latin character due to the horizontal headline bar (shirorekha) and the taller cap height. AyushBot applies per-language line height multipliers:

- **Devanagari (Hindi, Marathi):** line height × 1.3 (ascenders and descenders require more breathing room)
- **Bengali:** line height × 1.25 (complex conjunct consonants occupy more vertical space)
- **Tamil/Telugu/Kannada:** line height × 1.2 (circular and looping letterforms)
- **Latin (English):** line height × 1.0 (baseline)

These multipliers are applied programmatically based on the system locale — the ASHA never sees these adjustments, but they ensure that no script appears cramped or unnaturally tight.

***

## 4. Iconography

**Icon Library — Material Symbols (Rounded variant)**

The rounded variant of Material Symbols is the only appropriate choice for a healthcare app targeting non-technical users. Sharp corners signal hard technology; rounded corners signal approachability and warmth. All icons use the variable font axis at weight 400, grade 0, optical size 24.

**Clinical Icon Set — Custom on Top of Material Symbols**

Material Symbols does not cover several critical clinical concepts. A set of custom icons is designed using the same 24dp grid, 2dp stroke weight, and rounded corner radius as Material Symbols:

- Pulse oximeter (finger sensor with waveform)
- SpO₂ level (lungs with percentage)
- Weight scale (pediatric scale)
- ASHA worker (silhouette figure with bag)
- Referral (hospital building with arrow)
- Protocol document (document with caduceus watermark)
- Village cluster (hut cluster map view)

**Icon Communication Rules:**

Icons in AyushBot are never used alone without a text label on primary interactions — complying with established low-literacy mHealth design research which shows that icon-only interfaces are error-prone even for literate but novice users. The single exception: the emergency alarm icon (⚠️ triangle with exclamation) used in the Critical risk banner, which is universal and does not require text reinforcement. [microsoft](https://www.microsoft.com/en-us/research/publication/designing-mobile-interfaces-for-novice-and-low-literacy-users/)

***

## 5. Shape System

Material 3's shape tokens define the rounding radius of surfaces. AyushBot applies rounding deliberately — not uniformly: [m3.material](https://m3.material.io)

| Surface Type | Shape | Corner Radius | Rationale |
|---|---|---|---|
| FAB (New Visit button) | ExtraLarge | 28dp | Maximum roundness for maximum approachability on primary action |
| Cards (Case History, Recommendation) | Large | 16dp | Clearly bounded but not harsh |
| Buttons (primary) | Full | 50% | Pill shape, soft — consistent with M3 recommendations |
| Chips (filter, source citation) | Small | 8dp | Distinguished from buttons, clearly compact |
| Bottom Sheet | ExtraLarge (top only) | 28dp top | Standard M3 modal sheet |
| Alert Dialogs | Medium | 12dp | More formal, less playful — decisions happen here |
| Risk Badge Banner | Zero (full-width) | 0dp | Full-bleed banners have no corner radius — they claim the entire screen width as a signal of importance |
| Sensor Gauge Rings | Circle | 50% | Circular vitals gauges have inherent circular shape |
| Text Fields | ExtraSmall | 4dp | Conservative — data entry is a serious task |

***

## 6. Layout System and Spacing

### 6.1 Grid

AyushBot uses a **4dp base grid** for all spacing. Every margin, padding, gap, and height is a multiple of 4. This creates visual rhythm and prevents the micro-misalignments that make interfaces feel amateurish.

Key layout constants:
- **Screen horizontal padding:** 16dp (standard M3 margin for phones)
- **Card internal padding:** 16dp top/bottom, 16dp left/right
- **Section vertical spacing:** 24dp between major sections on a screen
- **List item height:** Minimum 56dp (ensures comfortable touch target even without a declared touch target overlay)
- **Bottom Navigation height:** 80dp (generous — accommodates thumb navigation)
- **FAB size:** 56dp × 56dp standard, with 16dp label margin

### 6.2 Elevation and Depth

AyushBot uses a flat-ish design — M3 tonal elevation (not shadow-based). Cards and surfaces that need to communicate "this is interactive" use a slightly elevated tonal fill (2dp tonal elevation = `SurfaceVariant` color with 8% primary overlay) rather than drop shadows. This keeps the interface clean and prevents the visual noise of multiple competing shadows. [developer.android](https://developer.android.com/develop/ui/compose/designsystems/material3)

The one exception: the FAB uses a standard M3 shadow elevation of 6dp to ensure it reads as floating above the content below it, which is critical for its discoverability.

### 6.3 Screen Anatomy — How Every Screen is Built

Every screen in AyushBot follows an identical structural template:

```
┌────────────────────────────────────┐
│  Status Bar (system, teal tinted)  │  24dp
├────────────────────────────────────┤
│  Top App Bar                       │  64dp
│  [Back arrow] [Screen Title] [⋮]  │
├────────────────────────────────────┤
│                                    │
│  Content Area                      │  flex
│  (scrollable, 16dp H padding)      │
│                                    │
│                                    │
├────────────────────────────────────┤
│  Bottom Navigation Bar             │  80dp
│  [Home] [+New] [History] [⚙ ]     │
└────────────────────────────────────┘
```

The Top App Bar collapses on scroll (M3 `TopAppBar` with `enterAlwaysScrollBehavior`) on long scrollable screens (Case History, Settings). On short or wizard-step screens, the top bar is pinned.

***

## 7. Component Deep-Dives

### 7.1 The Risk Badge — Most Critical UI Element

The Risk Badge is the single most important component in the app. The ASHA must be able to read it in under 1 second under bright sunlight on a 5-year-old Android phone. It is designed with exactly this constraint.

**Anatomy:**
- Full-width banner, zero corner radius, bleeds edge to edge
- Height: 96dp — large enough to fill the visual field without scrolling
- Left edge: a 6dp solid color bar (an additional color signal for peripheral vision)
- Icon: 40dp × 40dp, centered left, white on colored background
- Title text: `headlineMedium` (28sp, weight 600), white on colored background
- Subtitle: `bodyLarge` (16sp, weight 400), white at 87% opacity

**The Critical variant adds:**
- Pulsing background animation: the banner background oscillates between `StateCrimson` and a 20% brighter variant at 1.2Hz (slow enough to not feel seizure-inducing, fast enough to be attention-grabbing)
- Haptic pattern: `VibrationEffect.createWaveform([0, 200, 100, 200])` — two strong pulses
- Sound: A short, non-alarming but urgent two-tone chime

**Why no "traffic light" alone:**
Research on low-literacy mHealth users in India confirms that color alone is unreliable. The Risk Badge therefore has three redundant signals: color, icon shape, and text label. A colorblind ASHA reads "EMERGENCY" in large text and sees an exclamation triangle. She does not need to distinguish crimson from amber. [naskay](https://naskay.com/blog/color-psychology-in-healthcare-ui-2025/)

### 7.2 The Vitals Gauge Component

Three circular ring gauges sit side-by-side on the Sensor Capture screen.

**Each gauge anatomy:**
- Outer ring: 120dp diameter, `SurfaceVariant` background ring
- Colored progress ring: stroke width 8dp, color-coded (SpO₂ = teal, HR = warm red, Temp = orange)
- Center: `vitalDisplay` (48sp JetBrains Mono, weight 700) showing the live number
- Below center: `vitalUnit` (16sp JetBrains Mono, weight 400) for the unit
- Below the circle: `labelMedium` (12sp) for the sensor name

**Signal quality indicator:**
A thin linear progress bar below each gauge shows reading stability. It fills from 0% (unstable, moving) to 100% (5 consecutive stable readings within ±1% variance). The "Record Vitals" button is disabled and grayed out until all three bars reach 100%. This prevents the ASHA from accidentally recording a noisy reading.

**Color thresholding on the gauges:**
The ring color changes dynamically:
- SpO₂ ≥ 95%: ring = `StateGreen`
- SpO₂ 90–94%: ring = `StateAmber`
- SpO₂ < 90%: ring = `StateCrimson` + pulse animation

This gives the ASHA an instant visual feedback loop during measurement even before she submits the case.

### 7.3 The Symptom Card Grid

20 symptom cards in a responsive 2-column grid.

**Each card anatomy:**
- 160dp × 80dp cards on a standard phone width
- Large icon (36dp) left-aligned, `PrimaryContainer` background circle (48dp)
- Label text: `titleMedium` (16sp, weight 600) in the ASHA's language
- Toggle state: when selected, entire card background shifts from `Surface` to `PrimaryContainer`, border changes to `Primary` 2dp stroke, checkmark appears in top-right corner
- Micro-animation on tap: a subtle 80ms scale pulse (0.97 → 1.0) provides physical feedback

**Grouping with visual dividers:**
The 20 symptoms are grouped into 5 categories (Respiratory, Danger Signs, Nutrition, Neonate, Fever/Diarrhea). Each group has a `headlineSmall` label and a subtle `OutlineVariant` divider above it. This reduces the cognitive scanning load from "find one of 20 items" to "find one of 4 items in the right group."

### 7.4 The Recommendation Detail Card System

The Recommendation screen uses a card stack hierarchy. Cards are not generic containers — each card type has a distinct visual signature:

**Diagnosis Card** (white with `PrimaryContainer` top accent strip):
- 4dp top border in `Primary` teal
- `titleLarge` for diagnosis name
- 3-dot confidence indicator (filled dots for Confident, 2 filled for Likely, 1 for Low)
- Below: `sourceText` (Noto Serif, 14sp) for the citation passage, in a slightly inset frame with a left `OutlineVariant` 2dp bar — visually communicating "this is a quote"

**Action Card** (white, expandable):
- Collapsed state shows only the section header + chevron
- Expanded state reveals full content
- Expand/collapse uses `AnimatedVisibility` with a 250ms spring animation (not a linear ease — spring gives it a physical, natural feel)

**Referral Card** (teal-tinted `PrimaryContainer` background):
- Visually distinct from other cards — the elevated tonal fill signals importance
- Contains facility name in `headlineSmall`, distance chip, and a thumbnail map if the device can render one from the cached facility graph coordinates

***

## 8. Motion Design Language

Motion in AyushBot is purposeful. Every animation either:
1. **Orients** the user (this new content came from the right because I navigated forward)
2. **Confirms** an action (this card is selected because it bounced)
3. **Communicates state** (this reading is unstable because it pulses)

It never animates to show off. [m3.material](https://m3.material.io)

**Navigation transitions:**
- Forward navigation (screen → deeper screen): shared element transition where the tapped element expands to fill the new screen. Latency: 350ms with `FastOutSlowIn` easing.
- Back navigation: reverse of forward — the content collapses back to the source element. Latency: 300ms.
- Modal bottom sheets: slide up from bottom with `FastOutSlowIn`, overlay fades in at 60% opacity black.

**Content transitions:**
- Card appear on list scroll: cards fade in + slide up 12dp as they enter the viewport. Staggered 40ms per card. Prevents the jarring "pop" of 20 cards appearing simultaneously.
- Recommendation reveal: the Risk Badge fades in first (100ms), then the diagnosis card slides up from below it (200ms delay), then the action cards appear with a 100ms stagger. This sequence draws the eye down the page in the correct reading order.

**State change animations:**
- Risk gauge ring color shift (safe → alarm): cross-fades over 300ms, not an instant jump. A sudden color change is startling; a 300ms cross-fade is still urgent but not alarming.
- Critical badge pulse: `infiniteTransition` with `FastOutSlowIn` forward and `LinearOutSlowIn` reverse at 1.2Hz.
- Button press: `scale(0.96)` on down, `scale(1.0)` on up. 80ms. Provides physical press feel.

**Skeleton loading:**
While waiting for the gateway response (the "Analyzing..." state), the Recommendation screen shows a skeleton — gray animated shimmer boxes in the shape of the Risk Badge and two cards. This prevents layout shift when content arrives and feels more responsive than a spinner.

***

## 9. Voice-First Interface Design

Voice interaction is not an afterthought — it is a first-class design mode. Every primary action has a voice path.

**Microphone input button design:**
- Large circular FAB variant: 72dp diameter (larger than standard FAB to encourage tap confidence)
- `Primary` teal background with white microphone icon
- Tap-once to start recording, tap-again to stop (not push-to-hold — one-handed operation)
- Listening state: the button background pulses with a 1Hz sine wave in brightness, and a circular ripple expands outward from the button at 2Hz — a visual "I am listening" signal
- The transcription appears as text in a `bodyLarge` speech bubble above the button in real time as the ASHA speaks

**TTS playback button design:**
- Placed at the bottom of the Recommendation screen, full-width, prominent
- Speaker icon + label in the ASHA's language: "🔊 सुनें" / "🔊 শুনুন" / "🔊 கேளுங்கள்"
- During playback: button shifts to a "pause" state with a thin animated waveform progress bar spanning the button width
- The sentence currently being read aloud is highlighted in the recommendation text above — synchronized karaoke-style so the ASHA can follow along visually

***

## 10. Accessibility: Non-Negotiable Requirements

The accessibility requirements are not a checklist — they are structural design decisions. [linkedin](https://www.linkedin.com/posts/androiddev_want-to-make-your-apps-more-accessible-with-activity-7349516647633702912-UgQC)

**Contrast ratios:**
- All body text on surfaces: minimum WCAG AA (4.5:1). In practice, AyushBot's dark text (`#191C1D`) on light background (`#FAFDFD`) achieves 16.5:1.
- Risk badge white text on colored backgrounds: minimum 4.5:1 for all four risk tier colors. StateCrimson (`#9B1C1C`) at 4.8:1 is the tightest — verified passing. [naskay](https://naskay.com/blog/color-psychology-in-healthcare-ui-2025/)
- Sensor gauge numbers: JetBrains Mono 48sp bold on `SurfaceVariant` background achieves 12:1.

**Touch targets:**
- All interactive elements: minimum 48dp × 48dp touch target, even if the visual element is smaller. Implemented via `Modifier.minimumInteractiveComponentSize()` in Compose. [linkedin](https://www.linkedin.com/posts/androiddev_want-to-make-your-apps-more-accessible-with-activity-7349516647633702912-UgQC)
- FAB: 56dp visual, 72dp touch target with transparent padding.
- Symptom checklist cards: 160dp × 80dp — well above minimum.

**Screen reader (TalkBack) support:**
Every composable has a `contentDescription` in the ASHA's selected language. Custom semantics are defined for the vitals gauges (TalkBack reads: "SpO₂ reading: 97 percent, stable") and the risk badge ("Risk level: Low. Home management recommended."). The symptom cards use `Role.Checkbox` semantics so TalkBack announces checked/unchecked state. [developer.android](https://developer.android.com/develop/ui/compose/accessibility)

**Font scaling:**
All text uses `sp` units. The app is tested at 0.85×, 1.0×, 1.15×, 1.3×, and 1.5× system font scale. At 1.5× scale, multi-line labels in the symptom grid are accounted for with `maxLines = 2` and `overflow = TextOverflow.Ellipsis`, and card heights flex to `wrapContentHeight()` rather than fixed dp. [coldfusion-example.blogspot](https://coldfusion-example.blogspot.com/2025/01/handling-font-scaling-in-jetpack.html)

**One-handed operation:**
All primary interactions are reachable by the right thumb from the bottom of the screen. The FAB is bottom-right. The bottom navigation is accessible from the bottom center. The most-used buttons (Record Vitals, Submit, Voice Play) are in the bottom 40% of the screen. The top app bar is reserved for navigation only (back, overflow menu) — never for primary actions.

***

## 11. Low-Literacy and Novice User Patterns

Research specifically on low-literacy users in India — including 90 subjects across four countries in a Microsoft Research study — shows that textual interfaces fail entirely for this population, and that graphical interfaces with speech assistance dramatically outperform text-only experiences. AyushBot applies these findings directly: [microsoft](https://www.microsoft.com/en-us/research/publication/designing-mobile-interfaces-for-novice-and-low-literacy-users/)

**Progressive disclosure everywhere:**
Never show the ASHA more information than she needs at this moment. The Recommendation screen's action cards are collapsed by default. The differential diagnoses accordion is collapsed. Only the Risk Badge and Primary Diagnosis Card are expanded on arrival. Additional detail is always one tap away but never forced.

**Confirmation for destructive actions only:**
A confirmation dialog (M3 AlertDialog) appears only when the ASHA attempts to delete a case or discard an in-progress triage form. For all positive actions (recording vitals, submitting a case, generating a referral slip), there is no confirmation step — the action completes immediately. Interrupting a positive action flow with "Are you sure?" is a documented usability failure for non-expert users. [papers.ssrn](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4982726)

**Error messages in plain language:**
Errors never say "Network timeout occurred" or "MQTT connection refused." They say "AyushBot couldn't reach the PHC. Your case is saved and will be sent later." Every error message must answer: what happened, and what the ASHA should do (or not do) next.

**Onboarding as progressive disclosure:**
The first launch onboarding flow teaches one concept per screen. Language selection first because every subsequent screen must be in the right language. Profile setup second. Gateway pairing last and optional. Nothing about features, nothing about system architecture, nothing about AI.

***

## 12. Screen-by-Screen Visual Inventory

A quick visual identity summary for each screen, defining its dominant visual element:

| Screen | Dominant Visual | Primary Color Surface | Voice Available |
|---|---|---|---|
| Onboarding Language | Language flag grid, large script samples | White | No |
| Home Dashboard | Today's stats row + color-coded recent case list | `Background` | Yes (new visit) |
| Sensor Capture | Three 120dp circular gauges + signal quality bars | `Background` | No |
| Symptom Checklist | 2-column icon card grid with group headers | `SurfaceVariant` | Yes (add symptom) |
| Analyzing | Full-screen skeleton shimmer + waveform animation | `Background` | No |
| Recommendation | Full-width Risk Badge + card stack | Risk tier color → `Background` | Yes (TTS playback) |
| Referral Slip | Document-style layout, serif typography | White (print-ready) | No |
| Case History | Dense list, filter chips, search | `Background` | No |
| Voice Query | Chat bubble interface, microphone FAB | `Background` | Yes (primary mode) |
| Sensor Management | Live gauge panel + BLE device list | `Surface` | No |
| Settings | Standard M3 preference groups | `Background` | No |

***

## 13. What Makes This Visually Stunning *and* Right for the Context

The temptation in a student project is to make the interface flashy — gradients, glassmorphism, heavy animations. AyushBot must resist this and instead achieve visual beauty through **restraint and precision:**

- A perfectly consistent 4dp grid that makes every layout feel intentional
- The Noto typeface hierarchy that makes information breathe
- The clinical teal color that is genuinely beautiful and not seen in any competing app
- The Noto Serif citation passages that create a moment of visual texture amid sans-serif uniformity
- The JetBrains Mono vitals display that feels like a precision medical instrument
- The Risk Badge that fills the screen with unambiguous, unavoidable color when a child's life is at risk

Beautiful is not the same as decorative. AyushBot's beauty comes from things being exactly the right size, exactly the right color, and exactly in the right place — which is the hardest kind of design to get right, and the most powerful when it works. [dl.acm](https://dl.acm.org/doi/pdf/10.1145/3613904.3641976)