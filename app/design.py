"""Local presentation components. No file, network or analytical interfaces."""

import streamlit as st

CSS = """
<style>
:root {--navy:#0B1730;
--ink:#182640;
--muted:#52627A;
--blue:#2563EB;
--line:#DFE6F0;
}
[data-testid="stCaptionContainer"] {opacity:1!important;}
[data-testid="stAppViewContainer"] {background:#F6F8FC;
color:var(--ink);
}
[data-testid="stMainBlockContainer"] {max-width:1320px;
padding:3.6rem 2.6rem 2rem;
}
[data-testid="stHeader"] {background:#F6F8FC;
}
[data-testid="stSidebar"] {background:#0B1730;
border-right:1px solid #263859;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding-top:1.1rem;
}
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] small {color:#DCE5F5;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#B2C1D8;
font-size:.79rem;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:.32rem .05rem;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:.93rem;
font-weight:550;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:#182640;
}
[data-testid="stSidebar"] [data-testid="stAlert"] {background:#152D40;
border:1px solid #396B69;
}
[data-testid="stSidebar"] [data-testid="stAlert"] p {color:#CBF5E8;
}
h1,h2,h3 {letter-spacing:-.035em;
color:#182640;
}
h1 {font-size:2.35rem!important;
line-height:1.16!important;
}
h2 {font-size:1.55rem!important;
} h3 {font-size:1.12rem!important;
}
p {line-height:1.58;
} [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#52627A;
}
[data-testid="stMetric"] {background:#FFF;
border:1px solid #DFE6F0;
border-radius:14px;

 padding:1.05rem 1.15rem;
min-height:112px;
box-shadow:0 3px 12px #10234205;
}
[data-testid="stMetricLabel"] p {white-space:normal!important;
overflow:visible!important;text-overflow:clip!important;
font-size:.78rem;
letter-spacing:.015em;
color:#52627A;
font-weight:600;
}
[data-testid="stMetricValue"] {font-size:1.85rem;
letter-spacing:-.045em;
color:#122440;
}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:16px!important;
border-color:#DFE6F0!important;
background:#FFF;
}
[data-testid="stVegaLiteChart"] {background:#FFF;
border:1px solid #E3E9F2;
border-radius:16px;
padding:.5rem;
}
[data-testid="stDataFrame"] {border-radius:12px;
border:1px solid #DFE6F0;
}
[data-testid="stExpander"] {background:#FFF;
border-radius:12px;
border-color:#DFE6F0;
}
[data-testid="stAlert"] {border-radius:12px;
}
[data-testid="stMain"] a {color:#1D4ED8;
}
[data-testid="stMain"] button:focus-visible,[data-testid="stSidebar"] button:focus-visible,
input:focus-visible,a:focus-visible {outline:3px solid #38BDF8!important;
outline-offset:3px;
}
.mu-hero {background:#0B1730;
border:1px solid #233A5C;
border-radius:20px;
padding:1.8rem 2rem;
color:#FFF;
margin-bottom:.6rem;
position:relative;
overflow:hidden;
}
.mu-hero > * {position:relative;z-index:1;}
.mu-hero:after {z-index:0;content:'';
position:absolute;
width:180px;
height:180px;
border:32px solid #1C3B69;
border-radius:50%;
right:-72px;
top:-75px;
pointer-events:none;
}
.mu-brand {font-size:.73rem;
letter-spacing:.15em;
text-transform:uppercase;
font-weight:650;
color:#A9C3ED;
margin-bottom:.85rem;
}
.mu-hero h1 {color:#FFF;
font-size:clamp(1.9rem,3vw,2.7rem)!important;
margin:0 0 .65rem;
max-width:790px;
}
.mu-hero p {color:#CFDAEB;
max-width:780px;
margin:0;
font-size:.96rem;
}
.mu-tag {display:inline-block;
padding:.23rem .6rem;
border:1px solid #496186;
border-radius:30px;
color:#D8E8FF;
font-size:.69rem;
letter-spacing:.06em;
margin-bottom:.9rem;
}
.mu-eyebrow {color:#52627A;
letter-spacing:.13em;
text-transform:uppercase;
font-size:.71rem;
font-weight:700;
margin:.5rem 0 .45rem;
}
.mu-intro {color:#52627A;
font-size:1rem;
margin:-.25rem 0 1rem;
max-width:900px;
}
.mu-panel {background:#FFF;
border:1px solid #DFE6F0;
border-left:4px solid #2563EB;
border-radius:14px;
padding:1.1rem 1.3rem;
margin:.2rem 0 .8rem;
}
.mu-panel.teal {border-left-color:#0D9488;
background:#F0FAF7;
}
.mu-panel.amber {border-left-color:#B45309;
background:#FFFBF2;
}
.mu-panel.violet {border-left-color:#7C3AED;
}
.mu-panel h3 {font-size:1rem!important;
margin:0 0 .4rem;
letter-spacing:-.01em;
}
.mu-panel p {font-size:.9rem;
margin:0;
color:#3C506B;
}
.mu-grid {display:grid;
grid-template-columns:repeat(3,minmax(0,1fr));
gap:1rem;
margin:.4rem 0 1rem;
}
.mu-step {background:#FFF;
border:1px solid #DFE6F0;
border-radius:14px;
padding:1.15rem;
}
.mu-step .mu-num {font-size:.7rem;
color:#2563EB;
font-weight:750;
letter-spacing:.08em;
}
.mu-step h3 {margin:.35rem 0 .45rem;
}
.mu-step p {font-size:.86rem;
color:#52627A;
margin:0;
}
.mu-flow {display:grid;
grid-template-columns:repeat(5,minmax(0,1fr));
gap:.6rem;
margin:.3rem 0 1.2rem;
}
.mu-node {background:#FFF;
border:1px solid #D9E3F2;
border-top:3px solid #2563EB;
border-radius:12px;
padding:1rem .8rem;
}
.mu-node b {display:block;
font-size:.85rem;
margin:.35rem 0;
color:#182640;
}
.mu-node span {font-size:.74rem;
color:#52627A;
line-height:1.45;
display:block;
}
.mu-wordmark {padding:.4rem 0 1rem;
line-height:1.3;
font-size:1.15rem;
font-weight:700;
color:#FFF;
letter-spacing:-.025em;
}
.mu-wordmark span {display:block;
font-size:.66rem;
font-weight:550;
letter-spacing:.15em;
color:#A9C3ED;
text-transform:uppercase;
margin-top:.4rem;
}
@media(max-width:1100px) {[data-testid="stMainBlockContainer"] {padding:3.6rem 1.4rem;
} .mu-flow {grid-template-columns:repeat(3,minmax(0,1fr));
}}
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="select"]>div {background:#FFF;
border:1px solid #D4DEEC;border-radius:10px;}
@media(max-width:700px) {
.st-key-overview_kpis [data-testid="stHorizontalBlock"] {display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;}
.st-key-overview_kpis [data-testid="stColumn"] {min-width:0!important;width:100%!important;}
[data-testid="stMainBlockContainer"] {padding:3.5rem .85rem 2rem;
}
.mu-hero {padding:1.3rem 1.1rem;
border-radius:16px;
} .mu-hero h1 {font-size:1.95rem!important;
}
.mu-grid {grid-template-columns:1fr;
} .mu-flow {grid-template-columns:1fr 1fr;
}
h1 {font-size:1.85rem!important;
} [data-testid="stMetric"] {min-height:96px;
padding:.9rem 1rem;
}
[data-testid="stMetricValue"] {font-size:1.65rem;
}}
@media(prefers-reduced-motion:reduce) {* {scroll-behavior:auto!important;
transition:none!important;
}}
</style>
"""


def apply():
    st.html(CSS)


def escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heading(section, title, description):
    st.html(f'<div class="mu-eyebrow">{escape(section)}</div>')
    st.title(title)
    st.html(f'<p class="mu-intro">{escape(description)}</p>')


def panel(title, text, tone="blue"):
    if tone not in ("blue", "teal", "amber", "violet"):
        raise ValueError("Unknown presentation tone")
    st.html(
        f'<section class="mu-panel {tone}"><h3>{escape(title)}</h3><p>{escape(text)}</p></section>'
    )


def cards(items, *, flow=False):
    css = "mu-flow" if flow else "mu-grid"
    child = "mu-node" if flow else "mu-step"
    content = ""
    for i, (title, text) in enumerate(items, 1):
        content += (
            f'<div class="{child}"><span class="mu-num">0{i}</span>'
            f"<h3>{escape(title)}</h3><p>{escape(text)}</p></div>"
        )
    st.html(f'<div class="{css}">{content}</div>')
