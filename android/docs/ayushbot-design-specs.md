# AyushBot Android App — Design Specs Guide

## 1. Product Context and UX North Star

AyushBot is a clinical decision-support and triage companion for ASHA workers in rural India.
The Android app is the primary human interface into a deeptech stack: multi-agent EdgeRAG running on a PHC gateway, federated learning across districts, and a sophisticated IoT sensor pack for child and maternal assessment.
The visual and interaction design must:

- Reduce cognitive load under field stress.
- Build instant trust and a sense of safety.
- Make complex AI + IoT capabilities feel simple, predictable, and humane.
- Work reliably on low-cost Android devices and in multi-lingual, low-literacy contexts.

Design keywords: **Calm · Trustworthy · Immediate · Human**.

***

## 2. Platform & Technical Design Foundations

### 2.1 Target Platform

- Native Android app in Kotlin.
- Jetpack Compose UI with Material Design 3 (Material You) components.
- Single-activity, multi-screen architecture using `Navigation` for Compose.
- Minimum SDK 26, Target SDK latest stable.
- Offline-first: Room as single source of truth; WorkManager for background sync.

### 2.2 Layout Grid & Spacing System

- Base grid: **4 dp**.
- Screen horizontal padding: **16 dp**.
- Section vertical spacing: **24 dp** between major content blocks.
- Card padding: **16 dp** (all sides).
- Minimum touch target: **48 × 48 dp** for all interactive elements.
- Bottom navigation bar height: **80 dp**.

Use a consistent 4 dp rhythm across paddings, margins, and gaps.

### 2.3 Shape System

- Global shape scale:
  - Extra large: 28 dp (FAB, bottom sheets top corners).
  - Large: 16 dp (cards, primary containers).
  - Medium: 12 dp (dialogs, modals).
  - Small: 8 dp (chips, tags).
  - Extra small: 4 dp (text fields, subtle containers).
- Full-width banners (risk badges) use **0 dp** radius for maximum emphasis.

### 2.4 Elevation & Surfaces

Use tonal elevation, not heavy shadows.

- Surface: base (`surface` / `background`).
- Elevated card: `surfaceVariant` with 8% primary overlay.
- FAB: Material 3 default shadow elevation (6 dp) for affordance.

Avoid visual clutter from multiple overlapping shadows; rely on tone, outline, and shape.

***

## 3. Color Design for AyushBot

### 3.1 Brand Color Strategy

AyushBot sits between **clinical rigor** and **community empathy**.
The palette must communicate:

- Clinical competence and safety (blue / teal family).
- Growth, vitality, and rural context (green and earthy accent).
- Warmth and encouragement (saffron accent, used sparingly).

From healthcare color psychology research:

- Blue-dominated health apps show ~20% higher retention and higher perceived trust vs garish palettes.
- Greens are strongly associated with balance, growth, and recovery.
- Red should be reserved for alerts and critical states only, to avoid constant anxiety.

### 3.2 Core Brand Palette (Light Theme)

Define tokens in Material 3 terms; exact hex values can be tuned with design tools, but this is the baseline.

**Primary (Ayush Teal)**

- `primary`: `#006874` — Deep teal for brand identity and primary actions.
- `onPrimary`: `#FFFFFF`.
- `primaryContainer`: `#97F0FF` — Soft teal for cards and chips.
- `onPrimaryContainer`: `#001F24`.

Rationale: Teal fuses the trust of blue with the life/health connotations of green, and stands out from generic “medical blue” apps.

**Secondary (River Slate)**

- `secondary`: `#4A6267` — Muted blue-gray for secondary labels and icons.
- `onSecondary`: `#FFFFFF`.
- `secondaryContainer`: `#CCE8ED`.
- `onSecondaryContainer`: `#051F23`.

Use for secondary buttons, filter chips, and low-priority info.

**Tertiary (Saffron Accent)**

- `tertiary`: `#7D5700` — Warm saffron.
- `onTertiary`: `#FFFFFF`.
- `tertiaryContainer`: `#FFDDB3`.
- `onTertiaryContainer`: `#281900`.

