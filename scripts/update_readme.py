#!/usr/bin/env python3
"""
Update profile README dynamic sections and draw a sky SVG.
All APIs are free / no-key (NASA uses DEMO_KEY, called once per run).
"""
import re, os, json, math, random, datetime, urllib.request, urllib.error, html

README = "README.md"
SKY_SVG = "assets/sky.svg"

# ----- Locations / config -----
EINDHOVEN = "Eindhoven"                 # weather (where Hy studies)
SKY_LAT, SKY_LNG, SKY_TZ = 51.4416, 5.4697, "Europe/Amsterdam"  # Eindhoven sky
NASA_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
CET_OFFSET = 2

UA = "giahymai-readme-bot/1.0 (https://github.com/giahymai/giahymai)"

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

# ===================== DATA =====================

def get_weather():
    try:
        cur = json.loads(fetch(f"https://wttr.in/{EINDHOVEN}?format=j1"))["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        emoji = {"Sunny":"☀️","Clear":"🌙","Partly cloudy":"⛅","Cloudy":"☁️",
                 "Overcast":"☁️","Mist":"🌫️","Fog":"🌫️","Rain":"🌧️",
                 "Light rain":"🌦️","Patchy rain possible":"🌦️","Snow":"❄️"}.get(desc,"🌡️")
        return f"{emoji} **{EINDHOVEN}**: {cur['temp_C']}°C (feels {cur['FeelsLikeC']}°C) · {desc}"
    except Exception as e:
        return f"🌡️ Weather unavailable ({e.__class__.__name__})"

def get_hn(n=4):
    try:
        ids = json.loads(fetch("https://hacker-news.firebaseio.com/v0/topstories.json"))[:n]
        out = []
        for i in ids:
            it = json.loads(fetch(f"https://hacker-news.firebaseio.com/v0/item/{i}.json"))
            title = html.unescape(it.get("title","").strip())
            link = it.get("url") or f"https://news.ycombinator.com/item?id={i}"
            out.append(f"- [{title}]({link})")
        return "\n".join(out) if out else "- (no items)"
    except Exception as e:
        return f"- HN unavailable ({e.__class__.__name__})"

DEV_FACTS = [
    "The first computer bug was a real moth, taped into a logbook by Grace Hopper's team in 1947.",
    "`git` was written by Linus Torvalds in about 10 days in 2005.",
    "Python is named after Monty Python, not the snake.",
    "Java was originally called 'Oak', after a tree outside James Gosling's office.",
    "The `null` reference was called a 'billion-dollar mistake' by its own inventor, Tony Hoare.",
    "QWERTY was designed to slow typists down so mechanical typewriters wouldn't jam.",
    "The first 1GB hard drive (1980) weighed over 250 kg and cost $40,000.",
    "Ada Lovelace wrote the first algorithm intended for a machine, ~100 years before computers existed.",
    "There are two hard things in CS: cache invalidation, naming things, and off-by-one errors.",
    "The '@' in email was chosen by Ray Tomlinson in 1971 because it was rarely used in names.",
]

def get_fact():
    random.seed(datetime.date.today().toordinal())
    return "💡 " + random.choice(DEV_FACTS)

ASTRO_FACTS = [
    "A day on Venus is longer than its year.",
    "The Moon drifts ~3.8 cm farther from Earth every year.",
    "Sunlight takes about 8 minutes 20 seconds to reach Earth.",
    "There are more stars in the universe than grains of sand on Earth's beaches.",
    "A teaspoon of neutron star would weigh about a billion tonnes.",
    "Saturn is less dense than water — it would float in a big enough bathtub.",
    "A supermoon looks ~14% bigger and ~30% brighter than a micromoon.",
    "Footprints on the Moon may last millions of years — there's no wind.",
    "Jupiter's Great Red Spot is a storm raging for at least 350 years.",
    "Drive straight up at highway speed and you'd hit space in about an hour.",
]

MOON_EMOJI = {
    "New Moon":"🌑","Waxing Crescent":"🌒","First Quarter":"🌓","Waxing Gibbous":"🌔",
    "Full Moon":"🌕","Waning Gibbous":"🌖","Last Quarter":"🌗","Waning Crescent":"🌘",
}

