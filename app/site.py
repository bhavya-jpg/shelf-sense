"""Marketing / site-level presentation: navbar, landing page, How-it-works page, footer.

Pure HTML builders and CSS, like app/ui.py. All figures quoted here come from the recorded
evaluation (docs/experiments/) and the README; nothing is live or computed on this page.
"""

from app.ui import LOGO, esc

REPO_URL = "https://github.com/bhavya-jpg/shelf-sense"

# Documented, recorded facts used on the landing and method pages (see docs/experiments/README.md).
FACTS = {
    "error_before": 8, "error_after": 1,
    "median_latency_s": "18.2", "latency_range": "11.7–45.8 s", "production_runs": 9,
    "experiment_records": 24,
}

CSS = """
[data-testid="stMain"]{overflow-x:hidden}
/* navbar */
.st-key-nav{position:sticky;top:0;z-index:999;background:rgba(10,11,12,.84);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line);margin:-26px -44px 0;padding:12px 44px!important}
@media (max-width:760px){.st-key-nav{margin:-18px -16px 0;padding:10px 16px!important}}
.ss-nav-brand{display:flex;align-items:center;gap:11px;font-family:var(--display);font-weight:600;font-size:19px;letter-spacing:-.015em;color:var(--tx)}
.ss-nav-brand svg{width:22px;height:22px}
.ss-nav-brand small{font-family:var(--mono);font-size:10.5px;font-weight:400;letter-spacing:.08em;color:var(--dim);text-transform:uppercase;margin-left:4px}
[data-testid="stPageLink-NavLink"]{background:transparent!important;border-radius:2px;padding:6px 4px!important;justify-content:center}
[data-testid="stPageLink-NavLink"] p,[data-testid="stPageLink-NavLink"] span{font-family:var(--mono)!important;font-size:12px!important;letter-spacing:.09em;text-transform:uppercase;color:var(--mu)!important;transition:color .15s}
[data-testid="stPageLink-NavLink"]:hover p,[data-testid="stPageLink-NavLink"]:hover span{color:var(--lime)!important}
.st-key-navcta [data-testid="stPageLink-NavLink"],.st-key-herocta [data-testid="stPageLink-NavLink"],.st-key-finalcta [data-testid="stPageLink-NavLink"],.st-key-methodcta [data-testid="stPageLink-NavLink"]{background:var(--lime)!important;padding:11px 16px!important;border-radius:2px}
.st-key-navcta [data-testid="stPageLink-NavLink"] p,.st-key-herocta [data-testid="stPageLink-NavLink"] p,.st-key-finalcta [data-testid="stPageLink-NavLink"] p,.st-key-methodcta [data-testid="stPageLink-NavLink"] p{color:#0A0B0C!important;font-weight:600}
.st-key-navcta [data-testid="stPageLink-NavLink"]:hover,.st-key-herocta [data-testid="stPageLink-NavLink"]:hover,.st-key-finalcta [data-testid="stPageLink-NavLink"]:hover,.st-key-methodcta [data-testid="stPageLink-NavLink"]:hover{background:#DDFF7A!important}
.st-key-heroghost [data-testid="stPageLink-NavLink"]{border:1px solid var(--line2);padding:11px 16px!important}
.st-key-heroghost [data-testid="stPageLink-NavLink"]:hover{border-color:var(--lime)}
.st-key-herocta [data-testid="stPageLink-NavLink"],.st-key-heroghost [data-testid="stPageLink-NavLink"],.st-key-finalcta [data-testid="stPageLink-NavLink"]{padding:16px 22px!important}
@media (max-width:760px){.st-key-navlinks{display:none}}
/* shared page bits */
.ss-eb{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--lime)}
.ss-eb-dim{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.ss-sec{padding:110px 0 0}
.ss-sec-head{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:48px;align-items:end;border-top:1px solid var(--line);padding-top:22px;margin-bottom:46px}
.ss-sec-h{font-family:var(--display);font-weight:600;font-size:clamp(34px,4vw,60px);line-height:1.02;letter-spacing:-.035em;color:var(--tx);margin-top:18px}
.ss-sec-h span{color:var(--dim)}
.ss-sec-lede{font-size:17px;line-height:1.65;color:var(--mu);max-width:560px}
@media (max-width:900px){.ss-sec-head{grid-template-columns:1fr;gap:16px}.ss-sec{padding-top:72px}}
/* hero */
.ss-hero2{padding:56px 0 8px}
.ss-hero2-top{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
.ss-wordmark{font-family:var(--display);font-weight:600;font-size:clamp(72px,15vw,232px);line-height:.84;letter-spacing:-.06em;color:var(--tx);margin:34px 0 0 -6px;white-space:nowrap}
.ss-wordmark span{color:var(--lime)}
.ss-hero2-lede{font-size:clamp(18px,1.6vw,23px);line-height:1.5;color:var(--tx);max-width:640px;letter-spacing:-.01em}
.ss-hero2-lede span{color:var(--mu)}
.ss-crosshair-row{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.06em;margin:46px 0 10px}
.ss-frame{position:relative;border:1px solid var(--line2);border-radius:6px;padding:14px;background:linear-gradient(180deg,var(--s2),var(--s1))}
.ss-frame img{display:block;width:100%;height:auto;border-radius:3px;border:1px solid var(--line)}
.ss-frame-bar{display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.05em;padding:2px 2px 12px}
.ss-frame-bar b{color:var(--mu);font-weight:500}
@media (max-width:640px){.ss-crosshair-row span:nth-child(2),.ss-frame-bar span:last-child{display:none}}
.ss-pin{position:absolute;font-family:var(--mono);font-size:10.5px;color:var(--dim);letter-spacing:.04em}
.ss-pin.tl{top:-22px;left:0}.ss-pin.br{bottom:-22px;right:0}
/* marquee */
.ss-marquee{width:100vw;margin-left:calc(50% - 50vw);overflow:hidden;background:var(--lime);color:#0A0B0C;margin-top:96px;border-top:1px solid #0A0B0C;border-bottom:1px solid #0A0B0C}
.ss-marquee--dark{background:var(--s1);color:var(--tx);border-color:var(--line);margin-top:110px}
.ss-marquee-track{display:flex;width:max-content;animation:ss-marquee 46s linear infinite}
.ss-marquee--dark .ss-marquee-track{animation-duration:70s;animation-direction:reverse}
.ss-marquee-item{display:flex;align-items:center;gap:30px;padding:16px 30px 16px 0;font-family:var(--display);font-weight:600;font-size:clamp(20px,2.2vw,32px);letter-spacing:-.02em;white-space:nowrap}
.ss-marquee-item::after{content:"+";font-family:var(--mono);font-weight:400;font-size:.8em;opacity:.55}
.ss-marquee--dark .ss-marquee-item{font-family:var(--mono);font-weight:400;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--mu);padding:14px 26px 14px 0;gap:26px}
@keyframes ss-marquee{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@media (prefers-reduced-motion:reduce){.ss-marquee-track{animation:none}}
/* problem columns */
.ss-cols4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:4px;background:var(--s1)}
.ss-col{padding:26px 24px 30px;border-left:1px solid var(--line);display:flex;flex-direction:column;gap:18px;min-height:280px}
.ss-col:first-child{border-left:none}
.ss-col-top{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--mu)}
.ss-col svg{width:88px;height:88px;margin:14px 0 6px}
.ss-col-h{font-family:var(--display);font-weight:600;font-size:22px;letter-spacing:-.02em;line-height:1.15;color:var(--tx);margin-top:auto}
.ss-col-p{font-size:14.5px;line-height:1.6;color:var(--mu)}
@media (max-width:1000px){.ss-cols4{grid-template-columns:repeat(2,minmax(0,1fr))}.ss-col:nth-child(3){border-left:none}.ss-col:nth-child(n+3){border-top:1px solid var(--line)}}
@media (max-width:560px){.ss-cols4{grid-template-columns:1fr}.ss-col{border-left:none!important;border-top:1px solid var(--line)}.ss-col:first-child{border-top:none}}
/* how it works */
.ss-how{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:56px;align-items:start}
.ss-how-steps{border-top:1px solid var(--line)}
.ss-step{display:grid;grid-template-columns:86px minmax(0,1fr);gap:18px;padding:26px 0;border-bottom:1px solid var(--line)}
.ss-step-n{font-family:var(--display);font-weight:600;font-size:46px;letter-spacing:-.04em;line-height:.9;color:var(--line2)}
.ss-step:hover .ss-step-n{color:var(--lime)}
.ss-step-h{font-family:var(--display);font-weight:600;font-size:23px;letter-spacing:-.02em;color:var(--tx);margin-bottom:6px}
.ss-step-p{font-size:15px;line-height:1.6;color:var(--mu)}
.ss-step-p code{font-family:var(--mono);font-size:12.5px;color:var(--tx);background:var(--s3);padding:1px 5px;border-radius:2px}
@media (max-width:1000px){.ss-how{grid-template-columns:1fr}}
/* features list */
.ss-feat{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:56px}
.ss-feat-rows{border-top:1px solid var(--line)}
.ss-feat-row{display:grid;grid-template-columns:56px minmax(0,1fr) minmax(0,1.2fr);gap:18px;padding:22px 0;border-bottom:1px solid var(--line);align-items:baseline}
.ss-feat-row span{font-family:var(--mono);font-size:11px;color:var(--lime)}
.ss-feat-row b{font-family:var(--display);font-size:20px;font-weight:600;letter-spacing:-.015em;color:var(--tx)}
.ss-feat-row p{font-size:14.5px;line-height:1.6;color:var(--mu);margin:0}
@media (max-width:1000px){.ss-feat{grid-template-columns:1fr;gap:24px}.ss-feat-row{grid-template-columns:44px minmax(0,1fr)}.ss-feat-row p{grid-column:2}}
/* evidence numbers */
.ss-nums{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.ss-num{padding:30px 24px 28px 0;border-left:1px solid var(--line);padding-left:24px}
.ss-num:first-child{border-left:none;padding-left:0}
.ss-num-v{font-family:var(--display);font-weight:600;font-size:clamp(52px,6vw,96px);line-height:.9;letter-spacing:-.05em;color:var(--tx);white-space:nowrap}
.ss-num-v small{font-size:.42em;color:var(--mu);letter-spacing:-.02em}
.ss-num-k{font-size:14px;line-height:1.55;color:var(--mu);margin-top:16px;max-width:260px}
.ss-src-note{font-family:var(--mono);font-size:11.5px;color:var(--dim);margin-top:16px;letter-spacing:.02em}
@media (max-width:1000px){.ss-nums{grid-template-columns:repeat(2,minmax(0,1fr))}.ss-num:nth-child(3){border-left:none;padding-left:0}.ss-num:nth-child(n+3){border-top:1px solid var(--line)}}
/* honest story */
.ss-story{border:1px solid var(--line);border-radius:6px;background:var(--s1);padding:64px 56px;display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:56px;align-items:end}
.ss-quote{font-family:var(--display);font-weight:600;font-size:clamp(30px,3.4vw,52px);line-height:1.06;letter-spacing:-.035em;color:var(--tx)}
.ss-quote span{color:var(--red)}
.ss-quote em{font-style:normal;color:var(--dim)}
.ss-story ul{list-style:none;padding:0;margin:0;border-top:1px solid var(--line)}
.ss-story li{padding:14px 0;border-bottom:1px solid var(--line);font-size:15px;line-height:1.55;color:var(--mu);margin:0;display:grid;grid-template-columns:28px 1fr}
.ss-story li::before{content:"+";font-family:var(--mono);color:var(--lime)}
@media (max-width:1000px){.ss-story{grid-template-columns:1fr;padding:36px 24px;gap:32px}}
/* AMD block */
.ss-amd{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.ss-amd-l{padding:48px;background:var(--lime);color:#0A0B0C;display:flex;flex-direction:column;justify-content:space-between;gap:56px}
.ss-amd-l .ss-eb{color:#0A0B0C}
.ss-amd-h{font-family:var(--display);font-weight:600;font-size:clamp(34px,3.6vw,56px);line-height:1;letter-spacing:-.04em}
.ss-amd-l p{font-size:15px;line-height:1.6;max-width:440px;margin:0;color:#1E2410}
.ss-amd-r{background:var(--s1)}
.ss-spec{display:grid;grid-template-columns:150px minmax(0,1fr);gap:16px;padding:20px 32px;border-bottom:1px solid var(--line);font-size:15px;color:var(--tx)}
.ss-spec:last-child{border-bottom:none}
.ss-spec span{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);padding-top:3px}
@media (max-width:900px){.ss-amd{grid-template-columns:1fr}.ss-amd-l{padding:32px 24px}.ss-spec{grid-template-columns:1fr;gap:4px;padding:16px 24px}}
/* final CTA */
.ss-final{text-align:left;padding:120px 0 26px;border-top:1px solid var(--line);margin-top:110px}
.ss-final-h{font-family:var(--display);font-weight:600;font-size:clamp(48px,8vw,128px);line-height:.88;letter-spacing:-.055em;color:var(--tx)}
.ss-final-h span{color:var(--lime)}
/* footer */
.ss-footer{margin-top:40px;border-top:1px solid var(--line);padding-top:48px}
.ss-foot-grid{display:grid;grid-template-columns:minmax(0,1.4fr) repeat(3,minmax(0,1fr));gap:40px}
.ss-foot-grid p{font-size:14px;line-height:1.6;color:var(--mu);max-width:340px;margin:14px 0 0}
.ss-foot-h{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:14px}
.ss-foot-grid a{display:block;color:var(--tx)!important;text-decoration:none;font-size:14.5px;padding:5px 0}
.ss-foot-grid a:hover{color:var(--lime)!important}
.ss-foot-grid .ss-foot-plain{font-size:14.5px;color:var(--mu);padding:5px 0}
.ss-foot-word{font-family:var(--display);font-weight:600;font-size:clamp(64px,16.5vw,260px);line-height:.8;letter-spacing:-.065em;color:var(--s3);margin:72px 0 0 -8px;white-space:nowrap;user-select:none}
.ss-foot-bottom{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-top:1px solid var(--line);padding:18px 0 8px;margin-top:10px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--dim);text-transform:uppercase}
@media (max-width:900px){.ss-foot-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
/* method page tables */
.ss-pagehead{padding:46px 0 34px;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:48px;align-items:end}
.ss-pagehead-h{font-family:var(--display);font-weight:600;font-size:clamp(40px,5vw,76px);line-height:.98;letter-spacing:-.045em;color:var(--tx);margin-top:18px}
.ss-pagehead-h span{color:var(--dim)}
@media (max-width:900px){.ss-pagehead{grid-template-columns:1fr;gap:18px;padding:30px 0 22px}}
.ss-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border:1px solid var(--line);border-radius:4px;background:var(--s1)}
.ss-flow-c{padding:22px 20px 26px;border-left:1px solid var(--line);position:relative}
.ss-flow-c:first-child{border-left:none}
.ss-flow-c.is-amd{background:var(--lime-d);box-shadow:inset 0 2px 0 var(--lime)}
.ss-flow-n{font-family:var(--mono);font-size:11px;color:var(--lime);letter-spacing:.08em}
.ss-flow-h{font-family:var(--display);font-weight:600;font-size:19px;letter-spacing:-.015em;color:var(--tx);margin:30px 0 8px}
.ss-flow-p{font-size:13.5px;line-height:1.55;color:var(--mu)}
.ss-flow-c:not(:last-child)::after{content:"→";position:absolute;right:-9px;top:22px;font-family:var(--mono);font-size:13px;color:var(--dim);background:var(--bg);padding:0 2px;z-index:1}
@media (max-width:1000px){.ss-flow{grid-template-columns:1fr}.ss-flow-c{border-left:none;border-top:1px solid var(--line)}.ss-flow-c:first-child{border-top:none}.ss-flow-c::after{display:none}}
.ss-row-prod td{background:var(--lime-d)!important}
"""


