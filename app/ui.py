"""Presentation layer for the Streamlit UI: the stylesheet and pure HTML builders.

Every function returns an HTML string for st.markdown(..., unsafe_allow_html=True). Nothing here
computes business values: figures come from the validated models via app.presenters. Every piece
of text that comes from a user, a spec file or the model goes through esc().

HTML is emitted without blank lines or leading indentation, because Streamlit runs it through a
Markdown parser first (an indented line would become a code block).
"""

import html

from app import presenters
from app.models import ActionNote, ComplianceResult, ExposureSummary, Spec

STATUS_KIND = {"present": "ok", "partial": "warn", "missing": "bad", "misplaced": "info", "needs_review": "warn"}
OVERALL_KIND = {"compliant": "ok", "non_compliant": "bad", "needs_review": "warn"}

FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
    "&family=Inter+Tight:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
)


def esc(value) -> str:
    """HTML-escape, and encode '$' so Streamlit's Markdown never reads dollar amounts as LaTeX."""
    return html.escape(str(value), quote=True).replace("$", "&#36;")


def _join(*parts: str) -> str:
    return "".join(p for p in parts if p)


# --- stylesheet --------------------------------------------------------------------

CSS = """
:root{--bg:#0A0B0C;--s1:#101214;--s2:#15181A;--s3:#1B1F22;--line:#23272A;--line2:#31363A;
--tx:#ECEBE6;--mu:#9DA2A8;--dim:#6C7177;--lime:#CDFF3F;--lime-d:rgba(205,255,63,.09);
--amber:#F2B24B;--amber-d:rgba(242,178,75,.08);--red:#FF6B57;--red-d:rgba(255,107,87,.08);
--blue:#93B4FF;--blue-d:rgba(147,180,255,.08);
--mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
--display:'Inter Tight','Inter',system-ui,-apple-system,sans-serif;
--sans:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}
.stApp{background-color:var(--bg);color:var(--tx);font-family:var(--sans);
background-image:linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);
background-size:88px 88px;background-attachment:fixed}
[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1520px;padding:26px 44px 80px}
@media (max-width:760px){.block-container,[data-testid="stMainBlockContainer"]{padding:18px 16px 60px}}
.stMarkdown p,.stMarkdown li{color:var(--tx)}
/* header */
.ss-top{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:2px 0 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.ss-brand{display:flex;align-items:center;gap:12px;font-family:var(--display);font-weight:600;font-size:21px;letter-spacing:-.015em;color:var(--tx)}
.ss-brand svg{width:24px;height:24px;flex:none}
.ss-tag{font-family:var(--mono);font-size:11px;font-weight:400;letter-spacing:.08em;text-transform:uppercase;color:var(--mu);border:1px solid var(--line2);padding:3px 7px;border-radius:2px}
.ss-engine{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:12px;letter-spacing:.03em;color:var(--mu);flex-wrap:wrap}
.ss-engine b{color:var(--tx);font-weight:500}
.ss-sep{color:var(--line2)}
.ss-dot{width:7px;height:7px;border-radius:50%;display:inline-block;background:var(--lime);flex:none}
.ss-dot--warn{background:var(--amber)}.ss-dot--bad{background:var(--red)}
.ss-hero{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:56px;align-items:end;padding:34px 0 30px}
.ss-eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--lime);margin-bottom:20px}
.ss-h1{font-family:var(--display);font-weight:600;font-size:clamp(38px,4.4vw,64px);line-height:1;letter-spacing:-.04em;color:var(--tx)}
.ss-h1 span{color:var(--dim)}
.ss-lede{font-size:16px;line-height:1.65;color:var(--mu);max-width:540px}
.ss-lede b{color:var(--tx);font-weight:500}
.ss-coords{display:flex;gap:28px;margin-top:22px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--dim);text-transform:uppercase;flex-wrap:wrap}
.ss-coords b{color:var(--tx);font-weight:500}
@media (max-width:900px){.ss-hero{grid-template-columns:1fr;gap:18px;padding:28px 0 24px}}
/* panels (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] > [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > .ss-panel-mark){background:var(--s1);border:1px solid var(--line)!important;border-radius:6px;padding:26px 26px 28px!important}
.ss-panel-mark{display:none}
.ss-section{display:flex;align-items:center;gap:12px;margin:2px 0 6px}
.ss-idx{font-family:var(--mono);font-size:11px;color:var(--lime);letter-spacing:.06em;border:1px solid rgba(205,255,63,.35);padding:2px 6px;border-radius:2px}
.ss-sec-title{font-family:var(--display);font-size:22px;font-weight:600;letter-spacing:-.02em;color:var(--tx);white-space:nowrap}
.ss-rule{flex:1;height:1px;background:var(--line)}
.ss-aside{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.05em;text-transform:uppercase;white-space:nowrap}
.ss-label{font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--mu);margin:18px 0 8px;display:flex;justify-content:space-between;gap:12px}
.ss-label span{color:var(--dim)}
.ss-hint{font-family:var(--mono);font-size:11.5px;color:var(--dim);letter-spacing:.02em;line-height:1.6;margin-top:8px}
.ss-meta-line{font-size:13px;color:var(--mu);margin:2px 0 12px}
.ss-meta-line code{font-family:var(--mono);font-size:12px;color:var(--tx);background:var(--s3);padding:2px 6px;border-radius:2px}
/* tables */
div.ss-table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:4px;background:var(--s1)}
div.ss-table-wrap table.ss-table{width:100%;border-collapse:collapse;font-size:14px;margin:0;border:none}
div.ss-table-wrap table.ss-table th{font-family:var(--mono);font-size:10.5px;font-weight:500;letter-spacing:.09em;text-transform:uppercase;color:var(--dim);text-align:left;padding:11px 12px;border:none;border-bottom:1px solid var(--line);background:var(--s2);white-space:nowrap}
div.ss-table-wrap table.ss-table td{padding:12px 12px;border:none;border-bottom:1px solid var(--line);color:var(--tx);vertical-align:middle;background:transparent}
div.ss-table-wrap table.ss-table tr:last-child td{border-bottom:none}
div.ss-table-wrap table.ss-table .num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
div.ss-table-wrap table.ss-table th.num{text-align:right}
div.ss-table-wrap table.ss-table td.muted{color:var(--dim)}
div.ss-table-wrap table.ss-table tr.is-warn td:first-child{box-shadow:inset 2px 0 0 var(--amber)}
div.ss-table-wrap table.ss-table tr.is-bad td:first-child{box-shadow:inset 2px 0 0 var(--red)}
div.ss-table-wrap table.ss-table tr.is-info td:first-child{box-shadow:inset 2px 0 0 var(--blue)}
div.ss-table-wrap table.ss-table tbody tr:hover td{background:rgba(255,255,255,.018)}
.ss-prod{font-weight:500}
table.ss-results td.ss-prod{min-width:190px}
.ss-delta-neg{color:var(--amber)}.ss-delta-pos{color:var(--blue)}.ss-delta-zero{color:var(--dim)}
.ss-shelves{font-family:var(--mono);font-size:12.5px;color:var(--mu);white-space:nowrap}
.ss-shelves b{color:var(--tx);font-weight:500}
/* badges */
.ss-badge{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:10.5px;font-weight:500;letter-spacing:.07em;text-transform:uppercase;padding:4px 8px 4px 7px;border:1px solid;border-radius:2px;white-space:nowrap;line-height:1.2}
.ss-badge::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;flex:none}
.ss-badge--ok{color:var(--lime);border-color:rgba(205,255,63,.32);background:var(--lime-d)}
.ss-badge--warn{color:var(--amber);border-color:rgba(242,178,75,.35);background:var(--amber-d)}
.ss-badge--bad{color:var(--red);border-color:rgba(255,107,87,.38);background:var(--red-d)}
.ss-badge--info{color:var(--blue);border-color:rgba(147,180,255,.35);background:var(--blue-d)}
/* verdict + stats */
.ss-verdict{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;padding:6px 0 18px}
.ss-verdict-k{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--mu);margin-bottom:10px}
.ss-verdict-v{display:flex;align-items:center;gap:14px;font-family:var(--display);font-size:clamp(30px,3.2vw,44px);font-weight:600;letter-spacing:-.03em;line-height:1}
.ss-verdict-v .ss-dot{width:12px;height:12px}
.ss-verdict--ok .ss-verdict-v{color:var(--lime)}.ss-verdict--bad .ss-verdict-v{color:var(--red)}.ss-verdict--warn .ss-verdict-v{color:var(--amber)}
.ss-run-meta{font-family:var(--mono);font-size:11.5px;color:var(--mu);letter-spacing:.03em;text-align:right;line-height:1.7}
@media (max-width:640px){.ss-run-meta{text-align:left}}
.ss-run-meta b{color:var(--tx);font-weight:500}
.ss-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--s1)}
.ss-stat{padding:18px 18px 14px;border-left:1px solid var(--line);display:flex;flex-direction:column;gap:12px;min-width:0}
.ss-stat:first-child{border-left:none}
.ss-stat-k{flex:1;font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--mu);line-height:1.45}
.ss-stat-v{font-family:var(--display);font-size:clamp(26px,2.4vw,36px);font-weight:600;letter-spacing:-.025em;line-height:1;font-variant-numeric:tabular-nums;color:var(--tx);overflow-wrap:anywhere}
.ss-stat-v small{font-size:.5em;color:var(--mu);font-weight:500;letter-spacing:0}
.ss-stat--est{background:var(--amber-d);box-shadow:inset 0 2px 0 var(--amber)}
.ss-stat-flag{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--amber);text-transform:uppercase;min-height:28px;line-height:1.4}
@media (max-width:1180px){.ss-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.ss-stat:nth-child(3){border-left:none}.ss-stat:nth-child(n+3){border-top:1px solid var(--line)}}
/* notices */
.ss-notice{display:flex;gap:16px;align-items:flex-start;padding:13px 16px;border:1px solid var(--line);border-left:2px solid var(--amber);background:var(--amber-d);border-radius:3px;font-size:14px;line-height:1.55;color:var(--tx);margin:10px 0}
.ss-notice-tag{flex:none;font-family:var(--mono);font-size:10.5px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:var(--amber);white-space:nowrap;padding-top:3px;min-width:112px}
.ss-notice-detail{display:block;font-family:var(--mono);font-size:12px;color:var(--mu);margin-top:6px;overflow-wrap:anywhere}
.ss-notice--bad{border-left-color:var(--red);background:var(--red-d)}.ss-notice--bad .ss-notice-tag{color:var(--red)}
.ss-notice--info{border-left-color:var(--blue);background:var(--blue-d)}.ss-notice--info .ss-notice-tag{color:var(--blue)}
.ss-notice--plain{border-left-color:var(--line2);background:var(--s2)}.ss-notice--plain .ss-notice-tag{color:var(--mu)}
@media (max-width:640px){.ss-notice{flex-direction:column;gap:6px}}
/* discrepancies */
.ss-disc{border:1px solid var(--line);border-radius:4px;background:var(--s1)}
.ss-disc-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:16px;align-items:center;padding:12px 16px;border-top:1px solid var(--line);font-size:14px}
.ss-disc-row:first-child{border-top:none}
.ss-disc-n{font-family:var(--mono);font-size:12.5px;color:var(--mu);font-variant-numeric:tabular-nums;white-space:nowrap}
.ss-disc-none{padding:14px 16px;font-size:14px;color:var(--mu)}
/* empty / processing */
.ss-empty{position:relative;border:1px dashed var(--line2);border-radius:4px;padding:56px 44px;min-height:470px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(255,255,255,.012),transparent)}
.ss-corner{position:absolute;width:12px;height:12px;border-color:var(--mu);border-style:solid}
.ss-corner.tl{top:-1px;left:-1px;border-width:1px 0 0 1px}.ss-corner.tr{top:-1px;right:-1px;border-width:1px 1px 0 0}
.ss-corner.bl{bottom:-1px;left:-1px;border-width:0 0 1px 1px}.ss-corner.br{bottom:-1px;right:-1px;border-width:0 1px 1px 0}
.ss-empty-tag{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--lime);text-transform:uppercase;margin-bottom:18px}
.ss-empty-title{font-family:var(--display);font-size:clamp(28px,2.8vw,40px);font-weight:600;letter-spacing:-.03em;color:var(--tx);line-height:1.05;margin-bottom:14px}
.ss-empty-copy{font-size:15px;line-height:1.65;color:var(--mu);max-width:520px}
.ss-steps{list-style:none;padding:0;margin:30px 0 0;display:grid;gap:0;border-top:1px solid var(--line);max-width:560px}
.ss-steps li{display:flex;gap:18px;padding:12px 0;border-bottom:1px solid var(--line);font-size:14px;color:var(--tx);margin:0}
.ss-steps li span{font-family:var(--mono);font-size:11px;color:var(--dim);padding-top:3px}
.ss-proc{border:1px solid var(--line);border-radius:4px;padding:40px 40px 34px;background:var(--s1);min-height:360px}
.ss-proc-head{display:flex;align-items:center;gap:12px;font-family:var(--display);font-size:28px;font-weight:600;letter-spacing:-.025em;color:var(--tx)}
.ss-proc-sub{font-family:var(--mono);font-size:12px;color:var(--mu);margin:10px 0 26px;letter-spacing:.02em}
.ss-bar{height:2px;background:var(--line);overflow:hidden;position:relative;border-radius:2px}
.ss-bar span{position:absolute;top:0;left:-30%;width:30%;height:100%;background:var(--lime);animation:ss-slide 1.6s cubic-bezier(.6,0,.4,1) infinite}
@keyframes ss-slide{0%{left:-30%}100%{left:100%}}
.ss-pulse{animation:ss-pulse 1.4s ease-in-out infinite}
@keyframes ss-pulse{0%,100%{opacity:1}50%{opacity:.25}}
@media (prefers-reduced-motion:reduce){.ss-bar span,.ss-pulse{animation:none}.ss-bar span{left:0;width:100%;opacity:.4}}
/* actions */
.ss-actions{border:1px solid var(--line);border-radius:4px;background:var(--s1);overflow:hidden}
.ss-actions-head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid var(--line);background:var(--s2);flex-wrap:wrap}
.ss-actions-title{font-family:var(--display);font-size:18px;font-weight:600;letter-spacing:-.015em}
.ss-src{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;padding:4px 8px;border:1px solid var(--line2);border-radius:2px;color:var(--mu);white-space:nowrap}
.ss-src--amd{color:var(--lime);border-color:rgba(205,255,63,.32)}
.ss-src--bad{color:var(--red);border-color:rgba(255,107,87,.38)}
.ss-actions-body{padding:18px}
.ss-actions-lede{font-size:15px;line-height:1.6;color:var(--tx);margin-bottom:14px}
.ss-actions-lede span{display:block;color:var(--mu)}
.ss-act{display:grid;grid-template-columns:34px minmax(0,1fr);gap:12px;padding:14px 0;border-top:1px solid var(--line)}
.ss-act-n{font-family:var(--mono);font-size:11px;color:var(--lime);padding-top:3px}
.ss-act-prod{font-size:13px;color:var(--mu);margin-bottom:3px}
.ss-act-do{font-size:15px;font-weight:500;color:var(--tx);line-height:1.5}
.ss-act-facts{font-family:var(--mono);font-size:11.5px;color:var(--dim);margin-top:6px;line-height:1.6}
.ss-actions-foot{border-top:1px solid var(--line);padding-top:14px;margin-top:2px;font-size:13.5px;line-height:1.65;color:var(--mu)}
.ss-actions-foot div{margin:2px 0}
.ss-next{margin-top:12px;padding:11px 14px;border:1px solid rgba(205,255,63,.25);background:var(--lime-d);border-radius:3px;font-size:14px;color:var(--tx)}
.ss-next b{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--lime);font-weight:500;margin-right:8px}
.ss-src-caption{font-family:var(--mono);font-size:11px;color:var(--dim);line-height:1.6;padding:12px 18px;border-top:1px solid var(--line)}
/* image */
[data-testid="stImage"] img,[data-testid="stImage"]{border-radius:4px}
[data-testid="stImage"] img{border:1px solid var(--line2)}
.ss-file{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:10px 12px;border:1px solid var(--line);border-radius:3px;background:var(--s2);margin:2px 0 4px}
.ss-file-name{font-family:var(--mono);font-size:12.5px;color:var(--tx);overflow-wrap:anywhere}
.ss-file-meta{font-family:var(--mono);font-size:11px;color:var(--mu);letter-spacing:.03em}
[data-testid="stImageCaption"],[data-testid="caption"]{color:var(--dim)!important;font-family:var(--mono)!important;font-size:11px!important}
/* native widgets */
.stButton>button,[data-testid="stBaseButton-secondary"]{background:var(--s2);color:var(--tx);border:1px solid var(--line2);border-radius:3px;font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:9px 14px;transition:border-color .15s,background .15s}
.stButton>button:hover,[data-testid="stBaseButton-secondary"]:hover{border-color:var(--lime);color:var(--lime);background:var(--s3)}
.stButton>button[kind="primary"],[data-testid="stBaseButton-primary"]{background:var(--lime)!important;color:#0A0B0C!important;border:1px solid var(--lime)!important;font-weight:600;padding:14px 18px;font-size:13px;letter-spacing:.1em}
.stButton>button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{background:#DDFF7A!important;border-color:#DDFF7A!important;color:#0A0B0C!important}
.stButton>button:disabled,[data-testid="stBaseButton-primary"]:disabled{background:var(--s3)!important;color:var(--dim)!important;border-color:var(--line)!important}
.stButton>button:focus-visible{outline:2px solid var(--lime);outline-offset:2px}
[data-baseweb="select"]>div{background:var(--s2)!important;border:1px solid var(--line2)!important;border-radius:3px!important;font-size:14px}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label{font-family:var(--mono)!important;font-size:11px!important;letter-spacing:.09em;text-transform:uppercase;color:var(--mu)!important}
[data-testid="stFileUploaderDropzone"]{background:var(--s2);border:1px dashed var(--line2);border-radius:4px;padding:18px}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--lime)}
[data-testid="stFileUploaderDropzoneInstructions"] span,[data-testid="stFileUploaderDropzoneInstructions"] small{color:var(--mu)}
[data-testid="stExpander"] details{border:1px solid var(--line)!important;border-radius:4px;background:var(--s1)}
[data-testid="stExpander"] summary{font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mu)}
[data-testid="stExpander"] summary:hover{color:var(--lime)}
[data-testid="stStatusWidget"]{display:none}
.ss-gap{height:14px}
"""


