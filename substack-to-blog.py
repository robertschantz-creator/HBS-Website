#!/usr/bin/env python3
"""
Substack → HBS Blog Post Generator
------------------------------------
Pulls the latest post from timingcodehbs.substack.com and generates
a ready-to-publish HTML file in the blog/ folder.

Usage:
  python3 substack-to-blog.py

Options:
  python3 substack-to-blog.py --all        # Generate files for all recent posts
  python3 substack-to-blog.py --list       # List recent posts without generating
"""

import sys
import re
import html
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

SUBSTACK_RSS   = "https://timingcodehbs.substack.com/feed"
BLOG_DIR       = Path(__file__).parent / "blog"
SITE_BASE_URL  = "https://humanbehaviorspecialists.com"
AUTHOR_NAME    = "Robert Schantz"
AUTHOR_URL     = f"{SITE_BASE_URL}/about.html"

# ── Categories mapped from Substack tags (edit as needed) ──────────────────
TAG_MAP = {
    "career":        "Career",
    "finances":      "Finances",
    "finance":       "Finances",
    "money":         "Finances",
    "relationships": "Relationships",
    "relationship":  "Relationships",
    "health":        "Health & Well-being",
    "well-being":    "Health & Well-being",
    "wellbeing":     "Health & Well-being",
    "where to live": "Where to Live",
    "move":          "Where to Live",
    "location":      "Where to Live",
    "timing":        "Timing & Cycles",
    "cycles":        "Timing & Cycles",
    "numerology":    "Timing & Cycles",
    "personal year": "Timing & Cycles",
}