def style_tag() -> str:
    return f"<style>{CSS}</style>"


# --- navbar / footer ---------------------------------------------------------------------

def nav_brand() -> str:
    return f'<div class="ss-nav-brand">{LOGO}<span>Shelf-Sense</span><small>Shelf inspection</small></div>'


def marquee(items: list[str], dark: bool = False) -> str:
    spans = "".join(f'<span class="ss-marquee-item">{esc(i)}</span>' for i in items)
    cls = "ss-marquee ss-marquee--dark" if dark else "ss-marquee"
    return f'<div class="{cls}" aria-hidden="true"><div class="ss-marquee-track">{spans}{spans}</div></div>'


def footer() -> str:
    return (
        f'<div class="ss-footer"><div class="ss-foot-grid"><div>{nav_brand()}'
        '<p>Shelf compliance from one photograph. A vision model on AMD Developer Cloud counts; code decides, '
        'and every dollar figure is labelled for what it is.</p></div>'
        '<div><div class="ss-foot-h">Product</div><a href="/" target="_self">Overview</a>'
        '<a href="/inspect" target="_self">Dashboard</a><a href="/how-it-works" target="_self">How it works</a></div>'
        f'<div><div class="ss-foot-h">Project</div><a href="{REPO_URL}" target="_blank" rel="noopener">Source on GitHub</a>'
        f'<a href="{REPO_URL}/tree/main/docs/experiments" target="_blank" rel="noopener">Experiment records</a>'
        f'<a href="{REPO_URL}/blob/main/LICENSE" target="_blank" rel="noopener">MIT licence</a></div>'
        '<div><div class="ss-foot-h">Built with</div><div class="ss-foot-plain">AMD Developer Cloud · Token Factory</div>'
        '<div class="ss-foot-plain">Gemma-4-31B-IT</div><div class="ss-foot-plain">Python · Streamlit · Pydantic</div></div></div>'
        '<div class="ss-foot-word" aria-hidden="true">Shelf-Sense</div>'
        '<div class="ss-foot-bottom"><span>© 2026 Shelf-Sense · MIT licence</span>'
        '<span>AMD Developer Hackathon: ACT III · Reinvent Commerce</span></div></div>'
    )