def style_tag() -> str:
    return f'<link rel="stylesheet" href="{FONTS}"><style>{CSS}</style>'


# --- small pieces ------------------------------------------------------------------------

def badge(kind: str, text: str) -> str:
    return f'<span class="ss-badge ss-badge--{kind}">{esc(text)}</span>'


def status_badge(status: str) -> str:
    return badge(STATUS_KIND[status], presenters.STATUS_LABEL[status])


def notice(kind: str, tag: str, body: str, detail: str | None = None) -> str:
    """kind: warn | bad | info | plain. body and detail are plain text (escaped here)."""
    detail_html = f'<span class="ss-notice-detail">{esc(detail)}</span>' if detail else ""
    css = "" if kind == "warn" else f" ss-notice--{kind}"
    return f'<div class="ss-notice{css}"><div class="ss-notice-tag">{esc(tag)}</div><div>{esc(body)}{detail_html}</div></div>'


def section(idx: str, title: str, aside: str = "") -> str:
    aside_html = f'<span class="ss-aside">{esc(aside)}</span>' if aside else ""
    return (f'<div class="ss-panel-mark"></div><div class="ss-section"><span class="ss-idx">{esc(idx)}</span>'
            f'<span class="ss-sec-title">{esc(title)}</span><span class="ss-rule"></span>{aside_html}</div>')