def get_sky_data():
    """Returns dict for both the text block and the SVG drawing."""
    d = {"sunrise":"—","sunset":"—","golden":"—","daylen":"—",
         "phase":"","illum":0.0,"phase_value":0.5,"ok":False}
    try:
        r = json.loads(fetch(
            f"https://api.sunrisesunset.io/json?lat={SKY_LAT}&lng={SKY_LNG}&timezone={SKY_TZ}"))["results"]
        d.update(sunrise=r["sunrise"], sunset=r["sunset"],
                 golden=r.get("golden_hour","—"), daylen=r.get("day_length","—"),
                 phase=r.get("moon_phase",""), illum=float(r.get("moon_illumination",0) or 0),
                 phase_value=float(r.get("moon_phase_value",0.5) or 0.5), ok=True)
    except Exception as e:
        d["err"] = e.__class__.__name__
    return d

def sky_text(d):
    if not d["ok"]:
        return f"🌙 Sky data unavailable ({d.get('err','?')})"
    moon = MOON_EMOJI.get(d["phase"], "🌙")
    random.seed(datetime.date.today().toordinal() + 7)
    fact = random.choice(ASTRO_FACTS)
    return (f"🌅 **Sunrise** {d['sunrise']}  ·  🌇 **Sunset** {d['sunset']}\n"
            f"✨ **Golden hour** {d['golden']}  ·  ⏳ **Day length** {d['daylen']}\n"
            f"{moon} **Moon**: {d['phase']} ({d['illum']:.0f}% lit)\n\n"
            f"> 🔭 *{fact}*")

def get_apod():
    """Fetch NASA Astronomy Picture of the Day. Returns (markdown, ok)."""
    last_err = None
    for key in (NASA_KEY, "DEMO_KEY"):   # try user key, then DEMO_KEY
        try:
            a = json.loads(fetch(f"https://api.nasa.gov/planetary/apod?api_key={key}"))
            if a.get("media_type") != "image":
                return f"🎬 **{a.get('title','APOD')}** — [watch today's APOD]({a.get('url','')})", True
            img = a.get("hdurl") or a.get("url")
            title = a.get("title", "Astronomy Picture of the Day")
            link = a.get("url")
            md = (f'<a href="{link}"><img src="{img}" width="100%" '
                  f'alt="NASA APOD: {html.escape(title)}" /></a>\n\n'
                  f'<sub>📷 <b>{html.escape(title)}</b> · NASA Astronomy Picture of the Day</sub>')
            return md, True
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            print(f"[APOD] key={key[:6]}… failed: HTTP {e.code} {e.reason}")
        except Exception as e:
            last_err = e.__class__.__name__
            print(f"[APOD] key={key[:6]}… failed: {e.__class__.__name__}: {e}")
    return f"🛰️ APOD unavailable ({last_err})", False

