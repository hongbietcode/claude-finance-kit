# HTML Report Styles — ZaloPay Fintech Design System

Styles and layout hints only. Agents generate actual HTML based on these guidelines.

## Setup

Single self-contained HTML file. Libraries inlined by `scripts/build-html-report.py` (downloads + caches on first run):
- **Tailwind CSS** — styling framework
- **Plotly.js** — interactive charts

## Tailwind Config

Extend theme with these custom tokens:

| Token | Hex | Use |
|-------|-----|-----|
| `brand` | `#0068FF` | Primary blue, CTAs, links |
| `brand-dark` | `#0033C9` | Neutral/hold pill |
| `up` | `#01CD6B` | Positive values, bullish pill |
| `down` | `#FF3B30` | Negative values, bearish pill |
| `page` | `#F2F7FF` | Page body background |
| `surface` | `#FFFFFF` | Card background |
| `th` | `#E6F0FF` | Table header row |
| `ink` | `#142B43` | Primary body text |

Font stack: `SF Pro, Helvetica Neue, Arial, sans-serif`
Card shadow: `0 2px 12px rgba(0,104,255,0.08)`

## Page Container

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{PAGE_TITLE}}</title>
  <!-- Tailwind + Plotly inlined by scripts/build-html-report.py -->
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: '#0068FF', 'brand-dark': '#0033C9',
            up: '#01CD6B', down: '#FF3B30',
            page: '#F2F7FF', surface: '#FFFFFF',
            th: '#E6F0FF', ink: '#142B43',
          },
          fontFamily: { sans: ['SF Pro', 'Helvetica Neue', 'Arial', 'sans-serif'] },
          boxShadow: { card: '0 2px 12px rgba(0,104,255,0.08)' },
        }
      }
    }
  </script>
</head>
<body class="bg-page text-ink font-sans min-h-screen">
  <!-- Sticky Header -->
  <header class="sticky top-0 z-50 bg-surface shadow-sm px-6 py-3 flex items-center justify-between">
    <h1 class="text-lg font-bold text-brand">{{HEADER_LEFT}}</h1>
    <span class="text-sm text-gray-500">{{HEADER_RIGHT}}</span>
  </header>

  <!-- Main Content -->
  <main class="max-w-5xl mx-auto px-4 py-6 space-y-4">
    <!-- Cards go here -->
  </main>

  <!-- Footer -->
  <footer class="border-t border-blue-100 mt-8 py-4 text-center text-xs text-gray-400">
    {{FOOTER}}
  </footer>

  <!-- Plotly Charts (scripts at bottom) -->
</body>
</html>
```

## Layout Components

### Page Shell
- Body: `bg-page text-ink font-sans min-h-screen`
- Sticky header: `bg-surface shadow-sm`, brand text left, date/context right
- Main: `max-w-5xl mx-auto px-4 py-6 space-y-4`
- Footer: border-top, centered, `text-xs text-gray-400`, disclaimer text

### Card
- `bg-surface rounded-xl shadow-card p-6`
- Heading: `text-base font-semibold text-ink mb-4`

### Rating Pill
- Shared: `inline-flex items-center px-3 py-1 rounded-full text-xs font-bold text-white`
- Bullish: `bg-up` | Neutral: `bg-brand-dark` | Bearish: `bg-down`

### Table
- Full width, `text-sm border-collapse`
- Header row: `bg-th text-ink`, cells with `font-semibold border border-th`
- Body rows: `border-b border-blue-50 hover:bg-blue-50/40`
- Value cells: `text-right font-mono`

### Metric Card (KPI)
- `bg-th/50 rounded-lg p-3 text-center`
- Label: `text-xs text-gray-500` | Value: `text-lg font-bold text-ink` | Change: `text-xs font-medium`

### Value Coloring
- Positive: `text-up font-medium`
- Negative: `text-down font-medium`
- Neutral: `text-gray-500`

### Plotly Chart
- Container: `w-full h-64 mt-4`
- Layout: transparent background, minimal margins (`t:20 r:10 b:40 l:50`), gridcolor `#E6F0FF`, font color `#142B43`
- Config: `responsive: true, displayModeBar: false`

## Placeholder Convention

Use `{{NAME}}` for all dynamic values. Agents fill based on context and user language.

Common placeholders: `{{HEADER_LEFT}}`, `{{HEADER_RIGHT}}`, `{{FOOTER}}`, `{{SECTION_TITLE}}`, `{{LABEL}}`, `{{VALUE}}`, `{{METRIC_LABEL}}`, `{{METRIC_VALUE}}`, `{{PCT_CHANGE}}`, `{{PCT_CLASS}}`, `{{CHART_ID}}`