def label(text: str, aside: str = "") -> str:
    return f'<div class="ss-label">{esc(text)}<span>{esc(aside)}</span></div>'


def hint(text: str) -> str:
    return f'<div class="ss-hint">{esc(text)}</div>'


# --- header ---------------------------------------------------------------------------

LOGO = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<rect x="2.5" y="2.5" width="19" height="19" rx="1.5" stroke="#ECEBE6" stroke-width="1.4"/>'
    '<path d="M2.5 9h19M2.5 15.5h19" stroke="#ECEBE6" stroke-width="1.4"/>'
    '<rect x="5" y="4.6" width="3" height="3" fill="#CDFF3F"/><rect x="9.5" y="11" width="3" height="3" fill="#ECEBE6"/>'
    '<rect x="14" y="17.5" width="3" height="2" fill="#ECEBE6"/></svg>'
)


def header(model_name: str | None, endpoint_host: str | None, mock: bool, configured: bool) -> str:
    if not configured:
        engine = '<span class="ss-dot ss-dot--bad"></span><b>Inference not configured</b>'
    elif mock:
        engine = '<span class="ss-dot ss-dot--warn"></span><b>MOCK MODE</b><span class="ss-sep">/</span>no AMD call'
    else:
        engine = (f'<span class="ss-dot"></span><b>{esc(model_name)}</b><span class="ss-sep">/</span>'
                  f'AMD Developer Cloud · Token Factory<span class="ss-sep">/</span>{esc(endpoint_host)}')
    return (
        f'<div class="ss-top"><div class="ss-brand">{LOGO}<span>Shelf-Sense</span>'
        f'<span class="ss-tag">Shelf inspection</span></div><div class="ss-engine">{engine}</div></div>'
        '<div class="ss-hero"><div><div class="ss-eyebrow">[ Retail shelf compliance ]</div>'
        '<div class="ss-h1" role="heading" aria-level="1">One photograph.<br><span>Every facing counted.</span></div></div>'
        '<div><div class="ss-lede">A vision model on <b>AMD Developer Cloud</b> counts each product shelf by shelf. '
        '<b>Code</b> turns those counts into the verdict, an estimated margin at risk and a restocking list, '
        'and says plainly when a figure is unverified.</div>'
        '<div class="ss-coords"><span>Model <b>' + esc(model_name or "—") + '</b></span>'
        '<span>Input <b>≤1024 px</b></span><span>Calls <b>1 per inspection</b></span></div></div></div>'
    )


