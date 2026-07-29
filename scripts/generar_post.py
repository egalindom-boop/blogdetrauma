# -*- coding: utf-8 -*-
"""Genera un post diario de traumatologia con la API de Claude y reconstruye el sitio.

Formato de respuesta con marcadores de seccion (inmune a errores de escape JSON):
===TITULO=== ... ===SLUG=== ... ===DESCRIPCION=== ... ===CATEGORIA=== ... ===CUERPO=== ... ===FIN===
"""
import json, os, re, sys, time, unicodedata
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.environ.get('ANTHROPIC_API_KEY')
MODEL = 'claude-sonnet-4-5'

CATEGORIAS_VALIDAS = [
    'Trauma', 'Fracturas', 'Artrosis', 'Artroscopia', 'Cirugía de Mano',
    'Lesiones de Muñeca', 'Cirugía Miembro Superior', 'Cirugía Miembro Inferior',
    'Cirugía del Pie', 'Columna', 'Medicina Deportiva', 'Osteoporosis',
]

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def elegir_tema():
    with open(os.path.join(ROOT, 'temas.txt'), encoding='utf-8') as f:
        temas = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    usados_path = os.path.join(ROOT, 'temas_usados.json')
    usados = []
    if os.path.exists(usados_path):
        usados = json.load(open(usados_path, encoding='utf-8'))
    pendientes = [t for t in temas if t not in usados]
    if not pendientes:
        usados = []
        pendientes = temas
    tema = pendientes[0]
    usados.append(tema)
    with open(usados_path, 'w', encoding='utf-8') as f:
        json.dump(usados, f, ensure_ascii=False, indent=2)
    return tema


def llamar_claude(tema):
    prompt = f"""Eres el Dr. Enrique Galindo Martens, especialista en Traumatología y Cirugía Ortopédica,
profesor de la Facultad de Medicina de la Universidad Europea, con fellowships en Miami (EEUU) y Perth (Australia).
Escribes en tu blog personal blogdetrauma.com, "La Traumatología dedicada a los pacientes", activo desde 2009.

Escribe un artículo divulgativo NUEVO y ORIGINAL sobre: {tema}

Estilo del blog:
- En español de España, primera persona del singular cuando proceda ("en mi consulta veo con frecuencia...").
- Dirigido a pacientes: lenguaje claro, cercano y riguroso; explica los términos médicos la primera vez que aparecen.
- Entre 700 y 1000 palabras.
- Estructura con subtítulos <h2> (síntomas, diagnóstico, tratamiento, recuperación, cuándo consultar...).
- Usa <p>, <h2>, <ul>/<li> y <strong>. NO uses <h1>, imágenes, enlaces externos ni scripts.
- Cierra siempre recordando que el contenido es divulgativo y no sustituye la consulta con un especialista.
- De forma natural y solo si encaja, puedes mencionar una vez que en consulta usas el software médico DriCloud (https://www.dricloud.com).

Responde EXACTAMENTE en este formato con marcadores, sin nada antes ni después:
===TITULO===
(título atractivo y claro, máximo 70 caracteres, sin comillas)
===SLUG===
(slug-en-minusculas-con-guiones, máximo 8 palabras)
===DESCRIPCION===
(meta descripción de 140-155 caracteres)
===CATEGORIA===
(UNA de: {', '.join(CATEGORIAS_VALIDAS)})
===CUERPO===
(el artículo completo en HTML)
===FIN===
"""
    body = json.dumps({
        'model': MODEL,
        'max_tokens': 4000,
        'messages': [{'role': 'user', 'content': prompt}],
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=body,
        headers={
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        })
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode('utf-8'))
    return data['content'][0]['text']


def extraer(texto, marca, siguiente):
    m = re.search(re.escape(f'==={marca}===') + r'(.*?)' + re.escape(f'==={siguiente}==='), texto, re.S)
    return m.group(1).strip() if m else None


def generar():
    tema = elegir_tema()
    print(f'Tema: {tema}')
    for intento in range(1, 4):
        try:
            texto = llamar_claude(tema)
            titulo = extraer(texto, 'TITULO', 'SLUG')
            slug = extraer(texto, 'SLUG', 'DESCRIPCION')
            desc = extraer(texto, 'DESCRIPCION', 'CATEGORIA')
            cat = extraer(texto, 'CATEGORIA', 'CUERPO')
            cuerpo = extraer(texto, 'CUERPO', 'FIN')
            if not all([titulo, slug, desc, cat, cuerpo]):
                raise ValueError('Faltan secciones en la respuesta')
            if len(cuerpo) < 500 or '<p>' not in cuerpo:
                raise ValueError('Cuerpo demasiado corto o sin <p>')
            cat = cat.strip()
            if cat not in CATEGORIAS_VALIDAS:
                cat = 'Trauma'
            slug = slugify(slug)[:80]
            break
        except Exception as e:
            print(f'Intento {intento} fallido: {e}')
            if intento == 3:
                sys.exit(1)
            time.sleep(20)

    posts_path = os.path.join(ROOT, 'posts.json')
    posts = json.load(open(posts_path, encoding='utf-8'))

    # evitar slug duplicado
    existentes = {p['slug'] for p in posts}
    base = slug
    i = 2
    while slug in existentes:
        slug = f'{base}-{i}'
        i += 1

    ahora = datetime.utcnow()
    nuevo = {
        'id': f'bot-{ahora.strftime("%Y%m%d%H%M")}',
        'title': titulo,
        'slug': slug,
        'link': f'https://blogdetrauma.com/{slug}/',
        'pubdate': ahora.strftime('%a, %d %b %Y %H:%M:%S +0000'),
        'postdate': ahora.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'publish',
        'content': cuerpo,
        'excerpt': desc,
        'categories': [{'name': cat, 'slug': slugify(cat)}],
        'tags': [],
    }
    posts.append(nuevo)
    with open(posts_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f'Post añadido: {titulo} -> /{slug}/ [{cat}]')


if __name__ == '__main__':
    if not API_KEY:
        print('Falta ANTHROPIC_API_KEY')
        sys.exit(1)
    generar()
