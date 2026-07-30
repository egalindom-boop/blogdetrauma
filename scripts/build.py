# -*- coding: utf-8 -*-
"""Static site generator for blogdetrauma.com (WordPress -> static HTML)."""
import json, os, re, shutil, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from clean import clean_content, make_excerpt, format_date_es, slugify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('SITE_OUT', os.path.join(ROOT, 'site'))
RAW_IMAGES = os.path.join(ROOT, 'raw_images')
DOMAIN = 'https://blogdetrauma.com'

CATEGORY_ORDER = [
    'Trauma', 'Fracturas', 'Artrosis', 'Artroscopia', 'Cirugía de Mano',
    'Lesiones de Muñeca', 'Cirugía Miembro Superior', 'Cirugía Miembro Inferior',
    'Cirugía del Pie', 'Columna', 'Medicina Deportiva', 'Osteoporosis',
    'Tumores', 'Docencia', 'Televisión / Radio', 'Tecnologia',
]

BIO_ITEMS = [
    'Especialista en Traumatología y Cirugía Ortopédica',
    'Profesor Facultad de Medicina, Universidad Europea',
    'Licenciado en Medicina y Cirugía en Madrid',
    'United States Medical Licensing Examination',
    'Fellowship en Miami, FL, Estados Unidos',
    'Royal Australasian College of Surgeons Examination',
    'Fellowship Hand &amp; Upper Limb Surgery. Perth, Australia',
    'Investigación, Desarrollo y Patente de Prótesis de Hombro KIMS',
]

SOCIEDADES = [
    ('Sociedad Española de Cirugía Ortopédica y Traumatología', 'https://www.secot.es'),
    ('Asociación para el Estudio para la Osteosíntesis. Grupo AO. Suiza', 'https://www.aofoundation.org'),
    ('Sociedad Española de Artroscopia', 'https://www.aeartroscopia.com'),
]