# --- landing ----------------------------------------------------------------------------

def hero_top() -> str:
    return (
        '<div class="ss-hero2"><div class="ss-hero2-top"><span class="ss-eb">[ Retail shelf compliance ]</span>'
        '<span class="ss-eb-dim">AMD Developer Hackathon · ACT III</span></div>'
        '<div class="ss-wordmark" role="heading" aria-level="1">Shelf<span>-</span>Sense</div></div>'
    )


def hero_lede() -> str:
    return (
        '<div class="ss-hero2-lede">Photograph a shelf. Get per-product counts, a compliance verdict, an estimated '
        'margin at risk and a restocking list. <span>The vision model counts on AMD Developer Cloud; '
        'code makes every decision.</span></div>'
    )


def product_frame() -> str:
    return (
        '<div class="ss-crosshair-row"><span>[ 0, 0 ]</span><span>Dashboard · real inspection, compliant.png</span>'
        '<span>[ 1440, 900 ]</span></div>'
        '<div class="ss-frame"><div class="ss-frame-bar"><span><b>shelf-sense</b> / inspect</span>'
        '<span>Gemma-4-31B-IT · AMD Token Factory</span></div>'
        '<img src="/app/static/product.jpg" alt="Shelf-Sense dashboard showing a real inspection: overall status '
        'non-compliant, estimated margin at risk $1.00 marked unverified, and per-product results with per-shelf counts" '
        'loading="lazy"></div>'
    )


