#!/usr/bin/env python3
"""
Tooltech Technologies - static site builder.

GitHub Pages cannot run PHP, so this script writes the finished .html files.
Run it again whenever you change a product, write a blog post, or edit a page in src/:

    python3 build.py

Needs only Python 3 (no extra packages). Then commit and push the files to GitHub.
"""
import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- SETTINGS
CFG = {
    "contact_email": "tooltechtechnologies@gmail.com",
    "whatsapp": "256789570235",
    "phone": "+256789570235",
    "place": "Matugga",
    "posts_per_page": 6,
}

CATEGORIES = {
    "otg": "OTG adapters",
    "memory": "Memory cards",
    "flash": "Flash disks",
    "cable": "Cables",
    "audio": "Audio",
}

# key: (min, max or None for no limit, label)
RANGES = {
    "all": (0, None, "Any price"),
    "u5": (0, 4999, "Under UGX 5,000"),
    "r5": (5000, 9999, "UGX 5,000 to 9,999"),
    "r10": (10000, 14999, "UGX 10,000 to 14,999"),
    "o15": (15000, None, "UGX 15,000 and above"),
}

# To add or change a product, edit this list and run build.py again.
#   offer=True    -> "Offer of the Day" badge
#   coming=True   -> "Coming soon", cannot be added to the cart
#   featured=True -> shown on the home page
PRODUCTS = [
    dict(id="tt-01", name="OTG Type C", price=2000, category="otg", image="img/otg.jpg", description="Remax USB 2.0 Type C", offer=True),
    dict(id="tt-02", name="OTG Micro USB", price=2000, category="otg", image="img/otg.jpg", description="Remax USB 2.0 Micro USB", offer=True),
    dict(id="tt-03", name="Memory Card 2GB", price=10000, category="memory", image="img/memory-card-2GB.jpg", description="Boost High Speed", coming=True),
    dict(id="tt-04", name="Memory Card 4GB", price=15000, category="memory", image="img/memory-card-4GB.jpg", description="Boost High Speed", coming=True),
    dict(id="tt-05", name="Memory Card 8GB", price=18000, category="memory", image="img/memory-card-8GB.jpg", description="Boost High Speed"),
    dict(id="tt-06", name="Flash Disk 4GB", price=13500, category="flash", image="img/flash-disk-4GB.jpg", description="Sandisk Ultra Luxe", featured=True),
    dict(id="tt-07", name="Flash Disk 8GB", price=15000, category="flash", image="img/flash-disk-8GB.jpg", description="Sandisk Cruzer Blade"),
    dict(id="tt-08", name="Lightning Cable", price=7000, category="cable", image="img/iphone-cable.jpg", description="Lightning To USB", featured=True),
    dict(id="tt-09", name="Type C Cable", price=12000, category="cable", image="img/type-c.webp", description="Oraimo Ultra Durable", featured=True),
    dict(id="tt-010", name="Micro USB Cable", price=6000, category="cable", image="img/usb-micro-usb.jpg", description="Oraimo Ultra Durable"),
    dict(id="tt-011", name="Oraimo Earphones", price=10000, category="audio", image="img/oraimo-earphones.jpg", description="Deep Bass With Mic", featured=True),
]

# ---------------------------------------------------------------- HELPERS
def e(value):
    """HTML-escape everything that is printed into a page."""
    return html.escape(str(value), quote=True)


def money(n):
    return "UGX {:,}".format(int(n))


def wa_link(text=""):
    base = "https://wa.me/" + CFG["whatsapp"]
    if not text:
        return base
    from urllib.parse import quote
    return base + "?text=" + quote(text, safe="")


def product_url(p):
    return "product-%s.html" % p["id"]


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(name, content):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        f.write(content)


# Security policy for every page. GitHub Pages cannot send HTTP headers, so it is set
# with a <meta> tag. Only this site's own scripts can run.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data:",
    "frame-src https://www.google.com",
    "connect-src 'self' https://formspree.io",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self' https://formspree.io",
])