CSS = r"""
:root{
  --azul:#0e4d92;
  --azul-oscuro:#0a3a6e;
  --azul-claro:#e8f1fb;
  --texto:#26313c;
  --texto-suave:#5b6b7b;
  --borde:#e3e9f0;
  --fondo:#f7fafc;
  --blanco:#ffffff;
  --acento:#0e8a6d;
  --max:1140px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Source Sans 3','Segoe UI',system-ui,-apple-system,sans-serif;color:var(--texto);background:var(--fondo);line-height:1.7;font-size:17px}
img{max-width:100%;height:auto}
a{color:var(--azul);text-decoration:none}
a:hover{text-decoration:underline}
.container{max-width:var(--max);margin:0 auto;padding:0 20px}

/* Header */
.site-header{background:var(--blanco);border-bottom:3px solid var(--azul);box-shadow:0 1px 8px rgba(14,77,146,.08)}
.header-inner{display:flex;align-items:center;justify-content:space-between;padding:18px 0;flex-wrap:wrap;gap:10px}
.brand h1,.brand p.logo{font-family:'Lora',Georgia,serif;font-size:1.55rem;font-weight:700;color:var(--azul-oscuro);line-height:1.2}
.brand a{color:inherit;text-decoration:none}
.brand .tagline{font-size:.95rem;color:var(--texto-suave);margin-top:2px}
.main-nav{display:flex;gap:22px;flex-wrap:wrap}
.main-nav a{font-weight:600;font-size:.95rem;color:var(--texto);padding:4px 0;border-bottom:2px solid transparent}
.main-nav a:hover,.main-nav a.active{color:var(--azul);border-bottom-color:var(--azul);text-decoration:none}

/* Layout */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:44px;padding:44px 0}
@media(max-width:900px){.layout{grid-template-columns:1fr;padding:28px 0}}

/* Cards / listing */
.post-card{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;padding:30px 34px;margin-bottom:26px;box-shadow:0 1px 4px rgba(20,40,70,.05)}
.post-card h2{font-family:'Lora',Georgia,serif;font-size:1.45rem;line-height:1.3;margin-bottom:8px}
.post-card h2 a{color:var(--azul-oscuro)}
.post-card h2 a:hover{color:var(--azul);text-decoration:none}
.post-meta{font-size:.85rem;color:var(--texto-suave);margin-bottom:14px;display:flex;gap:14px;flex-wrap:wrap}
.post-meta .cats a{color:var(--acento);font-weight:600}
.post-card .excerpt{color:var(--texto)}
.leer-mas{display:inline-block;margin-top:12px;font-weight:700;font-size:.92rem}

/* Article */
.article{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;padding:40px 46px;box-shadow:0 1px 4px rgba(20,40,70,.05)}
@media(max-width:600px){.article{padding:26px 20px}}
.article h1{font-family:'Lora',Georgia,serif;font-size:2rem;line-height:1.25;color:var(--azul-oscuro);margin-bottom:10px}
.article .post-meta{margin-bottom:26px;padding-bottom:18px;border-bottom:1px solid var(--borde)}
.article-content p{margin-bottom:1.1em;text-align:left}
.article-content h2,.article-content h3{font-family:'Lora',Georgia,serif;color:var(--azul-oscuro);margin:1.4em 0 .6em}
.article-content ul,.article-content ol{margin:0 0 1.1em 1.4em}
.article-content strong{color:var(--azul-oscuro)}
.article-content table{border-collapse:collapse;margin:1.2em 0;width:100%}
.article-content td,.article-content th{border:1px solid var(--borde);padding:8px 12px}
.post-figure{margin:1.6em auto;text-align:center}
.post-figure img{border-radius:8px;box-shadow:0 2px 12px rgba(20,40,70,.12)}
.post-figure figcaption{font-size:.85rem;color:var(--texto-suave);margin-top:8px;font-style:italic}
.video-embed{position:relative;padding-bottom:56.25%;height:0;margin:1.6em 0;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(20,40,70,.15)}
.video-embed iframe{position:absolute;top:0;left:0;width:100%;height:100%;border:0}

/* Sidebar */
.sidebar .widget{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;padding:24px 26px;margin-bottom:24px;box-shadow:0 1px 4px rgba(20,40,70,.05)}
.sidebar .widget h3{font-family:'Lora',Georgia,serif;font-size:1.05rem;color:var(--azul-oscuro);text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid var(--azul);padding-bottom:8px;margin-bottom:14px}
.sidebar ul{list-style:none}
.sidebar li{padding:5px 0;border-bottom:1px dashed var(--borde);font-size:.92rem}
.sidebar li:last-child{border-bottom:none}
.doctor-card{text-align:center}
.doctor-card img{border-radius:10px;margin-bottom:12px}
.doctor-card .nombre{font-family:'Lora',Georgia,serif;font-weight:700;color:var(--azul-oscuro);font-size:1.1rem}
.bio-list li{text-align:left;position:relative;padding-left:18px}
.bio-list li::before{content:'›';position:absolute;left:2px;color:var(--acento);font-weight:700}
.cat-list a{color:var(--texto)}
.cat-list a:hover{color:var(--azul)}
.cat-list .num{color:var(--texto-suave);font-size:.85rem}

/* Pagination */
.pagination{display:flex;justify-content:center;gap:8px;margin:30px 0;flex-wrap:wrap}
.pagination a,.pagination span{padding:8px 14px;border:1px solid var(--borde);border-radius:8px;background:var(--blanco);font-weight:600;font-size:.9rem}
.pagination span.current{background:var(--azul);color:#fff;border-color:var(--azul)}
.pagination a:hover{background:var(--azul-claro);text-decoration:none}

/* Footer */
.site-footer{background:var(--azul-oscuro);color:#cfe0f2;margin-top:50px;padding:44px 0 90px}
.footer-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:34px}
.site-footer h4{color:#fff;font-family:'Lora',Georgia,serif;margin-bottom:12px;font-size:1rem}
.site-footer ul{list-style:none}
.site-footer li{padding:3px 0;font-size:.9rem}
.site-footer a{color:#a8c8e8}
.site-footer a:hover{color:#fff}
.footer-bottom{border-top:1px solid rgba(255,255,255,.15);margin-top:34px;padding-top:18px;font-size:.85rem;color:#9fb8d4;text-align:center}

/* Cookie bar */
#cookie-bar{position:fixed;bottom:0;left:0;right:0;background:#132a42;color:#e4edf7;padding:14px 20px;z-index:1000;box-shadow:0 -2px 14px rgba(0,0,0,.3);transform:translateY(110%);transition:transform .3s ease}
#cookie-bar.visible{transform:translateY(0)}
#cookie-bar .cb-inner{max-width:var(--max);margin:0 auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap;justify-content:space-between}
#cookie-bar p{font-size:.88rem;margin:0;flex:1 1 400px}
#cookie-bar a{color:#8fc1f0;text-decoration:underline}
#cookie-bar .cb-btns{display:flex;gap:10px}
#cookie-bar button{border:0;border-radius:8px;padding:9px 20px;font-weight:700;cursor:pointer;font-size:.88rem}
#cb-accept{background:#0e8a6d;color:#fff}
#cb-reject{background:transparent;color:#cfe0f2;border:1px solid #56718d}
"""