LANDING_MARQUEE = [
    "Shelf-by-shelf counting", "Code-computed verdicts", "Estimated margin at risk", "Labelled unverified",
    "Gemma-4-31B-IT", "AMD Developer Cloud", "One call per inspection", "No invented numbers",
]

FOOT_MARQUEE = [
    f"{FACTS['error_before']} → {FACTS['error_after']} box counting error after the shelf-by-shelf prompt",
    f"{FACTS['median_latency_s']} s median inspection",
    f"{FACTS['experiment_records']} experiment records with raw replies",
    "MIT licensed", "Self-taken photos only", "Model confidence is never trusted",
]

_ICONS = {
    "manual": '<svg viewBox="0 0 88 88" fill="none" stroke="#6C7177" stroke-width="1.2"><rect x="22" y="14" width="44" height="60" rx="2"/><path d="M32 30h24M32 40h24M32 50h14"/><rect x="36" y="8" width="16" height="10" rx="1" stroke="#CDFF3F"/></svg>',
    "infrequent": '<svg viewBox="0 0 88 88" fill="none" stroke="#6C7177" stroke-width="1.2"><circle cx="44" cy="44" r="30"/><path d="M44 24v20l13 8" stroke="#CDFF3F"/><path d="M14 44h6M68 44h6M44 14v6M44 68v6"/></svg>',
    "inconsistent": '<svg viewBox="0 0 88 88" fill="none" stroke="#6C7177" stroke-width="1.2"><rect x="12" y="22" width="28" height="44" rx="2"/><rect x="48" y="22" width="28" height="44" rx="2"/><path d="M20 36h12M20 46h12M56 36h12M56 46h6" /><path d="M40 44h8" stroke="#CDFF3F"/></svg>',
    "unpriced": '<svg viewBox="0 0 88 88" fill="none" stroke="#6C7177" stroke-width="1.2"><path d="M14 66h60M22 66V40M38 66V28M54 66V48M70 66V20"/><circle cx="54" cy="40" r="5" stroke="#CDFF3F"/></svg>',
}


