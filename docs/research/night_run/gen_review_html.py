#!/usr/bin/env python3
"""Generate easy-to-read review HTML (with discuss-checkboxes) from the two rollup docs.

Self-contained: no third-party deps, no network. Reads the markdown, emits HTML.
Checkboxes + progress + persistence are vanilla JS (localStorage), so ticks survive reloads.
Run:  python3 docs/research/night_run/gen_review_html.py
Out:  docs/research/night_run/review_design.html  +  review_issues.html
"""
import os
import re
import html

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)

DOCS = [
    ("data_architecture_design_2026-06-17.md", "review_design.html",
     "Data-Architecture Design — Review", "File B — the 24 decisions (§0) + 6 findings (§18) are the payload.",
     ("0.", "18.")),
    ("data_issue_register_2026-06-17.md", "review_issues.html",
     "Data Issue Register — Review", "File A — read §2 (owner decisions) + §3 (regressions) first.",
     ("2.", "3.", "4.")),
]


def inline(t):
    """Convert inline markdown: escape, then code spans, then bold."""
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t


def md_to_html(md, checkable_prefixes):
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    cur_h2 = ""

    def checkable():
        s = cur_h2.lstrip("# ").strip()
        return any(s.startswith(p) for p in checkable_prefixes)

    while i < n:
        line = lines[i]

        # fenced code block (the ASCII diagram)
        if line.strip().startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre class='diagram'>" + "\n".join(buf) + "</pre>")
            continue

        # table: a line with | and the next line is a |---| separator
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2  # skip header + separator
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" +
                       "".join(f"<th>{inline(c)}</th>" for c in header) +
                       "</tr></thead><tbody>")
            for r in rows:
                cells = [inline(c) for c in r]
                # checkable only in the right section AND when the row names an item (bold 1st cell)
                is_item = checkable() and cells and cells[0].strip().startswith("<strong>")
                cls = " class='item'" if is_item else ""
                out.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            out.append("</tbody></table>")
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            if lvl == 2:
                cur_h2 = m.group(2)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # hr
        if re.match(r"^---+\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # blockquote (consume consecutive > lines)
        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(inline(lines[i].lstrip(">").strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue

        # list item (ordered or unordered) — gather continuation lines
        m = re.match(r"^(\s*)([0-9]+\.|[-*])\s+(.*)$", line)
        if m:
            indent = len(m.group(1))
            ordered = bool(re.match(r"[0-9]+\.", m.group(2)))
            buf = [m.group(3)]
            i += 1
            # continuation: indented non-empty lines that are not new list items
            while i < n and lines[i].strip() and not re.match(r"^\s*([0-9]+\.|[-*])\s+", lines[i]) \
                    and (len(lines[i]) - len(lines[i].lstrip())) > indent - 1 \
                    and not lines[i].startswith("#") and "|" not in lines[i]:
                buf.append(lines[i].strip())
                i += 1
            tag = "ol" if ordered else "ul"
            content = inline(" ".join(buf))
            # checkable only in the right section AND when the item is titled (bold lead)
            is_item = checkable() and content.strip().startswith("<strong>")
            cls = " class='item'" if is_item else ""
            out.append(f"<{tag} class='lwrap'><li{cls}>{content}</li></{tag}>")
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # paragraph
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#|>|---|\s*([0-9]+\.|[-*])\s|```)", lines[i]) \
                and "|" not in lines[i]:
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#0f1115;--card:#171a21;--ink:#e6e8ec;--mut:#9aa3b2;--line:#2a2f3a;--acc:#4da3ff;--done:#1f6f43;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 20px 120px}}
header.top{{position:sticky;top:0;z-index:10;background:rgba(15,17,21,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:14px 20px}}
header.top h1{{font-size:17px;margin:0 0 6px}}
header.top .sub{{color:var(--mut);font-size:12.5px}}
.progwrap{{display:flex;align-items:center;gap:12px;margin-top:10px}}
.bar{{flex:1;height:9px;background:#222733;border-radius:6px;overflow:hidden}}
.bar > i{{display:block;height:100%;width:0;background:var(--acc);transition:width .2s}}
.count{{font-size:12.5px;color:var(--mut);white-space:nowrap}}
.btns button{{background:#222733;color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:5px 10px;font-size:12px;cursor:pointer;margin-left:6px}}
.btns button:hover{{border-color:var(--acc)}}
h1,h2,h3,h4{{line-height:1.3}}
h2{{margin-top:34px;font-size:20px;border-bottom:1px solid var(--line);padding-bottom:6px}}
h3{{margin-top:24px;font-size:16px;color:#cdd3dd}}
h4{{margin-top:18px;font-size:14px;color:var(--mut)}}
p{{margin:10px 0}}
code{{background:#222733;padding:1px 5px;border-radius:4px;font-size:12.5px;color:#ffd9a0}}
pre.diagram{{background:#11141a;border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto;font-size:11.5px;color:#aeb6c4}}
blockquote{{margin:12px 0;padding:10px 14px;border-left:3px solid var(--acc);background:#141822;color:var(--mut);border-radius:0 8px 8px 0;font-size:13.5px}}
hr{{border:0;border-top:1px solid var(--line);margin:22px 0}}
table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:12.5px}}
th,td{{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#1c212b;color:#cdd3dd;position:sticky}}
ol.lwrap,ul.lwrap{{margin:8px 0;padding:0}}
.item{{position:relative;list-style:none}}
ol.lwrap > li.item,ul.lwrap > li.item{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px 12px 44px;margin:8px 0}}
li.item .cb,tr.item .cb{{position:absolute;left:14px;top:12px}}
td:first-child{{padding-left:34px;position:relative}}
tr.item td:first-child .cb{{position:absolute;left:9px;top:8px}}
.cb{{width:18px;height:18px;cursor:pointer;accent-color:var(--acc)}}
.item.done{{opacity:.5}}
.item.done > *:not(.cb){{text-decoration:line-through}}
tr.item.done td{{opacity:.5;text-decoration:line-through}}
.legend{{color:var(--mut);font-size:12px;margin-top:6px}}
</style></head><body>
<header class=top>
  <h1>{title}</h1>
  <div class=sub>{subtitle} &nbsp;·&nbsp; tick a box once we've <b>discussed &amp; answered</b> that item. Ticks save in this browser.</div>
  <div class=progwrap>
    <div class=bar><i id=barfill></i></div>
    <div class=count id=count>0 / 0 discussed</div>
    <div class=btns><button onclick=expandJump()>Next undiscussed ↓</button><button onclick=resetAll()>Reset</button></div>
  </div>
</header>
<div class=wrap>
{body}
</div>
<script>
const KEY="{key}";
let state=JSON.parse(localStorage.getItem(KEY)||"{{}}");
const items=[...document.querySelectorAll(".item")];
items.forEach((el,idx)=>{{
  el.dataset.k="i"+idx;
  const cb=document.createElement("input");
  cb.type="checkbox";cb.className="cb";
  const host=el.tagName==="TR"?el.querySelector("td"):el;
  host.insertBefore(cb,host.firstChild);
  if(state[el.dataset.k]){{cb.checked=true;el.classList.add("done");}}
  cb.addEventListener("change",()=>{{
    state[el.dataset.k]=cb.checked;
    el.classList.toggle("done",cb.checked);
    localStorage.setItem(KEY,JSON.stringify(state));
    render();
  }});
}});
function render(){{
  const done=items.filter(e=>e.classList.contains("done")).length;
  document.getElementById("count").textContent=done+" / "+items.length+" discussed";
  document.getElementById("barfill").style.width=(items.length?100*done/items.length:0)+"%";
}}
function expandJump(){{
  const next=items.find(e=>!e.classList.contains("done"));
  if(next)next.scrollIntoView({{behavior:"smooth",block:"center"}});
}}
function resetAll(){{if(confirm("Clear all ticks on this page?")){{state={{}};localStorage.removeItem(KEY);items.forEach(e=>{{e.classList.remove("done");e.querySelector(".cb").checked=false;}});render();}}}}
render();
</script>
</body></html>"""


def main():
    for src, dst, title, subtitle, checkable_prefixes in DOCS:
        with open(os.path.join(RESEARCH, src), encoding="utf-8") as f:
            md = f.read()
        body = md_to_html(md, checkable_prefixes)
        page = PAGE.format(title=html.escape(title), subtitle=html.escape(subtitle),
                           body=body, key="review_" + dst)
        outpath = os.path.join(HERE, dst)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(page)
        n_items = body.count("class='item'")
        print(f"wrote {outpath}  ({n_items} checkbox items)")


if __name__ == "__main__":
    main()