Use for medium-risk states, educational callouts, and subtle highlights (never main backgrounds).

**Error / Critical**

- `error`: `#BA1A1A`.
- `onError`: `#FFFFFF`.
- `errorContainer`: `#FFDAD6`.
- `onErrorContainer`: `#410002`.

Reserved for true clinical emergencies and destructive actions.

**Neutrals**

- `background`: `#FAFDFD` — Off-white, slightly warm.
- `surface`: `#FAFDFD`.
- `surfaceVariant`: `#DBE4E6`.
- `onSurface`: `#191C1D`.
- `onSurfaceVariant`: `#3F484A`.
- `outline`: `#6F797A`.
- `outlineVariant`: `#BFC8CA`.

Neutrals must stay quiet; content and state colors carry meaning.

### 3.3 Clinical State Palette (Non-Brand)

Risk and clinical severity use a **separate semantic palette**.
This must never be repurposed for decoration.

- `stateSafe` (Low risk): `#1B6E2C` — Strong green.
- `stateCaution` (Monitor): `#B45309` — Amber.
- `stateHigh` (Refer): `#C2410C` — Deep orange.
- `stateCritical` (Emergency): `#9B1C1C` — Crimson.

Each risk tier must also have an icon and text label; color is never the only channel.

### 3.4 Dark Theme

Dark theme mirrors the same brand hues at different tones.

- `primary`: `#4FD8EB`.
- `onPrimary`: `#00363D`.
- `primaryContainer`: `#004F58`.
- `onPrimaryContainer`: `#97F0FF`.
- `background` / `surface`: `#191C1D`.
- `surfaceVariant`: `#3F484A`.
- `onSurface`: `#E1E3E3`.

Risk state colors are re-toned to maintain at least 4.5:1 contrast against dark surfaces.

### 3.5 Dynamic Color Policy

- **Dynamic Color (Material You)**: disabled by default for clinical state surfaces.
- Brand and risk colors are pinned to ensure consistent risk semantics across devices.
- Optionally, allow dynamic neutral surfaces (background/surface) while locking state colors.

***

## 4. Typography System

### 4.1 Typeface Choices

**Primary typeface: Noto Sans**

- Rationale: Noto covers all major Indian scripts (Devanagari, Bengali, Tamil, Telugu, Kannada, etc.).
- Style: Sans-serif, humanist, highly legible on low-DPI screens.

**Secondary typeface: Noto Serif**

- Used only for source/protocol citations and educational content.
- Visual cue that text is from an official guideline, not the AI.

**Numeric typeface: JetBrains Mono (optional)**

- For vitals (SpO₂, HR, RR, Temp, Weight) to prevent width jitter.

### 4.2 Type Scale (Light & Dark)

Base scale (can be mapped to Material 3 text styles):

- Display Large – 57 sp / 64 sp line height (splash headlines, hero states).
- Display Medium – 45 sp / 52 sp (rarely used; big empty states).
- Headline Large – 32 sp / 40 sp (top-level screen titles, e.g., recommendation screen heading).
- Headline Medium – 28 sp / 36 sp (Risk badge text: "EMERGENCY" / "Refer today").
- Headline Small – 24 sp / 32 sp (section headers like "What to do" / "Differentials").
- Title Large – 22 sp / 28 sp (primary navigation labels, prominent card titles).
- Title Medium – 16 sp / 24 sp (card subtitles, field labels).
- Title Small – 14 sp / 20 sp (chip labels, small headers).
- Body Large – 16 sp / 24 sp (main content, explanations, instructions).
- Body Medium – 14 sp / 20 sp (secondary text, helper copy, notes).
- Body Small – 12 sp / 16 sp (captions, timestamps, risk metadata).
- Label Large – 14 sp / 20 sp (button text, primary actions).
- Label Medium – 12 sp / 16 sp (badge labels, statuses).

Vitals display:

- `vitalValue`: 44–48 sp, bold.
- `vitalUnit`: 16 sp, regular.

