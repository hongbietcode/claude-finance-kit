---
name: news-sentiment
description: Vietnamese financial news crawling + sentiment analysis. Activate for market news, financial news, news sentiment, latest stock news, or recent events affecting Vietnamese stocks. Single-agent by default — multi-agent degrades sentiment quality.
---

# News & Sentiment Research

> **Install:** `claude-finance-kit` must be installed — see [`references/finance-kit-install-guide.md`](./references/finance-kit-install-guide.md) for setup command.

Default: single agent (T1). Research shows sentiment analysis quality drops from 3.93 → 3.77 with multi-agent debate.

## Operating Principles

- **Data-First:** thesis → data → reasoning → conclusion. State assumptions when data unavailable. Never hallucinate.
- **No Bias:** If risk > reward, recommend staying out. If setup unclear, say "No trade setup".
- **Concise & Actionable:** Bullet points and data tables over paragraphs.
- **Real-Time Data Only:** Market indices MUST be fetched live — never fabricated. Flag if delayed/unavailable.
- **Context-Aware:** Tailor analysis depth and style to user's timeframe and experience level. Always clarify if ambiguous.

## Workflow Router

| Trigger                                    | Tier | Structure                                 |
| ------------------------------------------ | ---- | ----------------------------------------- |
| "headlines from cafef", specific site      | T1   | Single crawler inline                     |
| "news about FPT", ticker/sector sentiment  | T1   | Single agent: crawl + classify            |
| "comprehensive news analysis", all sectors | T2   | Parallel crawl by site, single classifier |

## Data Collection

> **Code patterns:** See [`references/api-news-and-collector.md`](./references/api-news-and-collector.md) for Crawler & BatchCrawler APIs.
> **Error handling:** See [`references/common-patterns.md`](./references/common-patterns.md).

Use `Crawler(site_name)` for single-site crawling, `BatchCrawler(site_name, request_delay)` for large batches.

## Available Sites

cafef, cafebiz, vietstock, vneconomy, plo, vnexpress, tuoitre, ktsg, ncdt, dddn, baodautu, congthuong

## Sentiment Classification

For each article, classify:

- **Sentiment:** bullish / bearish / neutral
- **Event type:** earnings, M&A, regulatory, macro, sector
- **Confidence:** 0.0 - 1.0
- **Tickers mentioned:** extract stock symbols

Aggregate per-ticker: net score = bullish_count - bearish_count

## Report Structure

> **IMPORTANT:** Always write the report in the user's language (Vietnamese if user writes in Vietnamese, English if user writes in English).
> **MANDATORY:** Every analysis MUST produce a self-contained HTML report file. Follow styles and layout in [`references/html-report-styles.md`](./references/html-report-styles.md).

Strictly follow 7 sections:

1. **Bối cảnh thị trường** — VNINDEX (điểm, % ngày), P/E zone, macro headline (lãi suất, tỷ giá) — bối cảnh ngắn gọn để đặt tin tức vào context
2. **Cảm xúc tổng quan** — Số bài tích cực / trung lập / tiêu cực (con số + %), pill cảm xúc thị trường tổng thể; Plotly bar chart net score theo mã (xanh = tích cực, đỏ = tiêu cực)
3. **Tin tiêu điểm** — 5–10 bài nổi bật, mỗi bài: tiêu đề, nguồn, thời gian, mã liên quan, màu border trái theo cảm xúc (xanh = tích cực, đỏ = tiêu cực, xám = trung lập)
4. **Cảm xúc theo mã CP** — Bảng: mã | số bài tích cực | số bài tiêu cực | điểm net | nhãn (Tích cực / Trung lập / Tiêu cực); sắp xếp theo điểm net giảm dần
5. **Chủ đề nổi bật** — 3 chủ đề chính: loại sự kiện, số bài, tóm tắt 1 câu, danh sách mã liên quan
6. **Sự kiện đáng chú ý** — Corporate actions, chính sách, kết quả kinh doanh; mỗi sự kiện: nhãn loại (KQKD / M&A / CSTT / VĨ MÔ / ...) + tiêu đề + mô tả tác động ngắn
7. **Disclaimer** — "Báo cáo chỉ mang tính tham khảo, không phải khuyến nghị đầu tư. Nhà đầu tư tự chịu trách nhiệm về quyết định của mình."

**Required data per section:**

- S1: `Market("VNINDEX").pe()`, `Macro().interest_rate()`, `Macro().exchange_rate()` — brief snapshot
- S2–S6: crawl 10–50 bài từ cafef/vietstock/vnexpress → classify sentiment per article → aggregate
- Classify each article: sentiment (bullish/bearish/neutral), confidence (0–1), event_type, tickers_mentioned
- Aggregate: net_score[ticker] = bullish_count - bearish_count

### HTML Output Rules

1. **Format:** Self-contained HTML file — Tailwind CDN + Plotly.js CDN, no external dependencies
2. **Save path:** `{CWD}/plans/reports/{slug}-report.html` (e.g., `news-sentiment-fpt-2026-04-01-report.html`, `news-sentiment-market-2026-04-01-report.html`)
3. **Open:** After writing the file, run `open {file_path}` to auto-open in browser
4. **Charts:** Plotly.js with data embedded as inline JS variables
5. **Deliver in chat:** summary + file path link

## Reference Index

⚠️ **READ THESE WHEN:** You need detailed crawler API reference or routing logic beyond what SKILL.md provides.

| File                                                                                   | Content                                                              |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| [`references/finance-kit-install-guide.md`](./references/finance-kit-install-guide.md) | Installation instructions, requirements, environment variables       |
| [`references/common-patterns.md`](./references/common-patterns.md)                     | Common coding patterns for news crawling, error handling             |
| [`references/api-news-and-collector.md`](./references/api-news-and-collector.md)       | Detailed crawler API reference                                       |
| [`references/orchestration-protocol.md`](./references/orchestration-protocol.md)       | Complexity routing rules                                             |
| [`references/html-report-styles.md`](./references/html-report-styles.md)               | HTML report design system: Tailwind config, components, placeholders |