def problem_section() -> str:
    cols = [
        ("01", "manual", "Manual", "Every count is a person with a clipboard.",
         "Checking a bay means walking it, counting facings and writing them down."),
        ("02", "infrequent", "Infrequent", "Gaps sit unnoticed between walks.",
         "A missing facing can stay missing until the next scheduled check."),
        ("03", "inconsistent", "Inconsistent", "Two people, two different counts.",
         "Half-hidden boxes, variants and edge cases are judged differently each time."),
        ("04", "unpriced", "Unpriced", "Nobody knows what the gap costs.",
         "Without a number attached, restocking competes with everything else."),
    ]
    cells = "".join(
        f'<div class="ss-col"><div class="ss-col-top"><span>{esc(tag)}</span><span>[{n}]</span></div>{_ICONS[icon]}'
        f'<div class="ss-col-h">{esc(h)}</div><div class="ss-col-p">{esc(p)}</div></div>'
        for n, icon, tag, h, p in cols
    )
    return (
        '<div class="ss-sec"><div class="ss-sec-head"><div><span class="ss-eb">[01] The problem</span>'
        '<div class="ss-sec-h">Shelves are still<br><span>checked by eye.</span></div></div>'
        '<div class="ss-sec-lede">Missing facings quietly cost margin. Manual shelf walks are slow and inconsistent, '
        'and small stores can’t justify dedicated shelf-scanning hardware.</div></div>'
        f'<div class="ss-cols4">{cells}</div></div>'
    )