### 4.3 Language-Specific Adjustments

Different scripts need different line-height multipliers:

- Devanagari / Bengali: ×1.25–1.3 line height.
- Tamil / Telugu / Kannada: ×1.2.
- Latin-only screens: ×1.1.

Implement programmatically using locale-aware style helpers.

### 4.4 Accessibility

- All typography uses `sp` units.
- Support system font scale 0.85×–1.5× without layout breakage.
- At 1.5×, cards grow vertically; truncation is allowed only for secondary text, never primary content.

***

## 5. Iconography & Visual Language

### 5.1 Icon Library

- Base set: Material Symbols Rounded.
- Icon size: 24 dp standard; 32–40 dp for high-priority tap targets.
- Stroke weight: consistent single weight (400 style for Material Symbols).

### 5.2 Custom Clinical Icons

Create a small custom icon set for:

- Pulse oximeter.
- Stethoscope / respiratory sound.
- Weight scale (pediatric-focused form factor).
- MUAC band.
- Water source (for SDG-6 related features).
- ASHA worker (person with bag and dupatta).

Maintain the same grid (24 dp), corner radius, and stroke weight as Material Symbols.

### 5.3 Icon Usage Rules

- Always pair icons with text on primary actions.
- Icon-only buttons allowed only for universally understood actions (back, close, microphone, speaker).
- No more than one high-attention icon per card; avoid visual noise.

***

## 6. Component Design Specs

### 6.1 Top App Bar

- Small top app bar with:
  - Navigation icon (back or drawer).
  - Screen title (Headline Small).
  - Optional trailing action icon (e.g., info, overflow).
- Height: 64 dp.
- Background: `surface`.
- Divider below bar using `outlineVariant`.

### 6.2 Bottom Navigation

- 3–4 destinations max:
  - Home.
  - New Visit.
  - History.
  - Settings.
- Center tab (New Visit) visually emphasized (larger icon, pill-shaped container).
- Labels always visible (no icon-only mode).

### 6.3 Risk Badge

- Full-width banner at top of Recommendation screen.
- Height: 96 dp.
- Background color: `stateSafe` / `stateCaution` / `stateHigh` / `stateCritical`.
- Left accent: 6 dp stripe in same or darker shade.
- Icon: 40 dp, left-aligned.
- Title: Headline Medium.
- Subtitle: Body Large (short explanation).

States:

- Safe: calm green, checkmark, copy like "Child is stable".
- Caution: amber, exclamation inside triangle, e.g., "Monitor closely".
- High: deep orange, hospital icon, e.g., "Refer to PHC today".
- Critical: crimson, alert icon, pulsing animation.

### 6.4 Vitals Panel

- 3–4 circular gauges in a row or 2×2 grid depending on screen width.
- Each gauge:
  - Diameter: 120 dp.
  - Outer ring: `surfaceVariant`.
  - Progress ring: state-based color (safe / caution / critical thresholds per vital).
  - Center numeric value and unit.
  - Label below (Body Medium).
- Signal quality indicator below gauges (small bar or text like "Reading: Good / Noisy").

### 6.5 Symptom Checklist Cards

- 2-column grid of cards with icons and labels.
- Card size: ~160 × 80 dp.
- Default state: `surface` background, outline = `outlineVariant`.
- Selected state: `primaryContainer` background, outline = `primary`, checkmark overlay.
- Each group of symptoms preceded by group header (e.g., "Breathing", "Danger signs").

### 6.6 Recommendation Card Stack

Order on screen (after risk badge):

1. Primary Diagnosis Card.
2. Action Plan Card (Treat / Refer / Counsel).
3. Differential Diagnoses Card (collapsed by default).
4. Evidence & Source Card.

**Primary Diagnosis Card**:

- Top border: 4 dp in `primary`.
- Title: diagnosis name (Title Large).
- Confidence indicator: 3 small circles (filled indicates confidence level).
- Short explanation: Body Large.

**Action Plan Card**:

- Split into subtabs or expandable sections:
  - Treat.
  - Refer.
  - Counsel.