# ---------- Landmark of the day (curated names, images via Wikipedia API) ----------
# Only the name + note are hard-coded; the image is fetched live from Wikipedia,
# so links never rot. (title, country, wiki_page, note)
LANDMARKS = [
    ("Eiffel Tower", "France 🇫🇷", "Eiffel_Tower",
     "Built for the 1889 World's Fair and meant to be torn down 20 years later — it stayed."),
    ("Machu Picchu", "Peru 🇵🇪", "Machu_Picchu",
     "A 15th-century Inca citadel at 2,430 m, unknown to the outside world until 1911."),
    ("Taj Mahal", "India 🇮🇳", "Taj_Mahal",
     "A marble mausoleum built by Shah Jahan for his wife — it shifts color through the day."),
    ("Petra", "Jordan 🇯🇴", "Petra",
     "An entire city carved into rose-red sandstone over 2,000 years ago by the Nabataeans."),
    ("Great Wall of China", "China 🇨🇳", "Great_Wall_of_China",
     "Not one wall but many, built over centuries — together stretching more than 21,000 km."),
    ("Colosseum", "Italy 🇮🇹", "Colosseum",
     "Rome's amphitheatre held ~50,000 people and could even be flooded for mock sea battles."),
    ("Santorini", "Greece 🇬🇷", "Santorini",
     "Its white-and-blue towns sit on the rim of a volcano that erupted catastrophically ~1600 BC."),
    ("Mount Fuji", "Japan 🇯🇵", "Mount_Fuji",
     "Japan's highest peak (3,776 m) and an active volcano, last erupting in 1707."),
    ("Sydney Opera House", "Australia 🇦🇺", "Sydney_Opera_House",
     "Its sail-like shells are covered in over a million self-cleaning tiles."),
    ("Christ the Redeemer", "Brazil 🇧🇷", "Christ_the_Redeemer_(statue)",
     "A 30-m statue atop Corcovado, struck by lightning several times a year."),
    ("Angkor Wat", "Cambodia 🇰🇭", "Angkor_Wat",
     "The largest religious monument on Earth, built in the early 12th century."),
    ("Neuschwanstein Castle", "Germany 🇩🇪", "Neuschwanstein_Castle",
     "The fairy-tale castle that inspired Disney's Sleeping Beauty castle."),
    ("Grand Canyon", "USA 🇺🇸", "Grand_Canyon",
     "Carved by the Colorado River over ~6 million years, up to 1.8 km deep."),
    ("Hạ Long Bay", "Vietnam 🇻🇳", "Ha_Long_Bay",
     "Thousands of limestone karsts rising from emerald water — a drowned karst landscape."),
    ("Pyramids of Giza", "Egypt 🇪🇬", "Giza_pyramid_complex",
     "The Great Pyramid stood as the tallest human-made structure for ~3,800 years."),
    ("Golden Gate Bridge", "USA 🇺🇸", "Golden_Gate_Bridge",
     "Its colour, 'International Orange', was chosen to stay visible in San Francisco fog."),
]