# ---------------------------------------------------------------- MARKDOWN (safe)
def md_inline(raw):
    """Everything is escaped FIRST; only then are our own tags added."""
    escaped = e(raw)
    parts = re.split(r"(`[^`]+`)", escaped)
    out = []
    for part in parts:
        if len(part) > 2 and part[0] == "`" and part[-1] == "`":
            out.append("<code>" + part[1:-1] + "</code>")
            continue

        def link(m):
            text, url = m.group(1), m.group(2)
            if re.match(r"(?i)^https?://", url):
                return '<a href="%s" target="_blank" rel="noopener noreferrer nofollow">%s</a>' % (url, text)
            if re.match(r"^mailto:[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+$", url):
                return '<a href="%s">%s</a>' % (url, text)
            if re.match(r"^[A-Za-z0-9_\-]+\.html(#[A-Za-z0-9_\-]+)?$", url):
                return '<a href="%s">%s</a>' % (url, text)
            return text  # javascript:, data: ... are dropped, the words stay

        part = re.sub(r"\[([^\]\n]{1,200})\]\(([^\s)]{1,300})\)", link, part)
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part, flags=re.S)
        part = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", part, flags=re.S)
        out.append(part)
    return "".join(out)


def md_render(markdown):
    html_out = []
    para, items, quote, code = [], [], [], []
    state = {"list": None, "in_code": False}

    def flush_para():
        if para:
            html_out.append("<p>%s</p>" % md_inline(" ".join(para)))
            para.clear()

    def flush_list():
        if state["list"]:
            tag = state["list"]
            html_out.append("<%s>" % tag)
            html_out.extend("<li>%s</li>" % md_inline(i) for i in items)
            html_out.append("</%s>" % tag)
            state["list"] = None
            items.clear()

    def flush_quote():
        if quote:
            html_out.append("<blockquote><p>%s</p></blockquote>" % md_inline(" ".join(quote)))
            quote.clear()

    def flush_all():
        flush_para(); flush_list(); flush_quote()

    for line in markdown.replace("\t", "    ").splitlines():
        if line.startswith("```"):
            if state["in_code"]:
                html_out.append("<pre><code>%s</code></pre>" % e("\n".join(code)))
                code.clear()
                state["in_code"] = False
            else:
                flush_all()
                state["in_code"] = True
            continue
        if state["in_code"]:
            code.append(line)
            continue
        if not line.strip():
            flush_all()
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            flush_all()
            tag = "h3" if len(m.group(1)) == 3 else "h2"
            html_out.append("<%s>%s</%s>" % (tag, md_inline(m.group(2).strip()), tag))
            continue
        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if m:
            flush_para(); flush_quote()
            if state["list"] != "ul":
                flush_list(); state["list"] = "ul"
            items.append(m.group(1).strip())
            continue
        m = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if m:
            flush_para(); flush_quote()
            if state["list"] != "ol":
                flush_list(); state["list"] = "ol"
            items.append(m.group(1).strip())
            continue
        m = re.match(r"^>\s?(.*)$", line)
        if m:
            flush_para(); flush_list()
            quote.append(m.group(1).strip())
            continue
        flush_list(); flush_quote()
        para.append(line.strip())
    if state["in_code"]:
        html_out.append("<pre><code>%s</code></pre>" % e("\n".join(code)))
    flush_all()
    return "\n".join(html_out)


# ---------------------------------------------------------------- BLOG POSTS
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_RE = re.compile(r"^img/[A-Za-z0-9._ \-]+\.(?:webp|jpe?g|png|svg)$", re.I)