# --- setup panel ------------------------------------------------------------------------

def spec_table(spec: Spec) -> str:
    rows = "".join(
        f'<tr><td class="ss-prod">{esc(i.label)}</td><td class="num">{i.expected_count}</td>'
        f'<td class="num">{esc(presenters.usd(i.unit_margin_usd)) if i.unit_margin_usd is not None else "Not set"}</td></tr>'
        for i in spec.items
    )
    total = sum(i.expected_count for i in spec.items)
    return (
        f'<div class="ss-meta-line">{esc(spec.location)} · <code>{esc(spec.spec_id)}</code> · {len(spec.items)} products, {total} units expected</div>'
        '<div class="ss-table-wrap"><table class="ss-table"><thead><tr><th>Product</th><th class="num">Expected</th>'
        f'<th class="num">Unit margin*</th></tr></thead><tbody>{rows}</tbody></table></div>'
        '<div class="ss-hint">* Unit margins are author-entered demo assumptions, not point-of-sale data.</div>'
    )


def file_meta(name: str, size_bytes: int, dims: tuple[int, int] | None, source: str) -> str:
    size = f"{size_bytes / 1024 / 1024:.1f} MB" if size_bytes >= 1024 * 1024 else f"{size_bytes / 1024:.0f} KB"
    dim = f"{dims[0]} × {dims[1]} px · " if dims else ""
    return (f'<div class="ss-file"><span class="ss-file-name">{esc(name)}</span>'
            f'<span class="ss-file-meta">{esc(dim)}{esc(size)} · {esc(source)}</span></div>')


