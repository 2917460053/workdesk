#!/usr/bin/env python3
"""
抓取实时全球新闻，生成 /workspace/news.json
使用 WebSearch + WebFetch 无法在后台脚本运行，
所以这里采用「直接抓取新闻网站 HTML/JSON 接口」的方式。
"""
import json
import re
import html
from datetime import datetime
from urllib.request import Request, urlopen

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

def fetch(url, timeout=15):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            for enc in ["utf-8", "gbk", "gb2312"]:
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="ignore")
    except Exception as e:
        return None

def strip_html(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# ---- 各新闻源抓取函数 ----

def fetch_sohu_news():
    """搜狐新闻精华摘要"""
    url = "https://www.sohu.com/a/1055110597_122014422"
    text = fetch(url)
    if not text:
        return []
    # 提取正文
    items = []
    # 用正则找文章段落
    content_match = re.search(r'id="mp-editor">(.*?)</div>\s*<div class="article"', text, re.S)
    if not content_match:
        content_match = re.search(r'<article[^>]*>(.*?)</article>', text, re.S)
    content = content_match.group(1) if content_match else text
    # 按段落拆分
    paras = re.findall(r'<p[^>]*>(.*?)</p>', content, re.S)
    for p in paras:
        clean = strip_html(p)
        if len(clean) > 15 and not clean.startswith("返回搜狐"):
            items.append(clean)
    return items[:20]

def fetch_xinhua_world():
    """新华网国际频道 - 抓取首页最新新闻"""
    url = "http://www.news.cn/world/"
    text = fetch(url)
    if not text:
        return []
    items = []
    # 提取新闻链接和标题
    matches = re.findall(r'<a[^>]*href="(/world/\d{4}-\d{2}/\d{2}/c_\d+\.htm)"[^>]*>([^<]+)</a>', text)
    seen = set()
    for link, title in matches:
        title = strip_html(title)
        if title and len(title) > 5 and title not in seen:
            seen.add(title)
            items.append({
                "title": title,
                "link": "http://www.news.cn" + link,
                "source": "新华网",
                "tag": "国际"
            })
    return items[:15]

def fetch_chinanews_intl():
    """中国新闻网国际频道"""
    url = "https://www.chinanews.com.cn/gj/"
    text = fetch(url)
    if not text:
        return []
    items = []
    matches = re.findall(r'<a[^>]*href="(https?://www\.chinanews\.com[^"]*|/\w+/\d{4}/\d{2}-\d{2}/\d+\.shtml)"[^>]*>([^<]+)</a>', text)
    seen = set()
    for link, title in matches:
        title = strip_html(title)
        if title and len(title) > 5 and title not in seen:
            seen.add(title)
            if link.startswith("/"):
                link = "https://www.chinanews.com.cn" + link
            items.append({
                "title": title,
                "link": link,
                "source": "中国新闻网",
                "tag": "国际"
            })
    return items[:15]

def fetch_huanqiu():
    """环球网国际"""
    url = "https://www.huanqiu.com/"
    text = fetch(url)
    if not text:
        return []
    items = []
    matches = re.findall(r'<a[^>]*href="(https?://\w+\.huanqiu\.com/article/[A-Za-z0-9]+)"[^>]*>([^<]+)</a>', text)
    seen = set()
    for link, title in matches:
        title = strip_html(title)
        if title and len(title) > 5 and title not in seen:
            seen.add(title)
            items.append({
                "title": title,
                "link": link,
                "source": "环球网",
                "tag": "国际"
            })
    return items[:15]

def main():
    all_news = []
    print("抓取新华网国际...")
    all_news.extend(fetch_xinhua_world())
    print("抓取中国新闻网...")
    all_news.extend(fetch_chinanews_intl())
    print("抓取环球网...")
    all_news.extend(fetch_huanqiu())

    # 去重
    seen = set()
    unique = []
    for n in all_news:
        if n["title"] not in seen:
            seen.add(n["title"])
            unique.append(n)

    out = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(unique),
        "news": unique
    }
    with open("/workspace/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已生成 news.json，共 {len(unique)} 条")
    print(f"更新时间: {out['updated']}")

if __name__ == "__main__":
    main()