def how_section() -> str:
    steps = [
        ("01", "Photograph", "Any phone photo of the bay. It is EXIF-rotated and resized to <code>≤1024 px</code> before it leaves the server."),
        ("02", "Count on AMD", "Gemma-4-31B-IT on AMD Developer Cloud counts each product shelf by shelf, top to bottom, and reports per-shelf numbers."),
        ("03", "Decide in code", "Pydantic validation, the compliance verdict and the margin estimate are plain Python. The model never sets a status or a number."),
        ("04", "Act", "A restocking list in plain language. If AMD words it, code still inserts every name, count and figure; if not, a template does."),
    ]
    rows = "".join(
        f'<div class="ss-step"><div class="ss-step-n">{n}</div><div><div class="ss-step-h">{esc(h)}</div>'
        f'<div class="ss-step-p">{p}</div></div></div>'
        for n, h, p in steps
    )
    return (
        '<div class="ss-sec"><div class="ss-sec-head"><div><span class="ss-eb">[02] How it works</span>'
        '<div class="ss-sec-h">One photo in.<br><span>A decision out.</span></div></div>'
        '<div class="ss-sec-lede">One vision call per inspection. Everything that turns counts into a decision runs '
        'in code you can read, test and audit.</div></div>'
        '<div class="ss-how"><div class="ss-frame"><div class="ss-frame-bar"><span><b>compliant.png</b> · input</span>'
        '<span>4 shelves · self-taken</span></div><img src="/app/static/shelf.jpg" alt="Self-taken photo of a fully '
        'stocked cereal bay with four shelves" loading="lazy"></div>'
        f'<div class="ss-how-steps">{rows}</div></div></div>'
    )


def features_section() -> str:
    feats = [
        ("Per-shelf counts", "Every product is counted shelf by shelf, so a person can check the model in seconds: 6 / 5 / 3 / 2."),
        ("A verdict computed by code", "Compliant, non-compliant or needs review, decided from per-product statuses, never by the model."),
        ("Estimated margin at risk", "Missing and partial units × unit margin, always labelled unverified; unresolved items kept separate."),
        ("Discrepancies at a glance", "Shortfalls and overcounts against the spec, highlighted row by row."),
        ("A restocking list", "Plain-language actions, with a label saying whether AMD or the template wrote them."),
        ("Full transparency", "Model, endpoint, latency and real-versus-mock are on every result."),
    ]
    rows = "".join(
        f'<div class="ss-feat-row"><span>[{n:02d}]</span><b>{esc(h)}</b><p>{esc(p)}</p></div>'
        for n, (h, p) in enumerate(feats, 1)
    )
    return (
        '<div class="ss-sec"><div class="ss-feat"><div><div style="border-top:1px solid var(--line);padding-top:22px">'
        '<span class="ss-eb">[03] What you get</span><div class="ss-sec-h">Built for the<br><span>store floor.</span></div>'
        '<div class="ss-sec-lede" style="margin-top:22px">A store manager should understand the result in under ten '
        'seconds: status first, then the money, then the detail.</div></div></div>'
        f'<div class="ss-feat-rows">{rows}</div></div></div>'
    )