def load_posts():
    posts = []
    folder = os.path.join(ROOT, "posts")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        slug = name[:-3]
        if not SLUG_RE.match(slug):
            print("  skipped (bad file name):", name)
            continue
        raw = open(os.path.join(folder, name), encoding="utf-8-sig").read().replace("\r\n", "\n")
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
        if not m:
            print("  skipped (no header block):", name)
            continue
        meta = {}
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        try:
            date = datetime.datetime.strptime(meta.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            print("  skipped (bad date, use YYYY-MM-DD):", name)
            continue
        title = re.sub(r"[\x00-\x1f\x7f]+", " ", meta.get("title", "")).strip()
        if not title:
            print("  skipped (no title):", name)
            continue
        if date > datetime.date.today() + datetime.timedelta(days=1):
            print("  hidden until", date, ":", name)
            continue
        image = meta.get("image", "")
        if image and not (IMAGE_RE.match(image) and ".." not in image and os.path.isfile(os.path.join(ROOT, image))):
            print("  image ignored (must be a picture inside img/):", image)
            image = ""
        tags = [t.strip()[:30] for t in meta.get("tags", "").split(",") if t.strip()][:5]
        body = m.group(2).strip()
        posts.append(dict(
            slug=slug, title=title, date=date, image=image, tags=tags, body=body,
            excerpt=re.sub(r"\s+", " ", meta.get("excerpt", ""))[:240],
            minutes=max(1, -(-len(body.split()) // 200)),
        ))
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def fmt_date(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


# ---------------------------------------------------------------- PAGE LAYOUT
NAV = [
    ("home", "index.html", "Home"),
    ("about", "index.html#about", "About"),
    ("services", "index.html#services", "Services"),
    ("projects", "index.html#projects", "Projects"),
    ("shop", "shop.html", "Shop"),
    ("blog", "blog.html", "Blog"),
    ("location", "index.html#location", "Location"),
    ("contact", "index.html#contact", "Contact"),
]


def layout(title, description, main, active="", body_class="", show_cart=False,
           store_bar=False, scripts=(), noindex=False):
    full_title = "%s | Tooltech Technologies" % title if title else "Tooltech Technologies"
    nav = "\n".join(
        '          <a href="%s"%s>%s</a>' % (href, ' class="current" aria-current="page"' if key == active else "", label)
        for key, href, label in NAV
    )
    cart_btn = ('          <button type="button" id="cartBtn" class="cart-btn" aria-controls="cartDrawer" '
                'aria-expanded="false">\U0001F6D2 (<span id="cartCount">0</span>)</button>\n') if show_cart else ""
    bar = ""
    if store_bar:
        opts = "\n".join('            <option value="%s">%s</option>' % (k, e(v)) for k, v in CATEGORIES.items())
        bar = '''
      <form class="store-bar" id="storeBar" role="search">
        <div class="store-bar-inner">
          <select id="storeCat" aria-label="Search category">
            <option value="all">All</option>
%s
          </select>
          <input id="storeQ" type="search" maxlength="60" placeholder="Search Tooltech products" aria-label="Search products" autocomplete="off" />
          <button type="submit">Search</button>
        </div>
      </form>''' % opts
    scripts_html = "\n".join('    <script src="%s" defer></script>' % s for s in ["script.js"] + list(scripts))
    return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Security-Policy" content="%(csp)s" />
    <meta name="referrer" content="strict-origin-when-cross-origin" />
    <title>%(title)s</title>
    <meta name="description" content="%(desc)s" />
%(robots)s    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="style.css" />
  </head>
  <body%(body_class)s>
    <header>
      <nav class="navbar" id="navbar" aria-label="Main">
        <div class="company-name">
          <h3><a href="index.html">Tooltech</a></h3>
          <p>technologies</p>
        </div>

        <div class="nav-links" id="navLinks">
%(nav)s
        </div>

        <div class="nav-actions">
%(cart_btn)s          <div class="hamburger" id="hamburger" role="button" tabindex="0" aria-label="Open menu" aria-controls="navLinks" aria-expanded="false">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </nav>%(bar)s
    </header>

%(main)s

    <!-- FOOTER -->
    <footer>
      <div class="footer">
        <div class="top-footer">
          <div class="footer-brand">
            <h3>Tooltech <span>technologies</span></h3>
            <p>
              Genuine phone and computer accessories, plus IT support, networking,
              web development and ICT training. Order by WhatsApp or phone.
            </p>
          </div>
          <div class="footer-links">
            <h4>Quick Links</h4>
            <a href="index.html">Home</a>
            <a href="shop.html">Shop</a>
            <a href="blog.html">Blog</a>
            <a href="about.html">About</a>
            <a href="services.html">Services</a>
            <a href="projects.html">Projects</a>
            <a href="%(wa)s" target="_blank" rel="noopener">Chat on WhatsApp</a>
            <a href="tel:%(phone)s">Call Us</a>
            <a href="mailto:%(email)s">Email Us</a>
          </div>
        </div>
        <div class="bottom-footer">
          <p>&copy; <span id="year">%(year)d</span> Tooltech Technologies. All rights reserved.</p>
        </div>
      </div>
    </footer>

%(scripts)s
  </body>
</html>
''' % dict(
        csp=CSP, title=e(full_title), desc=e(description),
        robots='    <meta name="robots" content="noindex" />\n' if noindex else "",
        body_class=' class="%s"' % e(body_class) if body_class else "",
        nav=nav, cart_btn=cart_btn, bar=bar, main=main,
        wa=wa_link(), phone=CFG["phone"], email=CFG["contact_email"],
        year=datetime.date.today().year, scripts=scripts_html,
    )


CONTACT_FORM = '''<form class="contact-form" id="contactForm" novalidate>
            <p class="form-note" id="contactNote" role="status" hidden></p>
            <label for="contactEmail">Your email</label>
            <input type="email" id="contactEmail" name="email" required maxlength="120" autocomplete="email" />

            <label for="contactMessage">Message</label>
            <textarea id="contactMessage" name="message" required minlength="5" maxlength="3000" rows="5"></textarea>

            <div class="hp" aria-hidden="true">
              <label>Leave this field empty
                <input type="text" id="contactWebsite" name="website" tabindex="-1" autocomplete="off" />
              </label>
            </div>

            <button class="about-send-btn" type="submit">Send message</button>
            <p class="form-help">Opens your email app with the message ready to send to %s.</p>
          </form>''' % e(CFG["contact_email"])


# ---------------------------------------------------------------- PRODUCT CARDS
def product_card(p, shop=False):
    url = product_url(p)
    coming = p.get("coming")
    badge = ""
    if coming:
        badge = '<span class="p-badge soon">Coming soon</span>'
    elif p.get("offer"):
        badge = '<span class="p-badge">Offer of the Day</span>'
    if coming:
        action = '<a class="btn-ask" href="%s" target="_blank" rel="noopener">Ask on WhatsApp</a>' % e(
            wa_link("Hello Tooltech Technologies, please tell me when the %s is available." % p["name"]))
    elif shop:
        action = '<button type="button" class="btn-add" data-act="add">Add to cart</button>'
    else:
        action = '<a class="btn-ask" href="%s" target="_blank" rel="noopener">Order on WhatsApp</a>' % e(
            wa_link("Hello Tooltech Technologies, I am interested in %s." % p["name"]))
    return '''<article class="p-card" id="p-%(id)s">
  <a class="p-img" href="%(url)s" aria-label="View %(name)s">
    <img src="%(img)s" alt="%(name)s" loading="lazy" data-fallback="img/placeholder.svg" />
    %(badge)s
  </a>
  <div class="p-body">
    <a class="p-title" href="%(url)s">%(name)s</a>
    <p class="p-desc">%(desc)s</p>
    <div class="p-price">%(price)s</div>
    <div class="card-action" data-id="%(id)s">
      %(action)s
    </div>
  </div>
</article>''' % dict(id=e(p["id"]), url=e(url), name=e(p["name"]), img=e(p["image"]),
                     badge=badge, desc=e(p["description"]), price=e(money(p["price"])), action=action)


# ---------------------------------------------------------------- PAGES
def build_simple_pages():
    featured = "\n".join('''            <a class="card card-link" href="%s">
              <img src="%s" alt="%s" loading="lazy" />
              <div class="card-content">
                <h3>%s</h3>
                <p>%s</p>
                <div class="price">%s</div>
              </div>
            </a>''' % (e(product_url(p)), e(p["image"]), e(p["name"]), e(p["name"]), e(p["description"]), e(money(p["price"])))
        for p in PRODUCTS if p.get("featured"))

    pages = [
        ("index", "IT solutions and accessories",
         "IT solutions, computer repair, networking, training and genuine phone and computer accessories. Order by WhatsApp or phone.",
         "home", ""),
        ("about", "About us",
         "About Tooltech Technologies: web development, OS installation, networking, computer training, repair and maintenance.",
         "about", ""),
        ("services", "Services",
         "Networking, computer repair, ICT training, web development, OS installation and IT support from Tooltech Technologies.",
         "services", "footer-gap"),
        ("projects", "Projects",
         "Projects by Tooltech Technologies: school hotspot networks, websites, Linux servers, school systems and office networks.",
         "projects", "footer-gap"),
    ]
    for name, title, desc, active, body_class in pages:
        main = read("src/%s.html" % name)
        main = main.replace("{{FEATURED}}", featured).replace("{{CONTACT_FORM}}", CONTACT_FORM)
        scripts = ["contact.js"] if "{{CONTACT_FORM}}" in read("src/%s.html" % name) else []
        write(name + ".html", layout(title, desc, main, active=active, body_class=body_class, scripts=scripts))


def build_shop():
    cats_count = {}
    for p in PRODUCTS:
        cats_count[p["category"]] = cats_count.get(p["category"], 0) + 1

    def radio(name, value, label, count=None, checked=False):
        return '                <label class="f-opt"><input type="radio" name="%s" value="%s"%s /><span>%s</span>%s</label>' % (
            name, e(value), " checked" if checked else "", e(label),
            "<small>%d</small>" % count if count is not None else "")

    cat_html = [radio("cat", "all", "All products", len(PRODUCTS), True)]
    cat_html += [radio("cat", k, v, cats_count[k]) for k, v in CATEGORIES.items() if cats_count.get(k)]
    price_html = [radio("price", k, v[2], None, k == "all") for k, v in RANGES.items()]
    deal_html = [radio("deal", k, v, None, k == "all") for k, v in
                 (("all", "All items"), ("offer", "Offer of the Day"), ("soon", "Coming soon"))]
    sort_html = "\n".join('                  <option value="%s">%s</option>' % (k, v) for k, v in
                          (("featured", "Featured"), ("low", "Price: low to high"),
                           ("high", "Price: high to low"), ("name", "Name: A to Z")))

    cards = "\n".join(product_card(p, shop=True) for p in PRODUCTS)

    data = {
        "products": {p["id"]: dict(
            name=p["name"], desc=p["description"], price=p["price"], image=p["image"],
            coming=bool(p.get("coming")), offer=bool(p.get("offer")), cat=p["category"],
            url=product_url(p), order=i) for i, p in enumerate(PRODUCTS)},
        "categories": CATEGORIES,
        "ranges": {k: [v[0], v[1]] for k, v in RANGES.items()},
        "whatsapp": CFG["whatsapp"],
        "place": CFG["place"],
    }
    # \u003c etc. make it impossible for the data to break out of its tag
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    main = '''<main class="store-main">
      <form id="filterForm">
        <div class="shop-layout">
          <aside class="sidebar" aria-label="Filters">
            <button type="button" class="filter-toggle" id="filterToggle" aria-expanded="false" aria-controls="filterBody">Filters</button>
            <div class="filter-body" id="filterBody">
              <fieldset class="f-group">
                <legend>Category</legend>
%(cats)s
              </fieldset>
              <fieldset class="f-group">
                <legend>Price</legend>
%(prices)s
              </fieldset>
              <fieldset class="f-group">
                <legend>Deals</legend>
%(deals)s
              </fieldset>
              <button type="button" class="link-clear" id="clearFilters" hidden>Clear all filters</button>
            </div>
          </aside>

          <section class="results" aria-label="Products">
            <div class="results-bar">
              <p id="resultCount" aria-live="polite"></p>
              <label class="sort-label">Sort by
                <select id="sort">
%(sort)s
                </select>
              </label>
            </div>
            <div class="p-grid" id="shopGrid">
%(cards)s
            </div>
            <div class="empty-note" id="noResults" hidden>
              <h2>No products match</h2>
              <p>Try a different search or <button type="button" class="link-clear" id="noResultsClear">clear all filters</button>. You can also <a href="%(wa)s" target="_blank" rel="noopener">ask us on WhatsApp</a>.</p>
            </div>
          </section>
        </div>
      </form>
    </main>

    <!-- CART (shop page only) -->
    <div class="cart-overlay" id="cartOverlay" hidden></div>
    <aside class="cart-drawer" id="cartDrawer" role="dialog" aria-modal="true" aria-labelledby="cartTitle" aria-hidden="true" tabindex="-1">
      <div class="drawer-head">
        <h2 id="cartTitle">Your cart</h2>
        <button type="button" class="drawer-close" id="cartClose" aria-label="Close cart">&times;</button>
      </div>

      <div class="drawer-empty" id="cartEmpty">
        <p>Your cart is empty.</p>
        <p class="sum-note">Add something from the shop and it will appear here.</p>
      </div>

      <div class="drawer-body" id="cartBody" hidden>
        <div id="cartItems"></div>
        <div class="sum-row"><span id="sumLabel">Subtotal</span><strong id="sumTotal"></strong></div>
        <p class="sum-note">Delivery cost and payment are confirmed with you on WhatsApp. You do not pay on this website.</p>
        <button type="button" class="btn-add" id="proceed">Proceed to checkout</button>

        <form id="checkoutForm" hidden novalidate>
          <h3>Your details</h3>
          <label for="cName">Full name</label>
          <input id="cName" type="text" maxlength="80" autocomplete="name" />
          <label for="cPhone">Phone number</label>
          <input id="cPhone" type="tel" maxlength="20" autocomplete="tel" placeholder="07..." />
          <fieldset class="method">
            <legend>How do you want to get it?</legend>
            <label><input type="radio" name="method" value="pickup" checked /> Pick up in %(place)s</label>
            <label><input type="radio" name="method" value="delivery" /> Delivery</label>
          </fieldset>
          <div id="addrWrap" hidden>
            <label for="cAddr">Delivery location</label>
            <input id="cAddr" type="text" maxlength="120" autocomplete="street-address" placeholder="Area, landmark" />
          </div>
          <label for="cNotes">Notes (optional)</label>
          <textarea id="cNotes" rows="2" maxlength="300"></textarea>
          <p class="form-error" id="formError" role="alert" hidden></p>
          <button type="submit" class="btn-add">Place order on WhatsApp</button>
          <button type="button" class="link-clear" id="backToCart">Back</button>
        </form>

        <div id="sent" hidden>
          <h3>Your order is ready</h3>
          <p>WhatsApp opened with your order, reference <strong id="sentRef"></strong>. Press <strong>Send</strong> there and we will confirm stock, delivery and payment.</p>
          <button type="button" class="btn-ask" id="clearCart">Clear my cart</button>
          <button type="button" class="link-clear" id="editOrder">Change my order</button>
        </div>
      </div>
    </aside>

    <!-- Product data for the cart and filters. A JSON data block is not a script, so the
         content-security-policy allows it. -->
    <script type="application/json" id="productData">%(blob)s</script>''' % dict(
        cats="\n".join(cat_html), prices="\n".join(price_html), deals="\n".join(deal_html),
        sort=sort_html, cards=cards, wa=e(wa_link()), place=e(CFG["place"]), blob=blob)

    write("shop.html", layout(
        "Shop", "Phone and computer accessories: OTG adapters, memory cards, flash disks, cables and earphones. Order on WhatsApp.",
        main, active="shop", body_class="store", show_cart=True, store_bar=True, scripts=["shop.js"]))


def build_product_pages():
    for p in PRODUCTS:
        coming = p.get("coming")
        cat_name = CATEGORIES.get(p["category"], p["category"])
        related = [x for x in PRODUCTS if x["category"] == p["category"] and x["id"] != p["id"]]
        others = [x for x in PRODUCTS if x["category"] != p["category"]]
        more = (related + others)[:4]
        badge = ""
        if coming:
            badge = '<span class="p-badge soon">Coming soon</span>'
        elif p.get("offer"):
            badge = '<span class="p-badge">Offer of the Day</span>'
        if coming:
            buy = '''<p class="stock soon">Coming soon</p>
          <a class="btn-buy" href="%s" target="_blank" rel="noopener">Ask on WhatsApp</a>''' % e(
                wa_link("Hello Tooltech Technologies, please tell me when the %s is available." % p["name"]))
        else:
            buy = '''<p class="stock">Available to order</p>
          <a class="btn-add" href="shop.html#p-%s">Add to cart in the shop</a>
          <a class="btn-buy" href="%s" target="_blank" rel="noopener">Order on WhatsApp</a>''' % (
                e(p["id"]), e(wa_link("Hello Tooltech Technologies, I would like to order %s." % p["name"])))
        main = '''<main class="store-main">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="shop.html">Shop</a> <span>/</span>
        <a href="shop.html?cat=%(cat)s">%(cat_name)s</a> <span>/</span>
        <span>%(name)s</span>
      </nav>

      <div class="detail">
        <div class="detail-img">
          <img src="%(img)s" alt="%(name)s" data-fallback="img/placeholder.svg" />
          %(badge)s
        </div>
        <div class="detail-info">
          <h1>%(name)s</h1>
          <p class="detail-sub">%(desc)s</p>
          <div class="detail-price">%(price)s</div>
          <p class="detail-meta">Sold by Tooltech Technologies, %(place)s. Delivery cost and payment are confirmed with you on WhatsApp.</p>
          <ul class="detail-list">
            <li>Category: %(cat_name)s</li>
            <li>Order by WhatsApp or phone</li>
          </ul>
        </div>
        <aside class="buybox">
          <div class="detail-price">%(price)s</div>
          %(buy)s
          <a class="btn-ghost-dark" href="%(chat)s" target="_blank" rel="noopener">Chat about this item</a>
          <a class="btn-ghost-dark" href="tel:%(phone)s">Call us</a>
        </aside>
      </div>

      <h2 class="row-title">More you may like</h2>
      <div class="p-grid">
%(more)s
      </div>
    </main>''' % dict(
            cat=e(p["category"]), cat_name=e(cat_name), name=e(p["name"]), img=e(p["image"]), badge=badge,
            desc=e(p["description"]), price=e(money(p["price"])), place=e(CFG["place"]), buy=buy,
            chat=e(wa_link("Hello Tooltech Technologies, I am interested in %s." % p["name"])),
            phone=CFG["phone"], more="\n".join(product_card(x) for x in more))
        write(product_url(p), layout(
            p["name"], "%s (%s) at Tooltech Technologies. Order on WhatsApp or phone." % (p["name"], p["description"]),
            main, active="shop", body_class="store"))


def blog_card(p):
    url = "post-%s.html" % p["slug"]
    img = p["image"] or "img/placeholder-wide.svg"
    excerpt = '<p class="post-excerpt">%s</p>' % e(p["excerpt"]) if p["excerpt"] else ""
    return '''            <article class="card blog-card">
              <a class="blog-img" href="%(url)s" tabindex="-1" aria-hidden="true">
                <img src="%(img)s" alt="" loading="lazy" data-fallback="img/placeholder-wide.svg" />
              </a>
              <div class="card-content">
                <p class="post-meta">%(date)s &middot; %(min)d min read</p>
                <h3><a href="%(url)s">%(title)s</a></h3>
                %(excerpt)s
                <a class="svc-more" href="%(url)s">Read more</a>
              </div>
            </article>''' % dict(url=e(url), img=e(img), date=e(fmt_date(p["date"])), min=p["minutes"],
                                 title=e(p["title"]), excerpt=excerpt)


def build_blog(posts):
    per = CFG["posts_per_page"]
    pages = max(1, -(-len(posts) // per))

    def page_name(n):
        return "blog.html" if n == 1 else "blog-page-%d.html" % n

    # remove old list pages so deleted posts do not leave stale files behind
    for f in os.listdir(ROOT):
        if re.match(r"^(post-.+|blog-page-\d+)\.html$", f):
            os.remove(os.path.join(ROOT, f))

    for n in range(1, pages + 1):
        chunk = posts[(n - 1) * per: n * per]
        if chunk:
            grid = '          <div class="blog-grid">\n%s\n          </div>' % "\n".join(blog_card(p) for p in chunk)
        else:
            grid = '''          <div class="empty-note">
            <h2>No posts yet</h2>
            <p>We are writing our first posts. Please check back soon.</p>
          </div>'''
        pager = ""
        if pages > 1:
            prev = '<a class="btn btn-line" href="%s">&larr; Newer posts</a>' % page_name(n - 1) if n > 1 else ""
            nxt = '<a class="btn btn-line" href="%s">Older posts &rarr;</a>' % page_name(n + 1) if n < pages else ""
            pager = '''
          <nav class="pager" aria-label="Blog pages">
            %s
            <span>Page %d of %d</span>
            %s
          </nav>''' % (prev, n, pages, nxt)
        main = '''<main>
      <div class="page-head">
        <h1>Blog</h1>
        <p>Tips and guides on computers, networking, accessories and digital skills.</p>
      </div>

      <section class="block pt-20">
        <div class="block-inner">
%s%s
        </div>
      </section>
    </main>''' % (grid, pager)
        write(page_name(n), layout("Blog", "Tips and guides on computers, networking, accessories and digital skills from Tooltech Technologies.",
                                   main, active="blog", body_class="footer-gap"))

    for p in posts:
        others = [x for x in posts if x["slug"] != p["slug"]][:3]
        tags = "\n".join('          <span class="post-tag">%s</span>' % e(t) for t in p["tags"])
        cover = ('<img class="post-cover" src="%s" alt="" data-fallback="img/placeholder-wide.svg" />' % e(p["image"])) if p["image"] else ""
        more = ""
        if others:
            more = '''
      <section class="block alt">
        <div class="block-inner">
          <h2>More from the blog</h2>
          <div class="blog-grid">
%s
          </div>
        </div>
      </section>''' % "\n".join(blog_card(x) for x in others)
        main = '''<main>
      <article class="post-wrap">
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="blog.html">Blog</a> <span>/</span> <span>%(title)s</span>
        </nav>
        <h1 class="post-title">%(title)s</h1>
        <p class="post-meta">
          <time datetime="%(iso)s">%(date)s</time>
          &middot; %(min)d min read
%(tags)s
        </p>
        %(cover)s

        <div class="post-body">
%(body)s
        </div>

        <aside class="post-cta">
          <h2>Need help with this?</h2>
          <p>Send us an email or a WhatsApp message and we will get back to you.</p>
          <div class="svc-actions">
            <a class="btn btn-pink" href="mailto:%(email)s">Email us</a>
            <a class="btn btn-line" href="%(wa)s" target="_blank" rel="noopener">Chat on WhatsApp</a>
          </div>
        </aside>
      </article>
%(more)s
    </main>''' % dict(title=e(p["title"]), iso=p["date"].isoformat(), date=e(fmt_date(p["date"])), min=p["minutes"],
                      tags=tags, cover=cover, body=md_render(p["body"]), email=e(CFG["contact_email"]),
                      wa=e(wa_link()), more=more)
        write("post-%s.html" % p["slug"], layout(p["title"], p["excerpt"], main, active="blog"))


def build_404():
    main = '''<main>
      <div class="page-head">
        <h1>Page not found</h1>
        <p>The page you asked for does not exist or has moved.</p>
      </div>
      <section class="block pt-20">
        <div class="block-inner">
          <div class="svc-actions center">
            <a class="btn btn-pink" href="index.html">Go to the home page</a>
            <a class="btn btn-line" href="shop.html">Open the shop</a>
            <a class="btn btn-line" href="blog.html">Read the blog</a>
          </div>
        </div>
      </section>
    </main>'''
    write("404.html", layout("Page not found", "", main, body_class="footer-gap", noindex=True))


if __name__ == "__main__":
    print("Building Tooltech site ...")
    posts = load_posts()
    build_simple_pages()
    build_shop()
    build_product_pages()
    build_blog(posts)
    build_404()
    print("Done: %d products, %d blog posts." % (len(PRODUCTS), len(posts)))