- Use numbered steps for actions.

**Evidence & Source Card**:

- Noto Serif text.
- Clearly shows which protocol / guideline page the recommendation is grounded in.

### 6.7 Form Fields and Inputs

- Text fields: filled style with label and helper text.
- Error state: `error` border + helper text in `error`.
- Dropdowns: exposed dropdown menus for village, facility selection.
- Toggles: Material switches (for binary settings) and checkboxes (for multi-select lists).

### 6.8 Voice Interaction Controls

**Voice Input Button**:

- Large circular button (56–72 dp) with microphone icon.
- Idle: primary color background.
- Listening: pulsing ring animation.

**Voice Output Button**:

- Full-width pill at bottom: "Play Recommendation".
- On playback: animated waveform inside button.

***

## 7. Layouts for Key Screens

### 7.1 Home Screen

Layout structure:

- Top App Bar: title "AyushBot" + ASHA name.
- Content:
  - Today summary row (cards for "Visits", "Pending sync", "Alerts").
  - Quick actions row (New Visit, Case History, Voice Ask AyushBot, Emergency Referral).
  - Recent cases list (scrollable).
- Bottom navigation.

Visual priorities:

1. New Visit FAB / quick action.
2. Pending sync state.
3. Critical cases in history (use risk-state colors in list).

### 7.2 New Visit Flow

Four screens in a wizard:

1. Patient Details.
2. Sensor Capture.
3. Symptoms.
4. Review & Submit.

Each step:

- Progress indicator at top (e.g., 4-dot or labeled progress bar).
- Primary CTA at bottom (Next / Submit) pinned above bottom nav.

### 7.3 Recommendation Screen

Top-down hierarchy:

1. Risk Badge (full width).
2. Primary Diagnosis Card.
3. "What To Do Now" Card (actions).
4. "Why" Card (evidence summary).
5. Voice playback button.
6. Secondary actions (Generate referral slip, Share summary).

Scrolling allowed but primary information (badge + diagnosis + primary actions) should fit within first viewport on typical 6" screen.

### 7.4 Case History Screen

- Search bar at top.
- Filter chips (All, Today, Critical, Pending sync).
- List of cards:
  - Patient name / ID.
  - Date/time.
  - Risk badge chip.
  - Primary diagnosis.
- Tapping opens read-only detail.

### 7.5 Sensor Management Screen

- Connection status card (Node online/offline).
- Live vitals preview (gauges).
- Battery + signal bars.
- Button to run sensor self-test (displays individual sensor statuses with icons).

***

## 8. Motion & Transitions

### 8.1 Navigation Transitions

- Forward navigation (e.g., Home → New Visit): slide in from right, fade in.
- Back navigation: slide out to right, fade out.
- Modal bottom sheets: slide up from bottom with dimmed scrim.

### 8.2 Component Animations

- Risk badge state change: color cross-fade over 250 ms.
- Card expand/collapse: size + opacity animated over ~200 ms.
- Button press: 0.96→1.0 scale animation over 80 ms.

### 8.3 Skeleton Loading

- Use skeleton placeholders for recommendation content while waiting on gateway.
- Avoid global spinners; provide shape-consistent placeholders.

***

## 9. Accessibility & Health Literacy

- WCAG AA contrast minimum across all text and UI elements.
- All critical info must use **text + icon + color**, never color alone.
- Symptom text should be plain-language, locally translated, and often paired with an illustration.
- Avoid dense paragraphs; aim for short bullet points and chunked instructions.
- All interactive elements require descriptive content descriptions for TalkBack.

***

## 10. Design QA Checklist

Before shipping any screen:

- [ ] All text uses design system typography tokens.
- [ ] Color usage follows brand and clinical state palettes.
- [ ] Primary action is visually dominant and clearly labeled.
- [ ] Risk-related elements use correct state colors and iconography.
- [ ] All text is translatable (no hard-coded strings).
- [ ] Screen usable at 1.5× font scale and small device size.
- [ ] TalkBack reads content in a sensible order.
- [ ] Empty / loading / error states designed.