def evidence_section() -> str:
    f = FACTS
    return (
        '<div class="ss-sec"><div class="ss-sec-head"><div><span class="ss-eb">[04] Evidence</span>'
        '<div class="ss-sec-h">Measured,<br><span>not asserted.</span></div></div>'
        '<div class="ss-sec-lede">We tested against a hand-counted shelf: 16 Stars, 8 Koko Krunch, 4 Milo, 4 Trix. '
        'Every run, with the model’s raw reply, is in the repository.</div></div>'
        '<div class="ss-nums">'
        f'<div class="ss-num"><div class="ss-num-v">{f["error_before"]}<small>→</small>{f["error_after"]}</div>'
        '<div class="ss-num-k">Boxes of counting error, before and after the shelf-by-shelf prompt.</div></div>'
        f'<div class="ss-num"><div class="ss-num-v">{esc(f["median_latency_s"])}<small>s</small></div>'
        f'<div class="ss-num-k">Median inspection on AMD Token Factory ({f["production_runs"]} recorded runs, '
        f'{esc(f["latency_range"])}).</div></div>'
        f'<div class="ss-num"><div class="ss-num-v">{f["experiment_records"]}</div>'
        '<div class="ss-num-k">Experiment records: prompts, resolution, a second model and per-shelf cropping.</div></div>'
        '<div class="ss-num"><div class="ss-num-v">0<small>/9</small></div>'
        '<div class="ss-num-k">Production runs that got this fully stocked shelf right. We say so.</div></div></div>'
        '<div class="ss-src-note">Source: docs/experiments/ · one self-taken photo · a case study, not a benchmark.</div></div>'
    )


def honest_section() -> str:
    return (
        '<div class="ss-sec"><div class="ss-story"><div><span class="ss-eb">[05] Honest by design</span>'
        '<div class="ss-quote" style="margin-top:24px">The model counted <span>7</span> Koko Krunch boxes. '
        'There were 8. <em>It said it was 100% sure.</em></div></div>'
        '<ul><li>Every dollar figure is labelled “Estimated Margin at Risk (Unverified)”.</li>'
        '<li>Counts the model flags as unreliable, or that don’t add up, go to review instead of the estimate.</li>'
        '<li>Per-shelf counts are shown, so the miss is visible: shelf 2 says 1, not 2.</li>'
        '<li>Model confidence is displayed, never trusted.</li></ul></div></div>'
    )


def amd_section() -> str:
    specs = [
        ("Model", "Gemma-4-31B-IT, vision input"),
        ("Endpoint", "AMD Developer Cloud Token Factory, OpenAI-compatible chat completions"),
        ("Calls", "1 vision call per inspection, plus 1 text call to word the actions"),
        ("Latency", f"{FACTS['median_latency_s']} s median, {FACTS['latency_range']} on the shared endpoint"),
        ("Evidence", "First raw HTTP 200 and every experiment reply kept in the repository"),
        ("Not claimed", "We call the hosted service; we don’t claim a serving stack or GPU"),
    ]
    rows = "".join(f'<div class="ss-spec"><span>{esc(k)}</span><div>{esc(v)}</div></div>' for k, v in specs)
    return (
        '<div class="ss-sec"><div class="ss-amd"><div class="ss-amd-l"><span class="ss-eb">[06] Inference</span>'
        '<div><div class="ss-amd-h">Every inspection<br>runs on AMD.</div></div>'
        '<p>There is no other model provider in the real path. Mock mode exists for offline development only and is '
        'labelled on every screen it touches.</p></div>'
        f'<div class="ss-amd-r">{rows}</div></div></div>'
    )


def final_cta() -> str:
    return '<div class="ss-final"><span class="ss-eb">[ Get started ]</span><div class="ss-final-h" style="margin-top:22px">Check a shelf<br><span>in a minute.</span></div></div>'


# --- How it works page ---------------------------------------------------------------------

def method_head() -> str:
    return (
        '<div class="ss-pagehead"><div><span class="ss-eb">[ Method &amp; evidence ]</span>'
        '<div class="ss-pagehead-h" role="heading" aria-level="1">How Shelf-Sense<br><span>decides.</span></div></div>'
        '<div class="ss-sec-lede">The model observes; code decides. This page shows the pipeline, how the money is '
        'calculated, what we measured and what we don’t claim.</div></div>'
    )


def method_flow() -> str:
    cells = [
        ("01", "Photo + spec", "EXIF-rotated, resized to ≤1024 px. The spec is sent as text, without prices.", False),
        ("02", "AMD Token Factory", "Gemma-4-31B-IT counts each product shelf by shelf and returns JSON.", True),
        ("03", "Validation", "Schema check, one stricter retry, invented items dropped, unreliable counts to review.", False),
        ("04", "Calculator", "Verdict and margin estimate in plain Python, Decimal arithmetic.", False),
        ("05", "Action note", "Template, optionally reworded by AMD. Numbers are always inserted by code.", False),
    ]
    html = "".join(
        f'<div class="ss-flow-c{" is-amd" if amd else ""}"><div class="ss-flow-n">[{n}]</div>'
        f'<div class="ss-flow-h">{esc(h)}</div><div class="ss-flow-p">{esc(p)}</div></div>'
        for n, h, p, amd in cells
    )
    return _sec("[01] Pipeline", "Five steps,<br><span>one model call.</span>",
                "Every product name, count, status and dollar figure the user sees is rendered by code.",
                f'<div class="ss-flow">{html}</div>')