# --- results panel ------------------------------------------------------------------------

def empty_state() -> str:
    return (
        '<div class="ss-empty"><span class="ss-corner tl"></span><span class="ss-corner tr"></span>'
        '<span class="ss-corner bl"></span><span class="ss-corner br"></span>'
        '<div class="ss-empty-tag">[ Awaiting inspection ]</div>'
        '<div class="ss-empty-title">Results appear here.</div>'
        '<div class="ss-empty-copy">Pick a spec and a shelf photo, then run the inspection. '
        'One call to the vision model returns per-shelf counts; code computes everything else.</div>'
        '<ol class="ss-steps"><li><span>01</span>Per-product status with shelf-by-shelf counts</li>'
        '<li><span>02</span>Estimated margin at risk, always marked unverified</li>'
        '<li><span>03</span>A restocking list, labelled with who wrote it</li></ol></div>'
    )


def processing(model_name: str, mock: bool) -> str:
    if mock:
        head, sub = "Running mock inspection", "MOCK MODE · fixed fake result · no AMD call"
    else:
        head = "Running inspection"
        sub = f"{model_name} · AMD Token Factory · usually 20–60 s on the shared endpoint, including the action note"
    return (
        f'<div class="ss-proc"><div class="ss-proc-head"><span class="ss-dot ss-pulse"></span>{esc(head)}</div>'
        f'<div class="ss-proc-sub">{esc(sub)}</div><div class="ss-bar"><span></span></div>'
        '<ol class="ss-steps"><li><span>01</span>Photo (≤1024 px) and spec sent to the model</li>'
        '<li><span>02</span>Model counts each product, shelf by shelf</li>'
        '<li><span>03</span>Code validates the reply, computes the estimate and writes the actions</li></ol></div>'
    )