def get_landmark():
    idx = datetime.date.today().toordinal() % len(LANDMARKS)
    name, country, page, note = LANDMARKS[idx]
    img = ""
    try:
        data = json.loads(fetch(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{page}"))
        img = (data.get("originalimage") or data.get("thumbnail") or {}).get("source", "")
    except Exception:
        img = ""
    page_url = f"https://en.wikipedia.org/wiki/{page}"
    if img:
        media = (f'<a href="{page_url}"><img src="{img}" width="100%" '
                 f'alt="{html.escape(name)}" /></a>\n\n')
    else:
        media = ""  # image fetch failed; show text only
    return (f'{media}<sub>📍 <b>{html.escape(name)}</b> — {country} · '
            f'{html.escape(note)} · <a href="{page_url}">read more</a></sub>')

# ===================== SKY SVG =====================

def lerp(a, b, t): return a + (b - a) * t

def hex_lerp(c1, c2, t):
    a = tuple(int(c1[i:i+2],16) for i in (1,3,5))
    b = tuple(int(c2[i:i+2],16) for i in (1,3,5))
    return "#%02x%02x%02x" % tuple(int(lerp(a[i], b[i], t)) for i in range(3))

def sky_colors_for_hour(h):
    """Return (top, bottom) gradient colors based on local hour 0-23."""
    # keyframes: (hour, top, bottom)
    kf = [
        (0,  "#0b1026", "#1a1f3a"),   # deep night
        (5,  "#2a2a5e", "#c2698d"),   # pre-dawn
        (6,  "#ff9e6d", "#ffd89b"),   # sunrise
        (9,  "#4a90d9", "#aed4f5"),   # morning
        (12, "#2e7fd4", "#bfe3ff"),   # midday
        (17, "#3a6fb0", "#ffd1a1"),   # late afternoon
        (18, "#e8703a", "#ffb37a"),   # sunset
        (20, "#1e2a55", "#4a3a6e"),   # dusk
        (24, "#0b1026", "#1a1f3a"),   # back to night
    ]
    for i in range(len(kf)-1):
        h0, t0, b0 = kf[i]
        h1, t1, b1 = kf[i+1]
        if h0 <= h <= h1:
            t = (h - h0) / (h1 - h0) if h1 != h0 else 0
            return hex_lerp(t0, t1, t), hex_lerp(b0, b1, t)
    return kf[0][1], kf[0][2]

def draw_moon(cx, cy, r, phase_value):
    """Draw moon with shadow based on phase_value (0=new,0.5=full,1=new)."""
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f4f1e0"/>']
    illum = 1 - abs(1 - 2 * phase_value)   # 0 at new, 1 at full
    if illum < 0.97:
        waxing = phase_value < 0.5         # waxing => lit on the RIGHT
        # shadow disc covers the dark side; offset grows as illum -> 0
        # at illum=1 (full) offset huge (no shadow visible); at illum=0 offset 0 (full shadow)
        off = illum * 2 * r
        sx = (cx - off) if waxing else (cx + off)
        s.append(f'<circle cx="{sx:.1f}" cy="{cy}" r="{r}" fill="#0b1026" opacity="0.93"/>')
    s.append(f'<circle cx="{cx-r*0.3:.1f}" cy="{cy-r*0.2:.1f}" r="{r*0.18:.1f}" fill="#e2ddc8" opacity="0.5"/>')
    s.append(f'<circle cx="{cx+r*0.25:.1f}" cy="{cy+r*0.3:.1f}" r="{r*0.12:.1f}" fill="#e2ddc8" opacity="0.45"/>')
    return "\n".join(s)

def build_sky_svg(d, local_hour):
    W, H = 800, 240
    top, bot = sky_colors_for_hour(local_hour)
    is_night = local_hour < 6 or local_hour >= 19
    random.seed(20260603)  # stable star field
    stars = ""
    if is_night or local_hour < 7 or local_hour >= 18:
        n = 70 if is_night else 25
        for _ in range(n):
            x = random.uniform(0, W); y = random.uniform(0, H*0.7)
            rr = random.uniform(0.4, 1.6)
            op = random.uniform(0.3, 0.95)
            stars += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.1f}" fill="#ffffff" opacity="{op:.2f}"/>'

    # moon (top-right)
    moon = draw_moon(W-130, 75, 42, d.get("phase_value", 0.5)) if d["ok"] else ""

    # simple skyline silhouette at bottom
    sky_line = (
        f'<path d="M0,{H} L0,180 L60,180 L60,150 L100,150 L100,180 L150,180 '
        f'L150,120 L185,120 L185,180 L250,180 L250,160 L290,160 L290,180 '
        f'L360,180 L360,135 L400,135 L400,180 L470,180 L470,155 L510,155 '
        f'L510,180 L580,180 L580,125 L620,125 L620,180 L700,180 L700,150 '
        f'L740,150 L740,180 L{W},180 L{W},{H} Z" fill="#0b1026" opacity="0.55"/>'
    )

    phase = d.get("phase","") if d["ok"] else ""
    sub = (f"{d['sunrise']} → {d['sunset']}  ·  {phase}" if d["ok"]
           else "sky data unavailable")

    svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sky over the Netherlands">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{top}"/>
    <stop offset="100%" stop-color="{bot}"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#sky)"/>
{stars}
{moon}
{sky_line}
<text x="28" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="600" fill="#ffffff" opacity="0.95">The sky over the Netherlands</text>
<text x="28" y="78" font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="#ffffff" opacity="0.8">{sub}</text>
</svg>'''
    return svg

# ===================== ASSEMBLE =====================

def replace_block(text, name, content):
    pat = re.compile(rf"(<!-- {name}:start -->).*?(<!-- {name}:end -->)", re.DOTALL)
    return pat.sub(rf"\1\n{content}\n\2", text)

def main():
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=CET_OFFSET)

    sky = get_sky_data()
    apod_md, _ = get_apod()

    # write SVG (use local NL hour to pick sky colors)
    os.makedirs("assets", exist_ok=True)
    with open(SKY_SVG, "w", encoding="utf-8") as f:
        f.write(build_sky_svg(sky, now.hour))

    with open(README, encoding="utf-8") as f:
        text = f.read()

    text = replace_block(text, "DATE",
        f"📅 **{now.strftime('%A, %d %B %Y')}** — refreshed {now.strftime('%H:%M')} CET")
    text = replace_block(text, "WEATHER", get_weather())
    text = replace_block(text, "FACT", get_fact())
    text = replace_block(text, "SKY", sky_text(sky))
    text = replace_block(text, "APOD", apod_md)
    text = replace_block(text, "LANDMARK", get_landmark())
    text = replace_block(text, "HN", get_hn())

    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print("README + sky.svg updated.")

if __name__ == "__main__":
    main()