COOKIE_JS = r"""
(function(){
  var KEY='cookie-consent-bdt';
  function loadGA(){
    if(window._gaLoaded)return;window._gaLoaded=true;
    /* GA se inyecta via Netlify Snippet Injection; aqui solo activamos consentimiento */
    window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    window.gtag=window.gtag||gtag;
    gtag('consent','update',{analytics_storage:'granted'});
  }
  var v=null;
  try{v=localStorage.getItem(KEY);}catch(e){}
  if(v==='accepted'){loadGA();}
  else if(v!=='rejected'){
    var bar=document.getElementById('cookie-bar');
    if(bar){bar.classList.add('visible');}
  }
  var a=document.getElementById('cb-accept'),r=document.getElementById('cb-reject');
  if(a)a.addEventListener('click',function(){try{localStorage.setItem(KEY,'accepted');}catch(e){}loadGA();document.getElementById('cookie-bar').classList.remove('visible');});
  if(r)r.addEventListener('click',function(){try{localStorage.setItem(KEY,'rejected');}catch(e){}document.getElementById('cookie-bar').classList.remove('visible');});
})();
"""


def head(title, description, canonical, extra=''):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Source+Sans+3:wght@400;600;700&display=optional" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Source+Sans+3:wght@400;600;700&display=optional" rel="stylesheet"></noscript>
<style>{CSS}</style>
<link rel="alternate" type="application/rss+xml" title="Blog de Trauma RSS" href="/rss.xml">
{extra}
</head>
<body>
"""


def header_nav(active=''):
    def cls(k):
        return ' class="active"' if k == active else ''
    return f"""<header class="site-header">
  <div class="container header-inner">
    <div class="brand">
      <p class="logo"><a href="/">Blog del Dr. Enrique Galindo Martens</a></p>
      <p class="tagline">La Traumatología dedicada a los pacientes</p>
    </div>
    <nav class="main-nav">
      <a href="/"{cls('inicio')}>Inicio</a>
      <a href="/categorias/"{cls('categorias')}>Categorías</a>
      <a href="/sobre-mi/"{cls('sobre')}>Sobre mí</a>
    </nav>
  </div>
</header>
"""


def sidebar(cats_with_counts, recent_posts):
    cats_html = '\n'.join(
        f'<li><a href="/categoria/{slugify(c)}/">{c}</a> <span class="num">({n})</span></li>'
        for c, n in cats_with_counts
    )
    recientes = '\n'.join(
        f'<li><a href="/{p["slug"]}/">{p["title"]}</a></li>' for p in recent_posts[:6]
    )
    bio = '\n'.join(f'<li>{b}</li>' for b in BIO_ITEMS)
    socs = '\n'.join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n, u in SOCIEDADES)
    return f"""<aside class="sidebar">
  <div class="widget doctor-card">
    <p class="nombre">Dr. Enrique Galindo Martens</p>
    <p style="font-size:.9rem;color:var(--texto-suave)">Traumatólogo y Cirujano Ortopédico</p>
  </div>
  <div class="widget">
    <h3>Currículum</h3>
    <ul class="bio-list">{bio}</ul>
  </div>
  <div class="widget">
    <h3>Sociedades</h3>
    <ul>{socs}</ul>
  </div>
  <div class="widget">
    <h3>Categorías</h3>
    <ul class="cat-list">{cats_html}</ul>
  </div>
  <div class="widget">
    <h3>Artículos recientes</h3>
    <ul>{recientes}</ul>
  </div>
  <div class="widget">
    <h3>Tecnología médica</h3>
    <ul>
      <li><a href="https://www.dricloud.com" target="_blank" rel="noopener">Software médico DriCloud</a></li>
      <li><a href="https://www.xdentalcloud.com" target="_blank" rel="noopener">Software dental XDentalCloud</a></li>
      <li><a href="https://gestionmedica.org" target="_blank" rel="noopener">Gestión Médica</a></li>
    </ul>
  </div>
