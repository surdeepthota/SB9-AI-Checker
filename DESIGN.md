# Design System: PeachCheck Premium

## Overview
This design system defines a highly premium, modern, "Clean Corporate" aesthetic intended for government officials and heads of office. It completely rejects generic, "AI-looking" templates in favor of a sleek, meticulously crafted interface resembling top-tier B2B software (e.g., Stripe, Vercel).

The application must feel authoritative, secure, and incredibly crisp.

## 1. Color Palette

**Primary Colors (Authority & Trust)**
*   **Primary Brand:** Deep Navy Blue `#0f172a` (slate-900)
*   **Primary Action:** Vivid Cobalt `#2563eb` (blue-600)
*   **Background (Body):** Soft Off-White `#f8fafc` (slate-50)
*   **Card Background:** Pure White `#ffffff`
*   **Borders & Dividers:** Subtle Gray `#e2e8f0` (slate-200)

**Typography Colors**
*   **Text Primary (Headings):** `#0f172a` (slate-900)
*   **Text Secondary (Body/Labels):** `#475569` (slate-600)
*   **Text Tertiary (Metadata):** `#94a3b8` (slate-400)

**Semantic Feedback (Muted, professional hues)**
*   **Success (Passed/Verified):** Background `#dcfce7` / Text `#166534`
*   **Warning (Probabilistic/Review):** Background `#fef9c3` / Text `#854d0e`
*   **Danger (Failed/Tampered):** Background `#fee2e2` / Text `#991b1b`

## 2. Typography

We use modern, highly legible sans-serif typography. Avoid decorative fonts.
*   **Font Family:** `Inter`, `-apple-system`, `sans-serif`.
*   **Monospace (For data/code):** `JetBrains Mono`, `ui-monospace`.
*   **Headings:** Heavy weights (700-800), tight letter-spacing (`-0.02em`).
*   **Micro-copy / Badges:** Uppercase, heavy weight (700), wide letter-spacing (`0.05em`).

## 3. UI Components & Geometry

**Cards & Containers**
*   **No Glassmorphism:** Absolutely NO translucent backgrounds or heavy gradients.
*   **Radii:** Sharp, professional corners. Border-radius `6px` or `8px`.
*   **Shadows:** Extremely subtle. `box-shadow: 0 1px 3px rgba(0,0,0,0.05)`.
*   **Borders:** All cards must have a solid, 1px border (`#e2e8f0`).

**Buttons**
*   **Primary Button:** Solid Cobalt (`#2563eb`), white text, `6px` radius, no shadow.
*   **Secondary Button:** Pure white background, `1px` border (`#e2e8f0`), slate text.
*   **Padding:** Generous horizontal padding (e.g., `px-4 py-2`).

**Data Tables & Lists**
*   **Headers:** Uppercase, very small text (`11px` or `0.7rem`), text-tertiary color.
*   **Rows:** Border-bottom (`#e2e8f0`). Data cells should have generous vertical padding (`py-3`).

## 4. Layout Rules
*   **Whitespace:** Use abundant whitespace. Do not cram components together.
*   **Alignment:** Strict left-alignment for text. Right-alignment for numbers/metrics.
*   **Avoid:** Do not use centered, floating cards that look like generic login screens. Use full-width dashboards with sidebars or crisp top-navigation bars.