def method_money() -> str:
    rows = [
        ("Estimated Margin at Risk (Unverified)", "Missing: expected units × unit margin. Partial: (expected − detected) × unit margin. From AI-estimated counts; always labelled unverified."),
        ("Unresolved Potential Exposure (Upper Bound)", "Misplaced, needs-review or contradictory items: excluded from the estimate, shown separately as an upper bound."),
        ("Unavailable", "A missing or invalid unit value is reported as unavailable, never as $0; the estimate becomes “at least”."),
        ("Verified", "Only counts checked by a person. Nothing in the app produces this yet, so no figure is ever shown as verified."),
    ]
    body = "".join(f'<tr><td class="ss-prod">{esc(k)}</td><td>{esc(v)}</td></tr>' for k, v in rows)
    table = ('<div class="ss-table-wrap"><table class="ss-table"><thead><tr><th style="width:34%">Shown as</th>'
             f'<th>Meaning</th></tr></thead><tbody>{body}</tbody></table></div>'
             '<div class="ss-hint">Demo unit margins are a flat $1.00 per unit: an author-entered assumption, not point-of-sale data.</div>')
    return _sec("[02] The money", "A figure that admits<br><span>what it doesn’t know.</span>",
                "An estimate of $0.00 is never shown as “no action required” while unresolved items remain.", table)


def method_evaluation() -> str:
    rows = [
        ("Baseline", "First prompt", "1 of 4", "8", "0 of 2", False),
        ("1 · production", "Shelf-by-shelf counting prompt", "3 of 4", "1", "0 of 3", True),
        ("2", "1536 px instead of 1024 (incl. replication)", "3 of 4", "1", "0 of 6", False),
        ("3", "MiniCPM-V-4.7-35B-A3B instead of Gemma", "3 of 4", "1", "0 of 2", False),
        ("4", "One image per shelf (hand-placed crops)", "2–3 of 4", "2–3", "3 of 3", False),
    ]
    prod_cls = ' class="ss-row-prod"'
    body = "".join(
        f'<tr{prod_cls if prod else ""}><td class="ss-prod">{esc(a)}</td><td>{esc(b)}</td>'
        f'<td class="num">{esc(c)}</td><td class="num">{esc(d)}</td><td class="num">{esc(e)}</td></tr>'
        for a, b, c, d, e, prod in rows
    )
    table = ('<div class="ss-table-wrap"><table class="ss-table"><thead><tr><th>Experiment</th><th>Change</th>'
             '<th class="num">Exact counts</th><th class="num">Count error (boxes)</th><th class="num">Shelf correct</th>'
             f'</tr></thead><tbody>{body}</tbody></table></div>'
             '<div class="ss-hint">Production misses one half-hidden Koko Krunch box in every recorded run, at 100% model '
             'confidence. Per-shelf cropping found it but overcounted neighbours and needs four calls, so it was not adopted. '
             'Source: docs/experiments/.</div>')
    return _sec("[03] Evaluation", "One shelf,<br><span>counted by hand.</span>",
                "Ground truth: Stars 16, Koko Krunch 8, Milo 4, Trix 4. A single-image case study, not a benchmark.", table)


def method_limits() -> str:
    items = [
        "The model misses partly hidden packages, and its confidence doesn’t reveal it.",
        "One evaluated photo so far.",
        "Stock-out and misplaced scenarios need their own specs and ground truth.",
        "Specs are written by hand; there is no placement field yet.",
        "Unit margins are demo assumptions, not point-of-sale data.",
        "Latency on the shared endpoint varies widely (11.7–45.8 s per inspection).",
    ]
    lis = "".join(f"<li>{esc(i)}</li>" for i in items)
    return _sec("[04] Limits", "What we<br><span>don’t claim.</span>",
                "Known limits, stated plainly, so a judge or a store manager knows exactly what they’re getting.",
                f'<div class="ss-story" style="padding:36px 40px;grid-template-columns:1fr"><ul>{lis}</ul></div>')


def _sec(eyebrow: str, heading_html: str, lede: str, body: str) -> str:
    return (f'<div class="ss-sec" style="padding-top:72px"><div class="ss-sec-head"><div><span class="ss-eb">{esc(eyebrow)}</span>'
            f'<div class="ss-sec-h">{heading_html}</div></div><div class="ss-sec-lede">{esc(lede)}</div></div>{body}</div>')