</aside>
"""


def footer():
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>Blog de Trauma</h4>
        <p style="font-size:.9rem">Blog del Dr. Enrique Galindo Martens, especialista en Traumatología y Cirugía Ortopédica. Divulgación médica dedicada a los pacientes desde 2009.</p>
      </div>
      <div>
        <h4>Navegación</h4>
        <ul>
          <li><a href="/">Inicio</a></li>
          <li><a href="/categorias/">Categorías</a></li>
          <li><a href="/sobre-mi/">Sobre mí</a></li>
          <li><a href="/politica-de-cookies/">Política de cookies</a></li>
          <li><a href="/politica-de-privacidad/">Política de privacidad</a></li>
        </ul>
      </div>
      <div>
        <h4>Recursos recomendados</h4>
        <ul>
          <li><a href="https://www.dricloud.com" target="_blank" rel="noopener">DriCloud · Software médico</a></li>
          <li><a href="https://www.xdentalcloud.com" target="_blank" rel="noopener">XDentalCloud · Software dental</a></li>
          <li><a href="https://gestionmedica.org" target="_blank" rel="noopener">Gestión Médica</a></li>
          <li><a href="https://gestiondental.org" target="_blank" rel="noopener">Gestión Dental</a></li>
          <li><a href="https://mejorsoftware.org/software-clinicas/" target="_blank" rel="noopener">Comparador de software para clínicas</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2009–{datetime.now().year} Blog del Dr. Enrique Galindo Martens · blogdetrauma.com</p>
      <p style="margin-top:6px">La información de este blog es divulgativa y no sustituye la consulta con un médico especialista.</p>
    </div>
  </div>
</footer>
<div id="cookie-bar">
  <div class="cb-inner">
    <p>Utilizamos cookies analíticas (Google Analytics) para mejorar el contenido del blog. Puedes aceptarlas o rechazarlas. Más información en la <a href="/politica-de-cookies/">política de cookies</a>.</p>
    <div class="cb-btns">
      <button id="cb-accept">Aceptar</button>
      <button id="cb-reject">Rechazar</button>
    </div>
  </div>
</div>
<script src="/js/cookies.js" defer></script>
</body>
</html>
"""


def post_card(p):
    cats = ', '.join(f'<a href="/categoria/{slugify(c["name"])}/">{c["name"]}</a>' for c in p['categories'] if c['name'] != 'Sin categoría')
    return f"""<article class="post-card">
  <h2><a href="/{p['slug']}/">{p['title']}</a></h2>
  <div class="post-meta">
    <span>📅 {p['date_es']}</span>
    <span class="cats">{cats}</span>
  </div>
  <p class="excerpt">{p['excerpt']}</p>
  <a class="leer-mas" href="/{p['slug']}/">Continuar leyendo →</a>
</article>
"""



def _hacer_exportador():
    """Convierte jpg/png a WebP (max 1200px de ancho); si no hay Pillow, copia tal cual."""
    try:
        from PIL import Image
    except ImportError:
        Image = None

    def exportar(src, destdir, basename):
        stem, dot, ext = basename.rpartition('.')
        ext = ext.lower()
        if Image is None or ext not in ('jpg', 'jpeg', 'png'):
            shutil.copy2(src, os.path.join(destdir, basename))
            return
        try:
            im = Image.open(src)
            if im.mode in ('P', 'RGBA'):
                im = im.convert('RGBA') if 'A' in im.getbands() else im.convert('RGB')
        except Exception:
            shutil.copy2(src, os.path.join(destdir, basename))
            return
        try:
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
            if im.width > 1200:
                im = im.resize((1200, int(im.height * 1200 / im.width)), Image.LANCZOS)
            im.save(os.path.join(destdir, f'{stem}.webp'), 'WEBP', quality=82, method=4)
        except Exception:
            shutil.copy2(src, os.path.join(destdir, basename))
    return exportar

