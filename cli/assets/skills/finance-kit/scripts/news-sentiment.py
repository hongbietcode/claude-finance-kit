"""News Sentiment — crawl Vietnamese financial news and output for sentiment classification.

Usage: python scripts/news-sentiment.py [TICKER] [--sites cafef,vnexpress] [--limit 20]
Output: JSON to stdout with articles (title, url, description, publish_time, source)

Note: Sentiment classification is done by Claude's reasoning, not this script.
This script handles data collection only.
"""

import argparse
import json
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="News crawler for sentiment analysis")
    parser.add_argument("ticker", nargs="?", default=None, help="Filter by ticker symbol")
    parser.add_argument("--sites", default="cafef,vnexpress", help="Comma-separated news sites")
    parser.add_argument("--limit", type=int, default=20, help="Articles per site")
    args = parser.parse_args()

    from claude_finance_kit.news import Crawler

    sites = [s.strip() for s in args.sites.split(",")]
    all_articles = []

    for site in sites:
        try:
            crawler = Crawler(site_name=site)
            articles = crawler.get_latest_articles(limit=args.limit)
            for a in articles:
                a["source"] = site
            all_articles.extend(articles)
        except Exception as e:
            all_articles.append({"source": site, "error": str(e)})

    if args.ticker:
        ticker_upper = args.ticker.upper()
        filtered = [
            a
            for a in all_articles
            if "error" in a or ticker_upper in (a.get("title", "") + " " + a.get("description", "")).upper()
        ]
        all_articles = filtered if filtered else all_articles

    result = {
        "ticker_filter": args.ticker,
        "sites": sites,
        "total_articles": len(all_articles),
        "timestamp": datetime.now().isoformat(),
        "articles": all_articles,
    }

    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
