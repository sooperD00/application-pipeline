"""
The report. One self-contained HTML file you can email to someone.

The whole page is built around one idea: render the original document with every
character tinted by the bucket that claimed it, and leave everything the schema
failed to catch bare and flagged. Coverage stops being a percentage and becomes
something you can point at.
"""

from __future__ import annotations

import html
from pathlib import Path

HUE = {
    "role": "#2C5F8A",
    "accomplishment": "#17795E",
    "capability": "#8A6A10",
    "credential": "#6B4E9E",
    "narrative": "#7A4F2C",
    "unclassified": "#E01B4C",
}
ORDER = ["role", "accomplishment", "capability", "credential", "narrative", "unclassified"]

CSS = """
:root{
  --ground:#EEF0EC; --panel:#FAFBF9; --ink:#16201B; --muted:#63706A;
  --rule:#D3D8D2; --alarm:#E01B4C;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",ui-sans-serif,system-ui,sans-serif;
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:40px 28px 90px}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
h1{font-size:31px;font-weight:600;letter-spacing:-.02em;margin:.25em 0 .1em}
h2{font-size:20px;font-weight:600;letter-spacing:-.01em;margin:0}
.sub{color:var(--muted);max-width:62ch;margin:.5em 0 0}

.verdict{display:flex;gap:44px;flex-wrap:wrap;margin:30px 0 8px;
  padding:22px 26px;background:var(--panel);border:1px solid var(--rule);border-radius:3px}
.metric .n{font-family:"IBM Plex Mono",monospace;font-size:30px;font-weight:500;
  letter-spacing:-.02em;display:block;line-height:1.1}
.metric .l{font-size:12px;color:var(--muted)}
.bad{color:var(--alarm)}

.legend{display:flex;gap:16px;flex-wrap:wrap;margin:26px 0 8px;
  font-family:"IBM Plex Mono",monospace;font-size:11.5px}
.legend span{display:inline-flex;align-items:center;gap:6px;color:var(--muted)}
.sw{width:22px;height:9px;border-radius:2px;display:inline-block}

.sample{margin-top:44px;border-top:2px solid var(--ink);padding-top:16px}
.head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.pill{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);
  border:1px solid var(--rule);border-radius:2px;padding:2px 7px;background:var(--panel)}
.bar{display:flex;height:7px;margin:14px 0 4px;border-radius:2px;overflow:hidden;
  background:var(--rule)}
.bar i{display:block}

.cols{display:grid;grid-template-columns:1.35fr 1fr;gap:26px;margin-top:20px}
@media(max-width:880px){.cols{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:3px;padding:20px 22px}
.panel h3{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted);margin:0 0 14px;font-weight:500}

.src{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.5px;line-height:1.85;
  white-space:pre-wrap;word-break:break-word;max-height:640px;overflow:auto}
.src mark{background:transparent;color:inherit;border-radius:2px;padding:1px 0;
  box-shadow:inset 0 -.62em 0 var(--tint);transition:box-shadow .12s}
.src mark.lit{box-shadow:inset 0 -1.5em 0 var(--solid);color:#fff}
.src .miss{color:var(--alarm);text-decoration:underline wavy var(--alarm) 1px;
  text-underline-offset:3px}

.bk{border-left:3px solid var(--tint);padding:7px 0 7px 12px;margin-bottom:11px;cursor:default}
.bk:hover{background:#00000008}
.bk .t{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--tint)}
.bk .n{font-weight:600;font-size:14px}
.bk .c{color:var(--muted);font-size:13px}
.bk .m{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);margin-top:3px}
.alert{border:1px solid var(--alarm);border-radius:3px;padding:14px 16px;margin-bottom:18px;
  background:#E01B4C0A}
.alert h4{margin:0 0 8px;font-size:13px;color:var(--alarm);
  font-family:"IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase}
.alert p{margin:0 0 6px;font-size:13px}
.ok{color:var(--muted);font-size:13px;font-style:italic}
"""

JS = """
document.querySelectorAll('.bk').forEach(function(el){
  var k = el.dataset.k;
  function set(on){
    document.querySelectorAll('mark[data-k="'+k+'"]').forEach(function(m){
      m.classList.toggle('lit', on);
    });
  }
  el.addEventListener('mouseenter', function(){ set(true); });
  el.addEventListener('mouseleave', function(){ set(false); });
});
"""


def _overlay(text: str, owner: list[int], buckets) -> str:
    """The signature element: source text tinted by whichever bucket claimed it."""
    out, i, n = [], 0, len(text)
    while i < n:
        cur = owner[i]
        j = i
        while j < n and owner[j] == cur:
            j += 1
        chunk = html.escape(text[i:j])
        if cur == -1:
            out.append(f'<span class="miss">{chunk}</span>' if chunk.strip() else chunk)
        else:
            b = buckets[cur]
            tint = HUE.get(b.type, "#999")
            out.append(
                f'<mark data-k="{cur}" style="--tint:{tint}33;--solid:{tint}" '
                f'title="{html.escape(b.type)}: {html.escape(b.title)}">{chunk}</mark>'
            )
        i = j
    return "".join(out)


