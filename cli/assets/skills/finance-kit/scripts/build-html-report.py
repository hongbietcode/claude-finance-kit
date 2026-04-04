"""Build HTML Report — inject Tailwind + Plotly inline for offline self-contained reports.

Usage: python scripts/build-html-report.py INPUT_HTML OUTPUT_HTML
       python scripts/build-html-report.py report.html report-offline.html

Replaces CDN <script src="..."> tags with inline <script> containing the full library.
Caches downloaded libraries in .cache/ to avoid re-downloading.
"""

import argparse
import os
import re
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

CDN_URLS = {
    "https://cdn.tailwindcss.com": "tailwindcss.js",
    "https://cdn.plot.ly/plotly-2.35.2.min.js": "plotly-2.35.2.min.js",
}


def download_and_cache(url, filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"Downloading {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Cached → {cache_path}")
    return content


def inline_scripts(html):
    for cdn_url, cache_name in CDN_URLS.items():
        pattern = rf'<script\s+src="{re.escape(cdn_url)}">\s*</script>'
        if re.search(pattern, html):
            js_content = download_and_cache(cdn_url, cache_name)
            replacement = f"<script>{js_content}</script>"
            html = re.sub(pattern, replacement, html)
            print(f"Inlined {cache_name} ({len(js_content):,} chars)")
    return html


def main():
    parser = argparse.ArgumentParser(description="Inline CDN scripts into HTML report")
    parser.add_argument("input", help="Input HTML file path")
    parser.add_argument("output", nargs="?", help="Output HTML file path (default: overwrite input)")
    args = parser.parse_args()

    output = args.output or args.input

    with open(args.input, "r", encoding="utf-8") as f:
        html = f.read()

    html = inline_scripts(html)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Done → {output} ({os.path.getsize(output):,} bytes)")


if __name__ == "__main__":
    main()
