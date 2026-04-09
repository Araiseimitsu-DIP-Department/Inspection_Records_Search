# Design System Specification: The Quiet Architect

## 1. Overview & Creative North Star
The "Creative North Star" for this design system is **The Digital Curator**. 

Unlike standard "enterprise" software that clutters the interface with rigid grids and heavy borders, this system treats the desktop application as a gallery space. It is inspired by the precision of Swiss editorial design and the atmospheric depth of modern glass-based interfaces. 

We break the "template" look by prioritizing **negative space as a functional element**. By utilizing intentional asymmetry—such as oversized margins on one side and condensed utility panels on the other—we guide the eye through a narrative rather than a spreadsheet. The goal is an interface that feels less like a tool and more like a high-end, bespoke environment.

---

## 2. Colors & Tonal Architecture
The palette is rooted in a "High-Value White" philosophy. We do not use color to decorate; we use it to direct.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders to define sections or containers. 
Structure must be achieved through **Tonal Shifting**. A sidebar should be distinguished from the main canvas by moving from `surface` (#f8f9fa) to `surface-container-low` (#f1f4f6). If a boundary feels invisible, increase the contrast between the surface tiers rather than reaching for a stroke.

### Surface Hierarchy & Nesting
Treat the UI as a physical desk with stacked sheets of fine paper:
*   **Base Layer:** `surface` (#f8f9fa) – The infinite canvas.
*   **Functional Areas:** `surface-container-low` (#f1f4f6) – For navigation or utility panels.
*   **Active Workspaces:** `surface-container-lowest` (#ffffff) – Reserved for the primary content focus, providing a "pop" of brightness.
*   **Elevated Elements:** `surface-container-high` (#e3e9ec) – For temporary overlays or contextual menus.

### The "Glass & Gradient" Rule
To elevate the "Soft Blue" primary action (`primary`: #005bbf), use a subtle linear gradient transitioning to `primary_dim` (#0050a8). This adds "soul" to buttons, making them feel tactile rather than flat. For floating panels, apply **Glassmorphism**: use `surface` at 80% opacity with a `24px` backdrop blur to allow background colors to bleed through softly.

---

## 3. Typography: Editorial Authority
We pair the utilitarian precision of **Inter** with the geometric character of **Manrope** to create a sophisticated hierarchy.

*   **Display & Headlines (Manrope):** Use `display-lg` (3.5rem) and `headline-md` (1.75rem) with tighter letter-spacing (-0.02em). These are your "Editorial Anchors." They should be used sparingly to define the start of a journey.
*   **Body & Labels (Inter):** Use `body-md` (0.875rem) for all functional text. Inter’s high x-height ensures readability in data-heavy views.
*   **The Tonal Scale:** Use `on_surface_variant` (#586064) for secondary metadata. Never use pure black; it is too "heavy" for a premium minimalist aesthetic.

---

## 4. Elevation & Depth
Depth is created through light and shadow, not lines.

*   **The Layering Principle:** Instead of a shadow, place a `surface-container-lowest` card on a `surface-container-low` background. The slight shift in hex value creates a "natural lift."
*   **Ambient Shadows:** When a component must float (e.g., a dropdown or modal), use a shadow color tinted with the `on_surface` value: `box-shadow: 0 12px 40px rgba(43, 52, 55, 0.06)`. It should feel like a soft glow, not a dark smudge.
*   **The "Ghost Border" Fallback:** If a border is required for high-density data tables, use `outline_variant` (#abb3b7) at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Modern Data Tables
*   **No Vertical Lines:** Separate rows with `8px` of vertical white space or a very subtle background shift on hover (`surface-container-high`).
*   **Alignment:** Numeric data must be tabular-lining; headers should use `label-md` in uppercase with `0.05em` tracking.

### Sleek Input Fields
*   **Default State:** Background `surface-container-low`, no border, `DEFAULT` (0.25rem) or `md` (0.375rem) corner radius.
*   **Focus State:** A 2px "glow" using `primary` at 20% opacity. Avoid the harsh "outline" look.

### Buttons
*   **Primary:** Gradient from `primary` to `primary_dim`. Text: `on_primary` (#f7f7ff).
*   **Secondary:** Background `secondary_container` (#e4e2e6). No border.
*   **Tertiary:** Ghost style. Use `primary` text on a transparent background, shifting to `primary_container` on hover.

### Refined Chips
*   **Visuals:** Use `full` roundedness (9999px). Chips should use `tertiary_container` (#e1d8fa) for a soft, sophisticated alternative to standard blues or greys.

---

## 6. Do's & Don'ts

### Do
*   **Do** use asymmetrical padding. Give the top and left of your layout more "breathing room" than the bottom and right.
*   **Do** use `surface_bright` to highlight the most important interactive zone on a page.
*   **Do** utilize `xl` (0.75rem) roundedness for large containers to soften the "industrial" feel of the desktop app.

### Don't
*   **Don't** use dividers (`<hr>`). Use spacing. If you think you need a divider, add 24px of white space instead.
*   **Don't** use high-contrast shadows. If the shadow is clearly visible as a grey shape, it is too heavy.
*   **Don't** use standard "Select Blue" for everything. Reserve the `primary` blue for the single most important action on the screen. Use `secondary` or `tertiary` for everything else.
*   **Don't** use 100% opaque borders. Always use the "Ghost Border" rule (15-20% opacity).

---

## 7. Roundedness Scale
| Token | Value | Application |
| :--- | :--- | :--- |
| `none` | 0px | High-utility edge-to-edge panels |
| `sm` | 0.125rem | Tooltips, small tags |
| `DEFAULT` | 0.25rem | Standard input fields, small buttons |
| `md` | 0.375rem | Medium buttons, select menus |
| `lg` | 0.5rem | Standard cards, modal headers |
| `xl` | 0.75rem | Large main-content containers |
| `full` | 9999px | Search bars, chips, pill buttons |