def _sample(r) -> str:
    ex, cov, counts = r["ex"], r["cov"], r["counts"]
    total = max(len(ex.buckets), 1)

    bar = "".join(
        f'<i style="width:{100.0*counts.get(t,0)/total}%;background:{HUE[t]}"></i>'
        for t in ORDER if counts.get(t)
    )

    problems = []
    unc = [b for b in ex.buckets if b.type == "unclassified"]
    if unc:
        items = "".join(
            f"<p><b>{html.escape(b.title)}</b> — {html.escape(b.note or 'no reason given')}</p>"
            for b in unc
        )
        problems.append(
            f'<div class="alert"><h4>{len(unc)} unclassified — the enum did not '
            f'cover these</h4>{items}</div>'
        )
    if cov.fabricated:
        items = "".join(
            f"<p>{html.escape(ex.buckets[i].title)}</p>" for i in cov.fabricated
        )
        problems.append(
            f'<div class="alert"><h4>{len(cov.fabricated)} quotes not found in the '
            f'source</h4><p>These buckets cite text that isn\'t in the document. '
            f'Either the model drifted while copying, or it invented content.</p>{items}</div>'
        )
    if ex.leftover.strip():
        problems.append(
            f'<div class="alert"><h4>Reported leftover</h4>'
            f'<p>{html.escape(ex.leftover[:700])}</p></div>'
        )
    if not problems:
        problems.append('<p class="ok">Nothing unclassified, no fabricated quotes, '
                        'nothing left over.</p>')

    cards = []
    for k, b in enumerate(ex.buckets):
        tint = HUE.get(b.type, "#999")
        meta = " · ".join(x for x in [b.org, f"{b.start}–{b.end}".strip("–"),
                                      b.issuer, b.hedge and f"hedge: {b.hedge}",
                                      b.parent_role_title and f"↳ {b.parent_role_title}",
                                      b.section_hint] if x)
        cards.append(
            f'<div class="bk" data-k="{k}" style="--tint:{tint}">'
            f'<div class="t">{b.type} · {b.confidence:.1f}</div>'
            f'<div class="n">{html.escape(b.title)}</div>'
            f'<div class="c">{html.escape(b.content[:230])}</div>'
            f'{f"<div class=m>{html.escape(meta)}</div>" if meta else ""}</div>'
        )

    covcls = "bad" if cov.pct < 85 else ""
    return f"""
<section class="sample">
  <div class="head">
    <h2>{html.escape(r['name'])}</h2>
    <span class="pill">read as {ex.doc_kind}</span>
    <span class="pill">quality: {ex.overall_quality}</span>
    <span class="pill {covcls}">{cov.pct:.1f}% of the text survived</span>
    <span class="pill">{len(ex.buckets)} buckets</span>
  </div>
  <div class="bar">{bar}</div>
  <p class="sub">{html.escape(ex.quality_reasoning)}
     <br><span class="eyebrow">suggested titles</span>
     {html.escape(", ".join(ex.suggested_titles) or "none")}</p>
  <div class="cols">
    <div class="panel"><h3>Coverage overlay — tinted text was claimed,
      <span style="color:var(--alarm)">red was not</span></h3>
      <div class="src">{_overlay(r['text'], cov.owner, ex.buckets)}</div></div>
    <div class="panel"><h3>Buckets — hover to locate</h3>
      {''.join(problems)}{''.join(cards)}</div>
  </div>
</section>"""


def write(path: Path, results, model: str, schema_version: str) -> None:
    worst = min((r["cov"].pct for r in results), default=0)
    unc = sum(r["counts"].get("unclassified", 0) for r in results)
    fab = sum(len(r["cov"].fabricated) for r in results)

    legend = "".join(
        f'<span><i class="sw" style="background:{HUE[t]}"></i>{t}</span>' for t in ORDER
    )

    body = "".join(_sample(r) for r in results)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vault intake — schema {schema_version}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">
<div class="eyebrow">vault intake · schema {schema_version} · {html.escape(model)}</div>
<h1>Does the five-type enum hold?</h1>
<p class="sub">Every sample below was decomposed into roles, accomplishments,
capabilities, credentials and narratives. The test is not whether the output
looks reasonable — it's whether anything had nowhere to go.</p>
<div class="verdict">
  <div class="metric"><span class="n {'bad' if unc else ''}">{unc}</span>
    <span class="l">unclassified across all samples</span></div>
  <div class="metric"><span class="n {'bad' if worst < 85 else ''}">{worst:.0f}%</span>
    <span class="l">worst-case text coverage</span></div>
  <div class="metric"><span class="n {'bad' if fab else ''}">{fab}</span>
    <span class="l">quotes not found in source</span></div>
  <div class="metric"><span class="n">{len(results)}</span>
    <span class="l">documents</span></div>
</div>
<div class="legend">{legend}</div>
{body}
</div><script>{JS}</script></body></html>"""
    path.write_text(doc, encoding="utf-8")
