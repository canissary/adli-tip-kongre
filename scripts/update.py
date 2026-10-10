#!/usr/bin/env python3
"""Adli Tıp Kongre Takvimi - haftalık güncelleme betiği.

Claude API'nin web arama aracıyla yeni duyurulan kongre, sempozyum, atölye ve
kursları arar; doğrulanmış bilgileri data.json'a ekler, feed.xml (RSS) üretir
ve yapılan değişikliklerin özetini changes.md dosyasına yazar.

Gerekli ortam değişkeni: ANTHROPIC_API_KEY
İsteğe bağlı: ANTHROPIC_MODEL (varsayılan aşağıda), MAX_SEARCHES
Yalnızca Python standart kütüphanesini kullanır.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
FEED = os.path.join(ROOT, "feed.xml")
CHANGES = os.path.join(ROOT, "changes.md")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-5-5"
MAX_SEARCHES = int(os.environ.get("MAX_SEARCHES") or "25")
API = "https://api.anthropic.com/v1/messages"

TYPES = {"kongre", "sempozyum", "atolye", "kurs"}
FIELDS = {"adli-tip", "adli-bilimler", "saglik-hukuku"}
MODES = {"yuzyuze", "online", "hibrit"}
LANGS = {"TR", "EN", "ES"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TEXT_KEYS = ["name", "theme", "org", "venue", "city", "country", "fee", "notes", "dateText"]
DATE_KEYS = ["start", "end", "abstractDeadline", "registrationDeadline", "earlyDeadline"]

PROMPT = """Bugünün tarihi: {today}.

Görevin: Türkiye'deki adli tıp doktorları için tutulan "Adli Tıp Kongre Takvimi" listesini güncellemek. Amaç, yeni açıklanan kongre, sempozyum, atölye ve kursları kaçırmamaları.

KAPSAM
- Türkiye'de düzenlenen tüm adli tıp, adli bilimler ve sağlık/tıp hukuku kongre, sempozyum, atölye ve kursları (yüz yüze veya online).
- Yurt dışında: Türkçe, İngilizce veya İspanyolca oturumu olan; dernek, kurum veya üniversitelerin düzenlediği etkinlikler.
- Sadece bugünden sonra başlayan etkinlikler.
- EKLEME: adli bilimlere özel olmayan, ücret karşılığı "ISBN'li bildiri kitabı" vaat eden genel/ticari kongreler; reklam niteliğindeki "summit" ve benzeri predatör etkinlikler.

KONTROL EDİLECEK KAYNAKLAR (en az bunlar)
atud.org.tr, adlitipgunleri.com, atk.gov.tr, turazbilimdernegi.com, Adli Bilimciler Derneği, Polis Akademisi Adli Bilimler Enstitüsü (pa.edu.tr), Jandarma ve Sahil Güvenlik Akademisi, üniversitelerin adli tıp anabilim dalları ve adli bilimler enstitüleri, tıp hukuku sempozyumları, doktorclub.com/kongreler/turkiye; aafs.org, ialm.info, ECLM, EAFS/ENFSI, IAFS, BAFS, World Association for Medical Law; Asociación Española de Derecho Sanitario, Sociedad Española de Medicina Legal y Forense, Asociación Nacional de Médicos Forenses, Latin Amerika adli tıp enstitüleri (Kolombiya INMLCF, Panama IMELCF, Meksika, Peru, Arjantin, Şili) ve Iberoamerikan kongreleri.

LİSTEDE ZATEN OLAN ETKİNLİKLER (id | ad | başlangıç | özet son tarihi | kayıt son tarihi | ücret | url)
{existing}

KURALLAR
- Yalnızca resmi sayfada veya güvenilir bir kaynakta gördüğün bilgiyi yaz. Bilinmeyeni null bırak, asla tahmin etme.
- Listede olan bir etkinliği yeni olarak ekleme; bilgisi değiştiyse "updates" içinde ver.
- Tarihler YYYY-MM-DD. Tarih belli değilse start = "YYYY-01-01" ve dateText = "2028 (tarih açıklanmadı)" gibi bir metin.
- Metinler Türkçe yazılır (etkinliğin resmi adı orijinal dilinde kalabilir). Ülke adı Türkçe (Türkiye, İspanya, ABD...).
- url resmi etkinlik sayfası olmalı ve https:// ile başlamalı.