def verdict(result: ComplianceResult, endpoint_host: str | None) -> str:
    kind = OVERALL_KIND[result.overall_status]
    text = presenters.OVERALL[result.overall_status][1]
    source = "MOCK · no AMD call" if result.is_mock else f"Real inference · {endpoint_host or 'AMD endpoint'}"
    return (
        f'<div class="ss-verdict ss-verdict--{kind}"><div><div class="ss-verdict-k">Overall status</div>'
        f'<div class="ss-verdict-v"><span class="ss-dot ss-dot--{kind if kind != "ok" else ""}"></span>{esc(text)}</div></div>'
        f'<div class="ss-run-meta"><b>{esc(result.model_name or "—")}</b> · {esc(result.latency_s)} s<br>{esc(source)}</div></div>'
    )


def discrepancy_items(summary: ExposureSummary) -> list:
    """Items whose count differs from the spec or whose status needs attention, in spec order."""
    return [
        i for i in summary.items
        if i.status != "present" or i.exposure_status == "unresolved" or i.detected_count != i.expected_count
    ]


def stats(result: ComplianceResult, summary: ExposureSummary) -> str:
    n_disc = len(discrepancy_items(summary)) if summary.calculation_available else len(result.items)
    blank = '<span class="ss-stat-flag"></span>'
    flag = blank if summary.counts_verified else '<span class="ss-stat-flag">Unverified · AI-estimated counts</span>'
    return (
        '<div class="ss-stats">'
        f'<div class="ss-stat"><div class="ss-stat-k">Products checked</div><div class="ss-stat-v">{len(result.items)}</div>{blank}</div>'
        f'<div class="ss-stat"><div class="ss-stat-k">Discrepancies</div><div class="ss-stat-v">{n_disc}</div>{blank}</div>'
        f'<div class="ss-stat ss-stat--est"><div class="ss-stat-k">{esc(presenters.estimate_label(summary))}</div>'
        f'<div class="ss-stat-v">{esc(presenters.estimated_value(summary))}</div>{flag}</div>'
        f'<div class="ss-stat"><div class="ss-stat-k">{esc(presenters.POTENTIAL_LABEL)}</div>'
        f'<div class="ss-stat-v">{esc(presenters.potential_value(summary))}</div>{blank}</div></div>'
    )


