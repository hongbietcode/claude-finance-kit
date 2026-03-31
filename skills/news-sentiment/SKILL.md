---
name: news-sentiment
description: Vietnamese financial news crawling + sentiment analysis. Activate for market news, financial news, news sentiment, latest stock news, or recent events affecting Vietnamese stocks. Single-agent by default — multi-agent degrades sentiment quality.
---

# News & Sentiment Research

> **Install:** `claude-finance-kit` must be installed — see [`references/claude-finance-kit-install-guide.md`](../../references/claude-finance-kit-install-guide.md) for setup command.

Default: single agent (T1). Research shows sentiment analysis quality drops from 3.93 → 3.77 with multi-agent debate.

## Workflow Router

| Trigger                                    | Tier | Structure                                 |
| ------------------------------------------ | ---- | ----------------------------------------- |
| "headlines from cafef", specific site      | T1   | Single crawler inline                     |
| "news about FPT", ticker/sector sentiment  | T1   | Single agent: crawl + classify            |
| "comprehensive news analysis", all sectors | T2   | Parallel crawl by site, single classifier |

## Data Collection

> **Code patterns:** See [`references/api-news-and-collector.md`](../../references/api-news-and-collector.md) for Crawler & BatchCrawler APIs.
> **Error handling:** See [`references/common-patterns.md`](../../references/common-patterns.md).

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
> **HTML reports:** Follow styles and layout in [`references/html-report-styles.md`](../../references/html-report-styles.md).

Dàn ý báo cáo tin tức & cảm xúc đạt yêu cầu (5 sections):

1. **Cảm xúc tổng quan** — Số bài tích cực / trung lập / tiêu cực (con số + %), pill cảm xúc thị trường tổng thể; biểu đồ cột net score theo mã (tích cực = xanh, tiêu cực = đỏ)
2. **Tin tiêu điểm** — 5–10 bài nổi bật, mỗi bài: tiêu đề, nguồn, thời gian, mã liên quan, màu border trái theo cảm xúc (xanh = tích cực, đỏ = tiêu cực, xám = trung lập)
3. **Cảm xúc theo mã CP** — Bảng: mã | số bài tích cực | số bài tiêu cực | điểm net | nhãn (Tích cực / Trung lập / Tiêu cực); sắp xếp theo điểm net giảm dần
4. **Chủ đề nổi bật** — 3 chủ đề chính: loại sự kiện, số bài, tóm tắt 1 câu, danh sách mã liên quan
5. **Sự kiện đáng chú ý** — Corporate actions, chính sách, kết quả kinh doanh; mỗi sự kiện: nhãn loại (KQKD / M&A / CSTT / VĨ MÔ / ...) + tiêu đề + mô tả tác động ngắn

**Required data per section:**

- S1–S5: crawl 10–50 bài từ cafef/vietstock/vnexpress → classify sentiment per article → aggregate
- Classify each article: sentiment (bullish/bearish/neutral), confidence (0–1), event_type, tickers_mentioned
- Aggregate: net_score[ticker] = bullish_count - bearish_count
- **Disclaimer** (footer): "Báo cáo chỉ mang tính tham khảo, không phải khuyến nghị đầu tư. Nhà đầu tư tự chịu trách nhiệm về quyết định của mình."

## Reference Index

⚠️ **READ THESE WHEN:** You need detailed crawler API reference or routing logic beyond what SKILL.md provides.

| File                                                                                     | Content                                                              |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| [`references/claude-finance-kit-install-guide.md`](../../references/claude-finance-kit-install-guide.md) | Installation instructions, requirements, environment variables       |
| [`references/common-patterns.md`](../../references/common-patterns.md)                   | Common coding patterns for news crawling, error handling             |
| [`references/api-news-and-collector.md`](../../references/api-news-and-collector.md)     | Detailed crawler API reference                                       |
| [`references/orchestration-protocol.md`](../../references/orchestration-protocol.md)     | Complexity routing rules                                             |
| [`references/html-report-styles.md`](../../references/html-report-styles.md)             | HTML report design system: Tailwind config, components, placeholders |