ÇIKTI
Aramaların bitince yanıtının EN SONUNDA, <json> ve </json> etiketleri arasında yalnızca şu yapıda geçerli bir JSON ver:
{{
  "new": [
    {{"id": "kisa-benzersiz-kimlik-2027", "name": "...", "theme": null, "org": "...",
      "type": "kongre|sempozyum|atolye|kurs", "field": ["adli-tip","adli-bilimler","saglik-hukuku"],
      "start": "YYYY-MM-DD", "end": "YYYY-MM-DD veya null", "dateText": null,
      "venue": null, "city": "...", "country": "...", "mode": "yuzyuze|online|hibrit",
      "languages": ["TR","EN","ES"], "fee": null, "abstractDeadline": null,
      "registrationDeadline": null, "earlyDeadline": null, "notes": null, "url": "https://..."}}
  ],
  "updates": [
    {{"id": "mevcut-id", "abstractDeadline": "YYYY-MM-DD", "fee": "...", "reason": "kısa açıklama"}}
  ]
}}
Yeni bir şey yoksa {{"new": [], "updates": []}} döndür.
"""


def call_api(messages):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY tanımlı değil.")
    body = {
        "model": MODEL,
        "max_tokens": 16000,
        "messages": messages,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}],
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API hatası {e.code}: {e.read().decode(errors='replace')[:2000]}")


def ask(prompt):
    messages = [{"role": "user", "content": prompt}]
    for _ in range(6):
        resp = call_api(messages)
        if resp.get("stop_reason") == "pause_turn":
            messages.append({"role": "assistant", "content": resp["content"]})
            continue
        return "".join(b.get("text", "") for b in resp["content"] if b.get("type") == "text")
    sys.exit("Model yanıtı tamamlanmadı (pause_turn sınırı).")


def clean_date(v):
    return v if isinstance(v, str) and DATE_RE.match(v) else None


def clean_text(v, limit=400):
    if not isinstance(v, str):
        return None
    v = re.sub(r"\s+", " ", v).strip()
    return v[:limit] or None


def clean_event(e):
    if not isinstance(e, dict):
        return None
    out = {"id": re.sub(r"[^a-z0-9-]", "", str(e.get("id", "")).lower())[:80]}
    for k in TEXT_KEYS:
        out[k] = clean_text(e.get(k))
    for k in DATE_KEYS:
        out[k] = clean_date(e.get(k))
    out["type"] = e.get("type") if e.get("type") in TYPES else "kongre"
    out["field"] = [f for f in (e.get("field") or []) if f in FIELDS] or ["adli-tip"]
    out["mode"] = e.get("mode") if e.get("mode") in MODES else "yuzyuze"
    out["languages"] = [l for l in (e.get("languages") or []) if l in LANGS]
    url = e.get("url")
    out["url"] = url if isinstance(url, str) and url.startswith("https://") else None
    if not (out["id"] and out["name"] and out["start"] and out["url"] and out["country"]):
        return None
    return out


def parse(text):
    m = re.findall(r"<json>(.*?)</json>", text, re.S)
    if not m:
        sys.exit("Model JSON döndürmedi:\n" + text[-3000:])
    return json.loads(m[-1])


def build_feed(events, updated):
    items = sorted(events, key=lambda e: (e.get("added") or "", e["start"]), reverse=True)[:40]
    link = SITE_URL or "."
    parts = []
    for e in items:
        added = dt.datetime.strptime(e.get("added") or updated, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        place = ", ".join(x for x in [e.get("city"), e.get("country")] if x)
        desc = f"{e['start']} · {place} · Düzenleyen: {e.get('org') or '-'}"
        if e.get("abstractDeadline"):
            desc += f" · Özet son tarihi: {e['abstractDeadline']}"
        if e.get("registrationDeadline"):
            desc += f" · Kayıt son tarihi: {e['registrationDeadline']}"
        parts.append(
            "<item>"
            f"<title>{escape(e['name'])}</title>"
            f"<link>{escape(e['url'])}</link>"
            f"<guid isPermaLink=\"false\">{escape(e['id'])}</guid>"
            f"<pubDate>{format_datetime(added)}</pubDate>"
            f"<description>{escape(desc)}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        "<title>Adli Tıp Kongre Takvimi</title>"
        f"<link>{escape(link)}</link>"
        "<description>Adli tıp, adli bilimler ve sağlık hukuku kongre, sempozyum ve atölyeleri</description>"
        "<language>tr</language>" + "".join(parts) + "</channel></rss>\n"
    )


def main():
    today = dt.date.today()
    data = json.load(open(DATA, encoding="utf-8"))
    events = data["events"]
    by_id = {e["id"]: e for e in events}

    existing = "\n".join(
        f"{e['id']} | {e['name']} | {e['start']} | {e.get('abstractDeadline')} | "
        f"{e.get('registrationDeadline')} | {e.get('fee')} | {e['url']}"
        for e in events
    )
    result = parse(ask(PROMPT.format(today=today.isoformat(), existing=existing)))

    added, changed = [], []
    names = {e["name"].lower() for e in events}
    for raw in result.get("new", []):
        e = clean_event(raw)
        if not e or e["id"] in by_id or e["name"].lower() in names:
            continue
        if dt.date.fromisoformat(e["end"] or e["start"]) < today and not e.get("dateText"):
            continue
        e["added"] = today.isoformat()
        events.append(e)
        by_id[e["id"]] = e
        names.add(e["name"].lower())
        added.append(e)

    for u in result.get("updates", []):
        if not isinstance(u, dict) or u.get("id") not in by_id:
            continue
        e, diffs = by_id[u["id"]], []
        for k in TEXT_KEYS + DATE_KEYS:
            if k in u:
                v = clean_date(u[k]) if k in DATE_KEYS else clean_text(u[k])
                if v and v != e.get(k):
                    diffs.append(f"{k}: {e.get(k)} → {v}")
                    e[k] = v
        if diffs:
            changed.append((e, diffs, clean_text(u.get("reason")) or ""))

    cutoff = today - dt.timedelta(days=548)
    data["events"] = [
        e for e in events
        if e.get("dateText") or dt.date.fromisoformat(e.get("end") or e["start"]) >= cutoff
    ]
    data["updated"] = today.isoformat()

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(FEED, "w", encoding="utf-8") as f:
        f.write(build_feed(data["events"], data["updated"]))

    lines = [f"# Haftalık güncelleme – {today.isoformat()}", ""]
    if added:
        lines.append("## Yeni eklenen etkinlikler")
        for e in added:
            lines.append(
                f"- **{e['name']}** – {e['start']}, {e.get('city') or ''} {e['country']}"
                + (f" – özet son tarihi {e['abstractDeadline']}" if e.get("abstractDeadline") else "")
                + f" – {e['url']}"
            )
        lines.append("")
    if changed:
        lines.append("## Güncellenen bilgiler")
        for e, diffs, reason in changed:
            lines.append(f"- **{e['name']}**: " + "; ".join(diffs) + (f" ({reason})" if reason else ""))
        lines.append("")
    soon = sorted(
        (e[k], e["name"], label)
        for e in data["events"]
        for k, label in [("abstractDeadline", "özet"), ("registrationDeadline", "kayıt"), ("earlyDeadline", "erken kayıt")]
        if e.get(k) and 0 <= (dt.date.fromisoformat(e[k]) - today).days <= 30
    )
    if soon:
        lines.append("## Önümüzdeki 30 günde dolan son tarihler")
        lines += [f"- {d}: {n} ({l})" for d, n, l in soon]
        lines.append("")
    if not (added or changed):
        lines.append("Bu hafta yeni etkinlik veya değişiklik bulunmadı.")
    with open(CHANGES, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    # GitHub Actions'a yeni etkinlik olup olmadığını bildir
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"has_news={'true' if (added or changed) else 'false'}\n")


if __name__ == "__main__":
    main()