def discrepancies(summary: ExposureSummary) -> str:
    items = discrepancy_items(summary)
    if not items:
        return ('<div class="ss-disc"><div class="ss-disc-none">No discrepancies in the model’s counts. '
                'Counts are AI estimates; spot-check the shelf.</div></div>')
    rows = "".join(
        f'<div class="ss-disc-row"><span class="ss-prod">{esc(i.label)}</span>'
        f'<span class="ss-disc-n">{i.detected_count} of {i.expected_count} · {_delta(i.detected_count, i.expected_count)}</span>'
        f'{status_badge(i.status)}</div>'
        for i in items
    )
    return f'<div class="ss-disc">{rows}</div>'


def _delta(detected: int, expected: int) -> str:
    d = detected - expected
    cls = "ss-delta-zero" if d == 0 else ("ss-delta-neg" if d < 0 else "ss-delta-pos")
    sign = "±0" if d == 0 else (f"−{abs(d)}" if d < 0 else f"+{d}")
    return f'<span class="{cls}">{sign}</span>'


def items_table(result: ComplianceResult, summary: ExposureSummary) -> str:
    checks = {c.item_id: c for c in result.items}
    est_label = "Est. margin*" if not summary.counts_verified else "Margin"
    show_bound = any(i.potential_exposure_usd is not None for i in summary.items)
    rows = []
    for impact in summary.items:
        check = checks[impact.item_id]
        off = impact.status != "present" or impact.exposure_status == "unresolved" or impact.detected_count != impact.expected_count
        kind = STATUS_KIND[impact.status] if off else ""
        row_cls = f' class="is-{kind if kind != "ok" else "warn"}"' if kind else ""
        shelves = (" / ".join(f"<b>{n}</b>" for n in check.shelf_counts)) if check.shelf_counts else "—"
        exposure = {
            "none": esc(presenters.usd(0)),
            "estimated": esc(presenters.usd(impact.estimated_exposure_usd or 0.0)),
            "unresolved": "Excluded",
            "unavailable": "Unavailable",
        }[impact.exposure_status]
        bound = esc(presenters.usd(impact.potential_exposure_usd)) if impact.potential_exposure_usd is not None else "—"
        rows.append(
            f'<tr{row_cls}><td class="ss-prod">{esc(impact.label)}</td><td class="num">{impact.expected_count}</td>'
            f'<td class="num">{impact.detected_count}</td><td class="num">{_delta(impact.detected_count, impact.expected_count)}</td>'
            f'<td><span class="ss-shelves">{shelves}</span></td><td>{status_badge(impact.status)}</td>'
            f'<td class="num">{exposure}</td>' + (f'<td class="num muted">{bound}</td>' if show_bound else "") + '</tr>'
        )
    return (
        '<div class="ss-table-wrap"><table class="ss-table ss-results"><thead><tr><th>Product</th><th class="num">Exp.</th>'
        '<th class="num">Det.</th><th class="num">Δ</th><th>Per shelf ↓</th><th>Status</th>'
        f'<th class="num">{esc(est_label)}</th>' + ('<th class="num">Upper bound</th>' if show_bound else "") + '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
        + ('<div class="ss-hint">* Estimated margin at risk, unverified: calculated by code from the model’s counts.</div>'
           if not summary.counts_verified else "")
    )