def slug_from_title(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s[:80]


def estimate_read_time(text: str) -> str:
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"


def strip_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", " ", raw).strip()


def fetch_rss() -> list[dict]:
    print(f"Fetching {SUBSTACK_RSS} ...")
    req = urllib.request.Request(
        SUBSTACK_RSS,
        headers={"User-Agent": "Mozilla/5.0 (HBS blog importer)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    ns = {"content": "http://purl.org/rss/1.0/modules/content/",
          "dc": "http://purl.org/dc/elements/1.1/"}
    posts = []
    for item in root.findall(".//item"):
        title   = (item.findtext("title") or "").strip()
        link    = (item.findtext("link") or "").strip()
        pubdate = (item.findtext("pubDate") or "").strip()
        desc    = (item.findtext("description") or "").strip()
        content = (item.findtext("content:encoded", namespaces=ns) or desc).strip()
        tags    = [c.text.lower().strip() for c in item.findall("category") if c.text]

        # Resolve category
        category = "Timing & Cycles"
        for tag in tags:
            if tag in TAG_MAP:
                category = TAG_MAP[tag]
                break

        # Parse date
        try:
            dt = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")
            date_display = dt.strftime("%B %Y")
            date_iso     = dt.strftime("%Y-%m-%d")
        except Exception:
            date_display = datetime.now().strftime("%B %Y")
            date_iso     = datetime.now().strftime("%Y-%m-%d")

        plain_text = strip_html(content)
        posts.append({
            "title":        html.unescape(title),
            "link":         link,
            "date_display": date_display,
            "date_iso":     date_iso,
            "category":     category,
            "content_html": content,
            "plain_text":   plain_text,
            "read_time":    estimate_read_time(plain_text),
            "slug":         slug_from_title(title),
        })
    return posts


def content_to_hbs_html(raw_html: str) -> str:
    """
    Converts raw Substack HTML into HBS post-content styled HTML.
    Wraps bare <p> tags, converts <h2>/<h3>, preserves lists.
    Strips Substack subscription footers.
    """
    # Remove Substack boilerplate subscription CTAs
    raw_html = re.sub(
        r'<div[^>]*class="[^"]*subscribe[^"]*"[^>]*>.*?</div>',
        "", raw_html, flags=re.DOTALL | re.IGNORECASE
    )
    raw_html = re.sub(
        r'<p[^>]*>.*?Subscribe.*?</p>', "", raw_html,
        flags=re.DOTALL | re.IGNORECASE
    )
    # Normalise heading levels (Substack uses h2/h3 already — just keep them)
    # Wrap blockquotes as callouts
    raw_html = re.sub(
        r"<blockquote>(.*?)</blockquote>",
        r'<div class="post-callout"><p>\1</p></div>',
        raw_html, flags=re.DOTALL
    )
    return raw_html.strip()


def generate_html(post: dict) -> str:
    slug        = post["slug"]
    title       = html.escape(post["title"])
    category    = post["category"]
    date_display= post["date_display"]
    date_iso    = post["date_iso"]
    read_time   = post["read_time"]
    content     = content_to_hbs_html(post["content_html"])
    substack_url= post["link"]
    canonical   = f"{SITE_BASE_URL}/blog/{slug}.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | HBS</title>
  <meta name="description" content="{html.escape(post['plain_text'][:155])}..." />
  <link rel="canonical" href="{canonical}" />
  <link rel="stylesheet" href="../css/style.css" />
  <style>
    .post-hero{{padding:140px 0 72px;background:linear-gradient(135deg,var(--violet-dark) 0%,var(--violet) 100%);color:var(--white);}}
    .post-hero .eyebrow{{color:var(--gold-light);}}
    .post-hero h1{{color:var(--white);font-weight:300;font-size:clamp(1.8rem,3.5vw,2.8rem);line-height:1.25;max-width:760px;margin-bottom:20px;}}
    .post-hero__meta{{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-top:24px;}}
    .post-hero__meta span{{font-size:0.82rem;color:rgba(255,255,255,0.6);}}
    .post-hero__meta .post-cat{{font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--gold);background:rgba(201,168,76,0.15);padding:4px 12px;border-radius:20px;}}
    .post-body{{background:var(--dark-bg);padding:80px 0 64px;}}
    .post-layout{{display:grid;grid-template-columns:1fr 320px;gap:72px;align-items:start;}}
    .post-content{{max-width:680px;}}
    .post-content p{{font-size:0.97rem;color:var(--charcoal-soft);line-height:1.9;margin-bottom:24px;}}
    .post-content h2{{font-size:1.4rem;color:var(--on-dark);margin:48px 0 16px;font-weight:500;}}
    .post-content h3{{font-size:1.1rem;color:var(--on-dark);margin:32px 0 12px;font-family:var(--font-serif);font-weight:500;}}
    .post-content ul,.post-content ol{{padding-left:24px;margin-bottom:24px;}}
    .post-content li{{font-size:0.95rem;color:var(--charcoal-soft);line-height:1.8;margin-bottom:8px;}}
    .post-content strong{{color:var(--on-dark);}}
    .post-content a{{color:var(--gold);}}
    .post-callout{{background:var(--dark-card);border-left:3px solid var(--gold);border-radius:0 4px 4px 0;padding:24px 28px;margin:32px 0;}}
    .post-callout p{{margin:0;font-style:italic;color:var(--charcoal);}}
    .post-sidebar{{position:sticky;top:100px;}}
    .sidebar-card{{background:var(--dark-card);border:1px solid var(--border);border-radius:6px;padding:28px;margin-bottom:24px;}}
    .sidebar-card .eyebrow{{margin-bottom:12px;display:block;}}
    .sidebar-card h4{{font-size:1rem;color:var(--on-dark);margin-bottom:10px;}}
    .sidebar-card p{{font-size:0.85rem;color:var(--charcoal-soft);line-height:1.7;margin-bottom:20px;}}
    .post-footer-nav{{background:var(--dark-card);border-top:1px solid var(--border);padding:48px 0;}}
    .post-footer-nav__inner{{display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap;}}
    @media (max-width:960px){{.post-layout{{grid-template-columns:1fr;}}.post-sidebar{{position:static;}}}}
  </style>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "description": "{html.escape(post['plain_text'][:155])}",
    "author": {{"@type":"Person","name":"{AUTHOR_NAME}","url":"{AUTHOR_URL}"}},
    "publisher": {{"@type":"Organization","name":"Human Behavior Specialists","url":"{SITE_BASE_URL}"}},
    "datePublished": "{date_iso}",
    "mainEntityOfPage": "{canonical}"
  }}
  </script>
