"""Site configurations for Vietnamese financial news crawlers."""

DEFAULT_RSS_MAPPING = {
    "link": "link",
    "title": "title",
    "description": "description",
    "publish_time": "pubDate",
}

SITES_CONFIG = {
    "cafef": {
        "sitemap_url": "https://cafef.vn/latest-news-sitemap.xml",
        "config": {
            "title_selector": {"class": "title"},
            "content_selector": {"tag": "div", "class": "contentdetail"},
            "short_desc_selector": {"class": "sapo"},
            "publish_time_selector": {"class": "pdate"},
            "author_selector": {"class": "author"},
        },
    },
    "cafebiz": {
        "sitemap_url": "https://cafebiz.vn/latestnews-sitemap.xml",
        "config": {
            "title_selector": {"class": "title"},
            "content_selector": {"tag": "div", "class": "detail-content"},
            "short_desc_selector": {"class": "sapo"},
            "publish_time_selector": {"class": "time"},
            "author_selector": {"class": "detail-author"},
        },
        "rss": {
            "urls": [
                "https://cafebiz.vn/rss/home.rss",
                "https://cafebiz.vn/rss/cau-chuyen-kinh-doanh.rss",
                "https://cafebiz.vn/rss/vi-mo.rss",
                "https://cafebiz.vn/rss/cong-nghe.rss",
                "https://cafebiz.vn/rss/xa-hoi.rss",
            ],
            "mapping": DEFAULT_RSS_MAPPING,
        },
    },
    "vietstock": {
        "sitemap_url": "https://vietstock.vn/sitemap.xml",
        "config": {
            "title_selector": {"class": "article-title"},
            "content_selector": {"tag": "div", "class": "single_post_heading"},
            "short_desc_selector": {"class": "pHead"},
            "publish_time_selector": {"class": "date"},
            "author_selector": {"class": "pAuthor"},
        },
        "rss": {
            "urls": [
                "https://vietstock.vn/761/kinh-te/vi-mo.rss",
                "https://vietstock.vn/768/kinh-te/kinh-te-dau-tu.rss",
                "https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss",
                "https://vietstock.vn/4309/the-gioi/tien-ky-thuat-so.rss",
                "https://vietstock.vn/772/the-gioi/tai-chinh-quoc-te.rss",
                "https://vietstock.vn/775/the-gioi/kinh-te-nganh.rss",
            ],
            "mapping": DEFAULT_RSS_MAPPING,
        },
    },
    "vneconomy": {
        "sitemap_url": "https://vneconomy.vn/sitemap/latest-news.xml",
        "config": {
            "title_selector": {"tag": "h2", "class": "name-detail"},
            "content_selector": {"tag": "div", "class": "ct-edtior-web news-type1"},
            "short_desc_selector": {"tag": "div", "class": "news-sapo"},
            "publish_time_selector": {"tag": "p", "class": "date"},
            "author_selector": {"tag": "p", "class": "name"},
        },
    },
    "plo": {
        "sitemap": {
            "base_url": "https://plo.vn/sitemaps/news-",
            "pattern_type": "monthly",
            "format": "{year}-{month}",
            "extension": "xml",
            "current_url": "https://plo.vn/sitemaps/news-2025-8.xml",
        },
        "config": {
            "title_selector": {"class": "article__title"},
            "content_selector": {"tag": "div", "class": "article__body"},
            "short_desc_selector": {"class": "article__sapo"},
            "publish_time_selector": {"class": "time"},
            "author_selector": {"class": "author"},
        },
    },
    "vnexpress": {
        "config": {
            "title_selector": {"tag": "h1", "class": "title-detail"},
            "content_selector": {"tag": "article", "class": "fck_detail"},
            "short_desc_selector": {"tag": "p", "class": "description"},
            "publish_time_selector": {"tag": "span", "class": "date"},
            "author_selector": {"tag": "strong"},
        },
        "rss": {
            "urls": ["https://vnexpress.net/rss/tin-moi-nhat.rss"],
            "mapping": DEFAULT_RSS_MAPPING,
        },
    },
    "tuoitre": {
        "sitemap": {
            "base_url": "https://tuoitre.vn/StaticSitemaps/sitemaps-",
            "pattern_type": "monthly",
            "format": "{year}-{month}",
            "extension": "xml",
            "current_url": "https://tuoitre.vn/StaticSitemaps/sitemaps-2025-8.xml",
        },
        "config": {
            "title_selector": {"tag": "h1", "class": "detail-title"},
            "content_selector": {"tag": "div", "class": "detail-cmain"},
            "short_desc_selector": {"tag": "h2", "class": "detail-sapo"},
            "publish_time_selector": {"tag": "div", "class": "detail-time"},
            "author_selector": {"tag": "a", "class": "author-info"},
        },
        "rss": {
            "urls": [
                "https://tuoitre.vn/rss/tin-moi-nhat.rss",
                "https://tuoitre.vn/rss/the-gioi.rss",
                "https://tuoitre.vn/rss/kinh-doanh.rss",
                "https://tuoitre.vn/rss/thoi-su.rss",
                "https://tuoitre.vn/rss/phap-luat.rss",
                "https://tuoitre.vn/rss/nhip-song-so.rss",
            ],
            "mapping": DEFAULT_RSS_MAPPING,
        },
    },
    "ktsg": {
        "sitemap": {
            "base_url": "https://thesaigontimes.vn/post-sitemap",
            "pattern_type": "incremental",
            "index_url": "https://thesaigontimes.vn/sitemap_index.xml",
            "extension": "xml",
            "current_url": "https://thesaigontimes.vn/post-sitemap156.xml",
        },
        "config": {
            "title_selector": {"class": "tdb-title-text"},
            "content_selector": {"tag": "div", "class": "td-post-content"},
            "short_desc_selector": {"tag": "p"},
            "publish_time_selector": {"class": "entry-date updated td-module-date"},
            "author_selector": {"class": "wpb_wrapper td_block_wrap td_block_creative content-tacgia"},
        },
    },
    "ncdt": {
        "sitemap_url": "https://nhipcaudautu.vn/sitemap.xml",
        "config": {
            "title_selector": {"tag": "h1", "class": "post-detail-title"},
            "content_selector": {"tag": "div", "class": "content-detail"},
            "short_desc_selector": {"tag": "div", "class": "des-small"},
            "publish_time_selector": {"tag": "span", "class": "date-post"},
            "author_selector": {"tag": "span", "class": "user-post"},
        },
    },
    "dddn": {
        "sitemap_url": "https://diendandoanhnghiep.vn/sitemap-news.xml",
        "config": {
            "title_selector": {"class": "sc-longform-header-title"},
            "content_selector": {"tag": "div", "class": "b-maincontent"},
            "short_desc_selector": {"class": "sc-longform-header-sapo"},
            "publish_time_selector": {"class": "sc-longform-header-date"},
            "author_selector": {"class": "sc-longform-header-author"},
        },
    },
    "baodautu": {
        "sitemap": {
            "base_url": "https://baodautu.vn/sitemaps/news-",
            "pattern_type": "monthly",
            "format": "{year}-{month}",
            "extension": "xml",
            "current_url": "https://baodautu.vn/sitemaps/news-2025-8.xml",
        },
        "config": {
            "title_selector": {"tag": "h1", "class": "title-detail"},
            "content_selector": {"tag": "div", "id": "content_detail_news"},
            "short_desc_selector": {"tag": "div", "class": "sapo_detail"},
            "publish_time_selector": {"tag": "span", "class": "post-time"},
            "author_selector": {"tag": "a", "class": "author"},
        },
    },
    "congthuong": {
        "sitemap_url": "https://congthuong.vn/sitemap.xml",
        "config": {
            "title_selector": {"tag": "h1", "class": "detail-title"},
            "content_selector": {"tag": "div", "class": "detail-content"},
            "short_desc_selector": {"tag": "div", "class": "detail-sapo"},
            "publish_time_selector": {"tag": "span", "class": "time"},
            "author_selector": {"tag": "span", "class": "author"},
        },
        "rss": {
            "urls": [
                "https://congthuong.vn/rss/tin-moi-nhat.rss",
                "https://congthuong.vn/rss/tai-chinh.rss",
                "https://congthuong.vn/rss/kinh-doanh.rss",
            ],
            "mapping": DEFAULT_RSS_MAPPING,
        },
    },
}

SUPPORTED_SITES = list(SITES_CONFIG.keys())