def observations_table(result: ComplianceResult, summary: ExposureSummary) -> str:
    labels = {i.item_id: i.label for i in summary.items}
    rows = "".join(
        f'<tr><td class="ss-prod">{esc(labels.get(c.item_id, c.item_id))}</td><td class="num">{c.confidence:.0f}%</td>'
        f'<td>{esc(c.note or "—")}</td></tr>'
        for c in result.items
    )
    return (
        '<div class="ss-table-wrap"><table class="ss-table"><thead><tr><th>Product</th><th class="num">Model confidence</th>'
        f'<th>Model note</th></tr></thead><tbody>{rows}</tbody></table></div>'
        '<div class="ss-hint">Confidence is self-reported by the model and is not calibrated. It is never used to decide anything.</div>'
    )


# --- action note ------------------------------------------------------------------------

def parse_note(text: str, labels: list[str]) -> dict:
    """Split the action note (written by app/action_agent.py) into display parts. Labels are
    matched exactly, so a model-worded instruction can never be mistaken for a product name."""
    lines = text.split("\n")
    out = {"lede": [], "items": [], "foot": [], "next": None}
    seen_items = False
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("- "):
            body = line[2:]
            match = next((l for l in sorted(labels, key=len, reverse=True) if body.startswith(l + ": ")), None)
            if match and ". Action: " in body:
                facts, action = body[len(match) + 2:].rsplit(". Action: ", 1)
                out["items"].append({"label": match, "facts": facts, "action": action})
                seen_items = True
                continue
            out["foot" if seen_items else "lede"].append(line)
        elif line.startswith("Next: "):
            out["next"] = line[len("Next: "):]
        else:
            out["foot" if seen_items else "lede"].append(line)
    return out


def actions(note: ActionNote, summary: ExposureSummary) -> str:
    if note.source == "amd":
        tag = f'<span class="ss-src ss-src--amd">AMD-worded · {esc(note.model_name)}</span>'
    elif note.source == "unavailable":
        tag = '<span class="ss-src ss-src--bad">No action note</span>'
    else:
        tag = '<span class="ss-src">Deterministic template</span>'
    parts = parse_note(note.text, [i.label for i in summary.items])
    lede = "".join(f"<span>{esc(l)}</span>" if n else esc(l) for n, l in enumerate(parts["lede"]))
    items = "".join(
        f'<div class="ss-act"><div class="ss-act-n">{n:02d}</div><div><div class="ss-act-prod">{esc(it["label"])}</div>'
        f'<div class="ss-act-do">{esc(it["action"])}</div><div class="ss-act-facts">{esc(it["facts"])}</div></div></div>'
        for n, it in enumerate(parts["items"], 1)
    )
    foot = "".join(f"<div>{esc(l)}</div>" for l in parts["foot"])
    next_html = f'<div class="ss-next"><b>Next</b>{esc(parts["next"])}</div>' if parts["next"] else ""
    return _join(
        '<div class="ss-actions"><div class="ss-actions-head"><span class="ss-actions-title">Recommended actions</span>',
        tag, '</div><div class="ss-actions-body">',
        f'<div class="ss-actions-lede">{lede}</div>' if lede else "",
        items,
        f'<div class="ss-actions-foot">{foot}</div>' if foot else "",
        next_html,
        f'</div><div class="ss-src-caption">{esc(presenters.note_source_caption(note))}</div></div>',
    )