def build():
    posts = json.load(open(os.path.join(ROOT, 'posts.json'), encoding='utf-8'))
    available = set(f for f in os.listdir(RAW_IMAGES) if not f.startswith('.') and f != '__MACOSX')
    used_images = set()

    # clean & enrich
    legacy_redirects = []
    for p in posts:
        # replace numeric/meaningless slugs with title-derived ones, keeping a 301
        if not p['slug'] or re.match(r'^\d+(-\d+)?$', p['slug']):
            old = p['slug']
            p['slug'] = slugify(p['title'])
            if old:
                legacy_redirects.append((f'/{old}/', f'/{p["slug"]}/'))
                legacy_redirects.append((f'/{old}', f'/{p["slug"]}/'))
        p['dt'] = datetime.strptime(p['postdate'], '%Y-%m-%d %H:%M:%S')
        p['date_es'] = format_date_es(p['dt'])
        p['clean'] = clean_content(p['content'], available, used_images)
        p['excerpt'] = p['excerpt'].strip() or make_excerpt(p['clean'])
        # first image for og:image
        m = re.search(r'src="(/images/[^"]+)"', p['clean'])
        p['og_image'] = m.group(1) if m else None

    posts.sort(key=lambda p: p['dt'], reverse=True)

    # reset site dir
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE)
    os.makedirs(os.path.join(SITE, 'css'))
    os.makedirs(os.path.join(SITE, 'js'))
    os.makedirs(os.path.join(SITE, 'images'))

    with open(os.path.join(SITE, 'css', 'estilo.css'), 'w') as f:
        f.write(CSS)
    with open(os.path.join(SITE, 'js', 'cookies.js'), 'w') as f:
        f.write(COOKIE_JS)

    # copy used images only (convertidas a WebP)
    exportar_imagen_optimizada = _hacer_exportador()
    for img in used_images:
        src = os.path.join(RAW_IMAGES, img)
        if os.path.exists(src):
            exportar_imagen_optimizada(src, os.path.join(SITE, 'images'), img)

    # categories
    from collections import Counter, defaultdict
    cat_counts = Counter()
    cat_posts = defaultdict(list)
    for p in posts:
        for c in p['categories']:
            if c['name'] == 'Sin categoría':
                continue
            cat_counts[c['name']] += 1
            cat_posts[c['name']].append(p)
    cats_sorted = [(c, cat_counts[c]) for c in CATEGORY_ORDER if c in cat_counts]
    for c in cat_counts:
        if c not in CATEGORY_ORDER:
            cats_sorted.append((c, cat_counts[c]))

    sb = sidebar(cats_sorted, posts)

    # ---------- index + pagination ----------
    PER_PAGE = 10
    pages = [posts[i:i+PER_PAGE] for i in range(0, len(posts), PER_PAGE)]
    for i, page_posts in enumerate(pages):
        num = i + 1
        cards = '\n'.join(post_card(p) for p in page_posts)
        pag = ['<nav class="pagination">']
        for j in range(1, len(pages)+1):
            href = '/' if j == 1 else f'/pagina/{j}/'
            if j == num:
                pag.append(f'<span class="current">{j}</span>')
            else:
                pag.append(f'<a href="{href}">{j}</a>')
        pag.append('</nav>')
        pag_html = '\n'.join(pag)

        title = 'Blog del Dr. Enrique Galindo Martens · Traumatología y Cirugía Ortopédica'
        if num > 1:
            title += f' · Página {num}'
        desc = 'Blog de Traumatología y Cirugía Ortopédica del Dr. Enrique Galindo Martens. Artículos sobre fracturas, artrosis, artroscopia, cirugía de mano y medicina deportiva explicados para pacientes.'
        canonical = DOMAIN + ('/' if num == 1 else f'/pagina/{num}/')
        html = head(title, desc, canonical) + header_nav('inicio')
        html += f'<div class="container layout"><main>{cards}{pag_html}</main>{sb}</div>'
        html += footer()

        if num == 1:
            out = os.path.join(SITE, 'index.html')
        else:
            os.makedirs(os.path.join(SITE, 'pagina', str(num)), exist_ok=True)
            out = os.path.join(SITE, 'pagina', str(num), 'index.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)

    # ---------- post pages ----------
    for idx, p in enumerate(posts):
        cats = ', '.join(f'<a href="/categoria/{slugify(c["name"])}/">{c["name"]}</a>' for c in p['categories'] if c['name'] != 'Sin categoría')
        tags = ', '.join(t['name'] for t in p['tags'])
        canonical = f'{DOMAIN}/{p["slug"]}/'
        og_img = f'<meta property="og:image" content="{DOMAIN}{p["og_image"]}">' if p['og_image'] else ''
        extra = f"""<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['excerpt']}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
{og_img}
<script type="application/ld+json">{json.dumps({
    '@context': 'https://schema.org',
    '@type': 'MedicalWebPage',
    'headline': p['title'],
    'datePublished': p['dt'].strftime('%Y-%m-%d'),
    'author': {'@type': 'Physician', 'name': 'Dr. Enrique Galindo Martens',
               'medicalSpecialty': 'Traumatología y Cirugía Ortopédica'},
    'url': canonical,
    'inLanguage': 'es',
}, ensure_ascii=False)}</script>"""

        # prev / next
        nav_links = []
        if idx < len(posts) - 1:
            older = posts[idx+1]
            nav_links.append(f'<a href="/{older["slug"]}/">← {older["title"]}</a>')
        if idx > 0:
            newer = posts[idx-1]
            nav_links.append(f'<a href="/{newer["slug"]}/" style="margin-left:auto">{newer["title"]} →</a>')
        prevnext = f'<nav style="display:flex;gap:20px;margin-top:34px;padding-top:20px;border-top:1px solid var(--borde);font-size:.9rem;flex-wrap:wrap">{"".join(nav_links)}</nav>'

        tags_html = f'<p style="margin-top:22px;font-size:.85rem;color:var(--texto-suave)"><strong>Etiquetas:</strong> {tags}</p>' if tags else ''

        html = head(f"{p['title']} · Blog de Trauma", p['excerpt'][:158], canonical, extra)
        html += header_nav()
        html += f"""<div class="container layout"><main><article class="article">
<h1>{p['title']}</h1>
<div class="post-meta"><span>📅 {p['date_es']}</span><span class="cats">{cats}</span></div>
<div class="article-content">
{p['clean']}
</div>
{tags_html}
{prevnext}
</article></main>{sb}</div>"""
        html += footer()

        d = os.path.join(SITE, p['slug'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    # ---------- category pages ----------
    os.makedirs(os.path.join(SITE, 'categoria'), exist_ok=True)
    for cname, cposts in cat_posts.items():
        cslug = slugify(cname)
        cards = '\n'.join(post_card(p) for p in cposts)
        canonical = f'{DOMAIN}/categoria/{cslug}/'
        html = head(f'{cname} · Blog de Trauma',
                    f'Artículos sobre {cname} del Dr. Enrique Galindo Martens, especialista en Traumatología y Cirugía Ortopédica.',
                    canonical)
        html += header_nav('categorias')
        html += f'<div class="container layout"><main><h1 style="font-family:Lora,Georgia,serif;color:var(--azul-oscuro);margin-bottom:24px">Categoría: {cname}</h1>{cards}</main>{sb}</div>'
        html += footer()
        d = os.path.join(SITE, 'categoria', cslug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    # ---------- categorias index ----------
    cat_blocks = '\n'.join(
        f'<article class="post-card"><h2><a href="/categoria/{slugify(c)}/">{c}</a></h2><p class="excerpt">{n} artículo{"s" if n!=1 else ""}</p></article>'
        for c, n in cats_sorted
    )
    html = head('Categorías · Blog de Trauma',
                'Todas las categorías del blog de Traumatología del Dr. Enrique Galindo Martens.',
                f'{DOMAIN}/categorias/')
    html += header_nav('categorias')
    html += f'<div class="container layout"><main><h1 style="font-family:Lora,Georgia,serif;color:var(--azul-oscuro);margin-bottom:24px">Categorías</h1>{cat_blocks}</main>{sb}</div>'
    html += footer()
    os.makedirs(os.path.join(SITE, 'categorias'), exist_ok=True)
    with open(os.path.join(SITE, 'categorias', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # ---------- sobre mi ----------
    bio_lis = '\n'.join(f'<li>{b}</li>' for b in BIO_ITEMS)
    html = head('Sobre mí · Dr. Enrique Galindo Martens',
                'Currículum del Dr. Enrique Galindo Martens, especialista en Traumatología y Cirugía Ortopédica, profesor de la Facultad de Medicina de la Universidad Europea.',
                f'{DOMAIN}/sobre-mi/')
    html += header_nav('sobre')
    html += f"""<div class="container layout"><main><article class="article">
<h1>Dr. Enrique Galindo Martens</h1>
<div class="article-content">
<p>Soy especialista en <strong>Traumatología y Cirugía Ortopédica</strong>, y desde 2009 escribo este blog con un objetivo claro: acercar la traumatología a los pacientes, explicando en un lenguaje comprensible las lesiones, tratamientos y técnicas quirúrgicas más habituales de la especialidad.</p>
<h2>Formación y trayectoria</h2>
<ul class="bio-list" style="list-style:none;margin-left:0">{bio_lis}</ul>
<h2>Sociedades científicas</h2>
<ul>{''.join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n,u in SOCIEDADES)}</ul>
<h2>Tecnología y medicina</h2>
<p>Además de la práctica clínica, me interesa la transformación digital de la medicina. En mi consulta utilizo el software médico en la nube <a href="https://www.dricloud.com" target="_blank" rel="noopener">DriCloud</a>, que permite gestionar historia clínica electrónica, citas y firma digital de consentimientos. Para clínicas dentales existe su equivalente, <a href="https://www.xdentalcloud.com" target="_blank" rel="noopener">XDentalCloud</a>. Si estás valorando digitalizar una clínica, portales como <a href="https://gestionmedica.org" target="_blank" rel="noopener">gestionmedica.org</a>, <a href="https://gestiondental.org" target="_blank" rel="noopener">gestiondental.org</a> o el <a href="https://mejorsoftware.org/software-clinicas/" target="_blank" rel="noopener">comparador de software para clínicas de mejorsoftware.org</a> son un buen punto de partida.</p>
</div>
</article></main>{sb}</div>"""
    html += footer()
    os.makedirs(os.path.join(SITE, 'sobre-mi'), exist_ok=True)
    with open(os.path.join(SITE, 'sobre-mi', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # ---------- legal pages ----------
    legal_pages = {
        'politica-de-cookies': ('Política de cookies', """
<p>Este sitio web, blogdetrauma.com, utiliza cookies propias técnicas imprescindibles para su funcionamiento y cookies analíticas de terceros (Google Analytics) que solo se activan si el usuario las acepta expresamente mediante la barra de consentimiento.</p>
<h2>¿Qué son las cookies?</h2>
<p>Las cookies son pequeños archivos de texto que se almacenan en el navegador del usuario al visitar una página web. Permiten, entre otras cosas, recordar preferencias o elaborar estadísticas de uso.</p>
<h2>Cookies utilizadas en este sitio</h2>
<ul>
<li><strong>Cookies técnicas:</strong> almacenan la preferencia de consentimiento del usuario (localStorage: cookie-consent-bdt).</li>
<li><strong>Cookies analíticas (Google Analytics):</strong> permiten conocer de forma anónima el número de visitas y las páginas más consultadas. Solo se instalan si el usuario pulsa «Aceptar» en la barra de cookies.</li>
</ul>
<h2>Cómo desactivar las cookies</h2>
<p>El usuario puede rechazar las cookies analíticas desde la propia barra de consentimiento, o eliminarlas y bloquearlas en cualquier momento desde la configuración de su navegador.</p>
<h2>Responsable</h2>
<p>Massive Bionics LLC · Contacto: luki.negocios@gmail.com</p>
"""),
        'politica-de-privacidad': ('Política de privacidad', """
<p>En cumplimiento del Reglamento (UE) 2016/679 (RGPD) y de la LOPDGDD 3/2018, se informa a los usuarios de blogdetrauma.com de lo siguiente:</p>
<h2>Responsable del tratamiento</h2>
<p>Massive Bionics LLC · Contacto: luki.negocios@gmail.com</p>
<h2>Datos tratados</h2>
<p>Este sitio web no dispone de formularios de contacto ni recoge datos personales identificativos de los usuarios. Únicamente se tratan datos estadísticos anónimos de navegación mediante Google Analytics, previa aceptación de cookies por el usuario.</p>
<h2>Finalidad</h2>
<p>Elaborar estadísticas de uso del sitio con el fin de mejorar sus contenidos.</p>
<h2>Derechos</h2>
<p>El usuario puede ejercer sus derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo al correo de contacto indicado.</p>
<h2>Carácter divulgativo</h2>
<p>Los contenidos de este blog tienen carácter exclusivamente informativo y divulgativo, y en ningún caso sustituyen la consulta, diagnóstico o tratamiento realizados por un médico especialista.</p>
"""),
    }
    for slug, (title, body) in legal_pages.items():
        html = head(f'{title} · Blog de Trauma', title, f'{DOMAIN}/{slug}/')
        html += header_nav()
        html += f'<div class="container layout"><main><article class="article"><h1>{title}</h1><div class="article-content">{body}</div></article></main>{sb}</div>'
        html += footer()
        d = os.path.join(SITE, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    # ---------- sitemap, robots, rss, 404, redirects ----------
    urls = [f'{DOMAIN}/']
    urls += [f'{DOMAIN}/{p["slug"]}/' for p in posts]
    urls += [f'{DOMAIN}/categoria/{slugify(c)}/' for c, _ in cats_sorted]
    urls += [f'{DOMAIN}/categorias/', f'{DOMAIN}/sobre-mi/',
             f'{DOMAIN}/politica-de-cookies/', f'{DOMAIN}/politica-de-privacidad/']
    urls += [f'{DOMAIN}/pagina/{i}/' for i in range(2, len(pages)+1)]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sm += f'  <url><loc>{u}</loc></url>\n'
    sm += '</urlset>\n'
    with open(os.path.join(SITE, 'sitemap.xml'), 'w') as f:
        f.write(sm)

    with open(os.path.join(SITE, 'robots.txt'), 'w') as f:
        f.write(f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')

    # RSS (last 20)
    rss_items = ''
    for p in posts[:20]:
        rss_items += f"""  <item>
    <title>{p['title'].replace('&','&amp;')}</title>
    <link>{DOMAIN}/{p['slug']}/</link>
    <guid>{DOMAIN}/{p['slug']}/</guid>
    <pubDate>{p['dt'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
    <description><![CDATA[{p['excerpt']}]]></description>
  </item>\n"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Blog del Dr. Enrique Galindo Martens</title>
  <link>{DOMAIN}</link>
  <description>La Traumatología dedicada a los pacientes</description>
  <language>es</language>
{rss_items}</channel>
</rss>
"""
    with open(os.path.join(SITE, 'rss.xml'), 'w', encoding='utf-8') as f:
        f.write(rss)

    # 404
    html = head('Página no encontrada · Blog de Trauma', 'Error 404', f'{DOMAIN}/404.html')
    html += header_nav()
    html += '<div class="container layout"><main><article class="article"><h1>Página no encontrada</h1><div class="article-content"><p>La página que buscas no existe o ha cambiado de dirección.</p><p><a href="/">← Volver a la portada</a></p></div></article></main></div>'
    html += footer()
    with open(os.path.join(SITE, '404.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # _redirects: legacy WP urls
    with open(os.path.join(SITE, '_redirects'), 'w') as f:
        f.write('/feed /rss.xml 301\n/feed/ /rss.xml 301\n')
        for old, new in legacy_redirects:
            f.write(f'{old} {new} 301\n')

    n_files = sum(len(fs) for _, _, fs in os.walk(SITE))
    print(f'Build OK: {len(posts)} posts, {len(cats_sorted)} categorias, {len(used_images)} imagenes, {n_files} archivos totales')


if __name__ == '__main__':
    build()