</head>
<body>
  <a href="#main-content" class="skip-nav">Skip to main content</a>
  <nav class="nav" role="navigation">
    <div class="nav__inner">
      <a href="../index.html" class="nav__logo">
        <img src="../images/hbs-logo.svg" width="40" height="40" alt="" aria-hidden="true" />
        <div class="nav__logo-text">
          <span class="nav__logo-name">Human Behavior Specialists</span>
          <span class="nav__logo-tag">Guidance for Career, Relationships &amp; Where to Live</span>
        </div>
      </a>
      <ul class="nav__links">
        <li><a href="../the-work.html">The Work</a></li>
        <li><a href="../ways-to-work.html">Work Together</a></li>
        <li><a href="../personal-forecast.html">Personal Forecast</a></li>
        <li><a href="../about.html">About</a></li>
        <li><a href="../blog.html">Blog</a></li>
        <li><a href="../begin.html">Contact</a></li>
      </ul>
      <a href="../begin.html" class="btn btn-primary nav__cta">Begin</a>
      <button class="nav__toggle" aria-label="Toggle menu"><span></span><span></span><span></span></button>
    </div>
  </nav>

  <main id="main-content">
    <header class="post-hero">
      <div class="container">
        <a href="../blog.html" style="font-size:0.78rem;color:rgba(255,255,255,0.5);text-decoration:none;letter-spacing:0.04em;display:inline-block;margin-bottom:20px;">← Back to Blog</a>
        <span class="eyebrow">{html.escape(category)}</span>
        <h1>{title}</h1>
        <div class="post-hero__meta">
          <span class="post-cat">{html.escape(category)}</span>
          <span>{AUTHOR_NAME}</span>
          <span>{date_display}</span>
          <span>{read_time}</span>
        </div>
      </div>
    </header>

    <section class="post-body">
      <div class="container">
        <div class="post-layout">
          <article class="post-content">
            {content}

            <!-- CTA -->
            <div style="margin-top:40px;padding:32px;background:var(--dark-card);border:1px solid var(--border);border-radius:6px;text-align:center;">
              <span class="eyebrow" style="display:block;margin-bottom:12px;">Know Your Phase</span>
              <h3 style="font-family:var(--font-serif);font-size:1.4rem;color:var(--on-dark);margin-bottom:12px;font-weight:400;">Get Your Personal Year Timing Report</h3>
              <p style="font-size:0.88rem;color:var(--charcoal-soft);max-width:440px;margin:0 auto 24px;line-height:1.75;">An 18–22 page personalized PDF covering your current cycle and what it means for the decisions you're facing right now.</p>
              <a href="../report.html" class="btn btn-gold">Get the Report — $47</a>
            </div>
          </article>

          <aside class="post-sidebar">
            <div class="sidebar-card">
              <span class="eyebrow">Also on Substack</span>
              <h4>Get These in Your Inbox</h4>
              <p>Subscribe to The Timing Code on Substack to get every article delivered directly to you.</p>
              <a href="https://timingcodehbs.substack.com" class="btn btn-outline" style="width:100%;text-align:center;display:block;" target="_blank" rel="noopener">Follow on Substack</a>
            </div>
            <div class="sidebar-card">
              <span class="eyebrow">Related</span>
              <h4>Get Your Personal Year Report</h4>
              <p>An 18–22 page PDF personalized to your specific numbers and the year you're currently in.</p>
              <a href="../report.html" class="btn btn-gold" style="width:100%;text-align:center;display:block;">$47 — Get the Report</a>
            </div>
            <div class="sidebar-card">
              <h4>Work With Robert Directly</h4>
              <p>A one-on-one Personal Forecast Session covers your full blueprint, your current cycle, and how it applies to the decisions you're actually facing.</p>
              <a href="../personal-forecast.html" class="btn btn-outline" style="width:100%;text-align:center;display:block;">See the Session</a>
            </div>
          </aside>
        </div>
      </div>
    </section>

    <div class="post-footer-nav">
      <div class="container">
        <div class="post-footer-nav__inner">
          <a href="../blog.html" class="btn btn-outline">← All Articles</a>
          <div style="text-align:right;">
            <span style="display:block;font-size:0.72rem;color:var(--charcoal-soft);letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">Originally on Substack</span>
            <a href="{substack_url}" style="font-size:0.88rem;color:var(--gold);" target="_blank" rel="noopener">Read on Substack →</a>
          </div>
        </div>
      </div>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer__grid">
        <div>
          <div class="footer__brand-logo">
            <img src="../images/hbs-logo.svg" width="32" height="32" alt="" aria-hidden="true" />
            <div>
              <span class="footer__brand-name">Human Behavior Specialists</span>
              <span class="footer__brand-tag">Guidance for Career, Relationships &amp; Where to Live</span>
            </div>
          </div>
          <p class="footer__desc">A pattern-based advisory practice focused on life transitions, decision timing, and sustainable direction.</p>
        </div>
        <div class="footer__col">
          <h5>Navigate</h5>
          <ul class="footer__links">
            <li><a href="../the-work.html">The Work</a></li>
            <li><a href="../ways-to-work.html">Work Together</a></li>
            <li><a href="../about.html">About</a></li>
            <li><a href="../blog.html">Blog</a></li>
            <li><a href="../begin.html">Contact</a></li>
          </ul>
        </div>
        <div class="footer__col">
          <h5>Reports</h5>
          <ul class="footer__links">
            <li><a href="../report.html">Personal Year Timing — $47</a></li>
            <li><a href="../full-numerology-report.html">Full Numerology Report — $67</a></li>
            <li><a href="../address-report.html">Address &amp; Location Report — $19.95</a></li>
          </ul>
        </div>
      </div>
      <div class="footer__bottom">
        <p>&copy; 2026 Human Behavior Specialists. Advisory and educational in nature. Not therapy, medical, legal, or financial advice.</p>
      </div>
    </div>
  </footer>
  <script src="../js/main.js"></script>
