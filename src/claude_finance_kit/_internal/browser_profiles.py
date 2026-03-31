"""Browser fingerprint profiles for anti-bot detection evasion."""

DESKTOP_BROWSERS: dict[str, dict[str, str]] = {
    "chrome": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ),
    },
    "firefox": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) "
            "Gecko/20100101 Firefox/137.0"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) "
            "Gecko/20100101 Firefox/138.0"
        ),
    },
    "edge": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.3240.50"
        ),
    },
    "opera": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 OPR/118.0.0.0"
        ),
    },
    "brave": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Brave/1.77.101"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Brave/1.77.101"
        ),
    },
    "vivaldi": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Vivaldi/7.2"
        ),
    },
    "coccoc": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 CocCoc/136.0.0.0"
        ),
    },
    "safari": {
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
        ),
    },
}

MOBILE_BROWSERS: dict[str, dict[str, str]] = {
    "chrome": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.60 Mobile Safari/537.36"
        ),
    },
    "safari": {
        "ios": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        ),
    },
    "samsung": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G991B) "
            "AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/21.0 Chrome/110.0.5481.154 Mobile Safari/537.36"
        ),
    },
    "opera": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; M2102J20SG) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 OPR/76.2.4027.73374"
        ),
    },
    "coccoc": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36 CocCocBrowser/137.0.258"
        ),
    },
    "firefox": {
        "android": "Mozilla/5.0 (Android 13; Mobile; rv:137.0) Gecko/137.0 Firefox/137.0",
    },
}

USER_AGENTS: dict[str, dict[str, str]] = {}

for _browser_dict in [DESKTOP_BROWSERS, MOBILE_BROWSERS]:
    for _browser, _platforms in _browser_dict.items():
        if _browser not in USER_AGENTS:
            USER_AGENTS[_browser] = {}
        USER_AGENTS[_browser].update(_platforms)


def list_all_profiles() -> None:
    """Print all available browser/platform combinations."""
    print("Available browser/platform combinations:")
    for browser, platforms in USER_AGENTS.items():
        for platform_name in platforms:
            print(f"- {browser:10} | {platform_name:10}")