</body>
</html>"""


def add_to_blog_index(post: dict, out_path: Path) -> None:
    """Prints a blog index card snippet to copy into blog.html."""
    slug     = post["slug"]
    title    = html.escape(post["title"])
    category = html.escape(post["category"])
    date     = post["date_display"]
    plain    = post["plain_text"]
    excerpt  = html.escape(" ".join(plain.split()[:30])) + "..."

    print("\n" + "─"*60)
    print("ADD THIS CARD TO blog.html (inside .post-grid):\n")
    print(textwrap.dedent(f"""\
          <article class="post-card fade-in">
            <div class="post-card__top">
              <span class="post-cat">{category}</span>
            </div>
            <div class="post-card__body">
              <div class="post-meta">
                <span class="post-date">{date}</span>
                <span class="post-read">{post['read_time']}</span>
              </div>
              <h3>{title}</h3>
              <p>{excerpt}</p>
              <a href="blog/{slug}.html" class="post-read-link">Read Article →</a>
            </div>
          </article>"""))
    print("─"*60)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--latest"
    posts = fetch_rss()

    if not posts:
        print("No posts found in RSS feed.")
        return

    if mode == "--list":
        print(f"\nFound {len(posts)} posts:\n")
        for i, p in enumerate(posts):
            print(f"  {i+1}. [{p['category']}] {p['title']} ({p['date_display']})")
        return

    targets = posts if mode == "--all" else [posts[0]]

    BLOG_DIR.mkdir(exist_ok=True)
    for post in targets:
        slug     = post["slug"]
        out_path = BLOG_DIR / f"{slug}.html"

        if out_path.exists():
            print(f"⚠️  {out_path.name} already exists — skipping (delete to regenerate)")
            continue

        html_out = generate_html(post)
        out_path.write_text(html_out, encoding="utf-8")
        print(f"✅  Generated: blog/{slug}.html")
        print(f"    Title:     {post['title']}")
        print(f"    Category:  {post['category']}")
        print(f"    Date:      {post['date_display']}")
        add_to_blog_index(post, out_path)

    print("\nDone. Drop the generated file(s) in the blog/ folder and add the card snippet to blog.html.")


if __name__ == "__main__":
    main()
