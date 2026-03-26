"""
Moteur de génération de cartes — Folium.
"""
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from branca.colormap import LinearColormap


PALETTES = {
    'bleu':   ['#EFF6FF', '#BFDBFE', '#60A5FA', '#2563EB', '#1E3A8A'],
    'vert':   ['#F0FDF4', '#BBF7D0', '#4ADE80', '#16A34A', '#14532D'],
    'rouge':  ['#FFF1F2', '#FECDD3', '#FB7185', '#E11D48', '#881337'],
    'orange': ['#FFFBEB', '#FDE68A', '#FBBF24', '#D97706', '#78350F'],
    'violet': ['#F5F3FF', '#DDD6FE', '#A78BFA', '#7C3AED', '#3B0764'],
}

SENEGAL_BOUNDS = [[12.3, -17.5], [16.6, -11.4]]
SENEGAL_CENTER = [14.4974, -14.4524]


def generer_choropletre(
    df: pd.DataFrame,
    variable: str,
    colonne_geo: str,
    geojson_data: dict,
    cle_join: str,
    palette: str = 'bleu',
    titre: str = None,
    annee: str = None,
) -> str:

    # Filtrer par année si demandé
    if annee and 'annee' in df.columns:
        df = df[df['annee'].astype(str) == str(annee)]

    # Agréger
    df[variable] = pd.to_numeric(df[variable], errors='coerce')
    df_agg = df.groupby(colonne_geo)[variable].mean().reset_index()

    if df_agg.empty:
        raise ValueError(f"Aucune donnée pour '{variable}'")

    val_min = float(df_agg[variable].min())
    val_max = float(df_agg[variable].max())
    if val_min == val_max:
        val_max = val_min + 1

    # Détecter si les valeurs sont "grandes" (absolues > 2 chiffres)
    valeurs_grandes = val_max >= 100

    # ── Carte ─────────────────────────────────────────────────────────────────
    carte = folium.Map(
        location=SENEGAL_CENTER,
        zoom_start=7,
        tiles=None,
        min_zoom=6,
        max_zoom=10,
        max_bounds=True,
        scrollWheelZoom=False,
        zoom_control=False,   # on remet un zoom custom
    )

    # Fond clair sans labels de villes
    folium.TileLayer(
        tiles='https://cartodb-basemaps-a.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}.png',
        attr='&copy; CARTO',
        name='Fond',
        overlay=False,
        control=False,
    ).add_to(carte)

    carte.fit_bounds(SENEGAL_BOUNDS)

    # ── Colormap en 5 plages max ───────────────────────────────────────────────
    couleurs = PALETTES.get(palette, PALETTES['bleu'])
    colormap = LinearColormap(
        colors=couleurs,
        vmin=val_min,
        vmax=val_max,
        caption=titre or variable,
    )
    colormap.width = 180

    def get_couleur(feature):
        region_nom = feature['properties'].get(cle_join, '')
        ligne = df_agg[df_agg[colonne_geo] == region_nom]
        if ligne.empty or pd.isna(ligne[variable].values[0]):
            return '#E5E2DB'
        return colormap(float(ligne[variable].values[0]))

    # ── GeoJSON ───────────────────────────────────────────────────────────────
    folium.GeoJson(
        geojson_data,
        name='Régions',
        style_function=lambda feature: {
            'fillColor':   get_couleur(feature),
            'color':       '#FFFFFF',
            'weight':      2,
            'fillOpacity': 0.85,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[cle_join],
            aliases=['Région :'],
            localize=True,
            sticky=True,
            style=(
                'background-color:#1A2332;color:#E8EFF7;'
                'font-family:DM Sans,sans-serif;font-size:12px;'
                'padding:6px 10px;border-radius:6px;border:none;'
            ),
        ),
        highlight_function=lambda x: {
            'weight': 3,
            'color': '#2563EB',
            'fillOpacity': 0.95,
        },
    ).add_to(carte)

    # ── Labels sur la carte (seulement si valeurs courtes) ────────────────────
    if not valeurs_grandes:
        _ajouter_labels_regions(carte, df_agg, colonne_geo, variable, geojson_data, cle_join)

    # ── Légende 5 plages (en haut à droite) ───────────────────────────────────
    _ajouter_legende_plages(carte, df_agg, variable, val_min, val_max, couleurs, titre)

    # ── Flèche Nord (haut gauche) ─────────────────────────────────────────────
    _ajouter_fleche_nord(carte)

    # ── Barre d'échelle (bas gauche via CSS) ──────────────────────────────────
    # Leaflet scale est déjà en bas à gauche par défaut
    folium.plugins.MeasureControl(
        position='bottomleft',
        primary_length_unit='kilometers',
        secondary_length_unit=None,
        primary_area_unit='sqkilometers',
    ).add_to(carte)

    # ── CSS global ────────────────────────────────────────────────────────────
    _injecter_css(carte)

    return carte._repr_html_()


def _ajouter_legende_plages(carte, df_agg, variable, val_min, val_max, couleurs, titre):
    """Légende 5 plages en haut à droite."""
    step = (val_max - val_min) / 5
    plages = []
    for i in range(5):
        borne_bas = val_min + i * step
        borne_haut = val_min + (i + 1) * step
        couleur = couleurs[i] if i < len(couleurs) else couleurs[-1]
        if val_max >= 1000:
            label = f'{borne_bas:,.0f} – {borne_haut:,.0f}'
        elif val_max >= 100:
            label = f'{borne_bas:.0f} – {borne_haut:.0f}'
        else:
            label = f'{borne_bas:.1f} – {borne_haut:.1f}'
        plages.append((couleur, label))

    items_html = ''.join([
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:5px;">'
        f'<div style="width:16px;height:16px;border-radius:3px;'
        f'background:{c};flex-shrink:0;border:1px solid rgba(0,0,0,0.1);"></div>'
        f'<span style="font-size:11px;color:#1A2332;">{l}</span>'
        f'</div>'
        for c, l in plages
    ])

    legende_html = f"""
    <div id="legende-carte" style="
        position:absolute;
        top:12px; right:12px;
        z-index:1000;
        background:rgba(255,255,255,0.95);
        border:1px solid #E5E2DB;
        border-radius:10px;
        padding:12px 14px;
        box-shadow:0 2px 8px rgba(13,27,42,0.1);
        font-family:DM Sans,sans-serif;
        min-width:150px;
    ">
        <div style="font-size:11px;font-weight:700;color:#4A5568;
                    text-transform:uppercase;letter-spacing:0.06em;
                    margin-bottom:9px;">{titre or variable}</div>
        {items_html}
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legende_html))


def _ajouter_fleche_nord(carte):
    """Flèche Nord en haut à gauche."""
    fleche_html = """
    <div id="fleche-nord" style="
        position:absolute;
        top:12px; left:52px;
        z-index:1000;
        background:rgba(255,255,255,0.95);
        border:1px solid #E5E2DB;
        border-radius:8px;
        padding:7px 10px;
        box-shadow:0 2px 6px rgba(13,27,42,0.1);
        display:flex;
        flex-direction:column;
        align-items:center;
        gap:1px;
        font-family:DM Sans,sans-serif;
    ">
        <div style="font-size:20px;line-height:1;color:#1A2332;font-weight:700;">↑</div>
        <div style="font-size:10px;font-weight:700;color:#1A2332;
                    letter-spacing:0.08em;">N</div>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(fleche_html))


def _ajouter_labels_regions(carte, df_agg, colonne_geo, variable, geojson_data, cle_join):
    """Labels nom région + valeur au centre — seulement pour valeurs courtes."""
    try:
        for feature in geojson_data.get('features', []):
            region_nom = feature['properties'].get(cle_join, '')
            ligne = df_agg[df_agg[colonne_geo] == region_nom]

            if ligne.empty:
                continue

            valeur = ligne[variable].values[0]
            if pd.isna(valeur):
                continue

            coords    = feature['geometry'].get('coordinates', [])
            geom_type = feature['geometry'].get('type', '')

            if geom_type == 'Polygon' and coords:
                pts = coords[0]
            elif geom_type == 'MultiPolygon' and coords:
                pts = max(coords, key=lambda p: len(p[0]))[0]
            else:
                continue

            lat = sum(c[1] for c in pts) / len(pts)
            lon = sum(c[0] for c in pts) / len(pts)

            html = (
                '<div style="font-family:DM Sans,sans-serif;'
                'text-align:center;pointer-events:none;">'
                f'<div style="font-size:10px;font-weight:700;color:#1A2332;'
                f'text-shadow:0 1px 2px rgba(255,255,255,0.95);">{region_nom}</div>'
                f'<div style="font-size:11px;font-weight:600;color:#2563EB;'
                f'background:rgba(255,255,255,0.88);padding:1px 5px;'
                f'border-radius:4px;margin-top:2px;display:inline-block;">'
                f'{round(float(valeur), 1)}</div>'
                '</div>'
            )

            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html=html,
                    icon_size=(90, 36),
                    icon_anchor=(45, 18),
                ),
            ).add_to(carte)

    except Exception:
        pass


def _injecter_css(carte):
    """CSS global : fond blanc, légende compacte, barre d'échelle."""
    css = """
    <style>
        .leaflet-container {
            background: #F8F7F4 !important;
        }
        /* Masquer la colormap branca (on a notre propre légende) */
        .legend.leaflet-control {
            display: none !important;
        }
        /* Barre d'échelle : style épuré */
        .leaflet-control-scale-line {
            background: rgba(255,255,255,0.92) !important;
            border: 1px solid #E5E2DB !important;
            border-radius: 4px !important;
            font-family: 'DM Mono', monospace !important;
            font-size: 10px !important;
            color: #4A5568 !important;
            padding: 2px 6px !important;
        }
        /* Zoom control */
        .leaflet-control-zoom {
            border: 1px solid #E5E2DB !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(13,27,42,0.08) !important;
        }
        .leaflet-control-zoom a {
            background: rgba(255,255,255,0.95) !important;
            color: #1A2332 !important;
            font-weight: 600 !important;
        }
        .leaflet-control-zoom a:hover {
            background: #EFF6FF !important;
            color: #2563EB !important;
        }
        /* Masquer attribution Leaflet et CARTO */
        .leaflet-control-attribution {
            display: none !important;
        }
    </style>
    """
    carte.get_root().html.add_child(folium.Element(css))


# ── Heatmap ───────────────────────────────────────────────────────────────────
def generer_heatmap(
    df: pd.DataFrame,
    col_lat: str,
    col_lon: str,
    col_intensite: str = None,
    titre: str = None,
) -> str:
    df[col_lat] = pd.to_numeric(df[col_lat], errors='coerce')
    df[col_lon] = pd.to_numeric(df[col_lon], errors='coerce')
    df = df.dropna(subset=[col_lat, col_lon])

    if df.empty:
        raise ValueError("Aucune coordonnée GPS valide")

    carte = folium.Map(
        location=[df[col_lat].mean(), df[col_lon].mean()],
        zoom_start=7,
        tiles='CartoDB dark_matter',
    )

    if col_intensite and col_intensite in df.columns:
        df[col_intensite] = pd.to_numeric(df[col_intensite], errors='coerce')
        heat_data = df[[col_lat, col_lon, col_intensite]].dropna().values.tolist()
    else:
        heat_data = df[[col_lat, col_lon]].values.tolist()

    HeatMap(
        heat_data,
        radius=15, blur=10, min_opacity=0.3,
        gradient={0.4: '#3B82F6', 0.65: '#8B5CF6', 1.0: '#EF4444'},
    ).add_to(carte)

    return carte._repr_html_()


# ── Carte de points ───────────────────────────────────────────────────────────
def generer_carte_points(
    df: pd.DataFrame,
    col_lat: str,
    col_lon: str,
    col_label: str = None,
    col_couleur: str = None,
    titre: str = None,
) -> str:
    df[col_lat] = pd.to_numeric(df[col_lat], errors='coerce')
    df[col_lon] = pd.to_numeric(df[col_lon], errors='coerce')
    df = df.dropna(subset=[col_lat, col_lon])

    if df.empty:
        raise ValueError("Aucune coordonnée GPS valide")

    if len(df) > 5000:
        df = df.sample(5000, random_state=42)

    carte = folium.Map(
        location=[df[col_lat].mean(), df[col_lon].mean()],
        zoom_start=7, tiles='CartoDB positron',
    )

    cluster = MarkerCluster(name='Points').add_to(carte)

    for _, row in df.iterrows():
        popup_html = ''
        if col_label and col_label in row.index:
            popup_html = f'<b>{col_label}</b>: {row[col_label]}'
        if col_couleur and col_couleur in row.index:
            popup_html += f'<br><b>{col_couleur}</b>: {row[col_couleur]}'

        folium.CircleMarker(
            location=[row[col_lat], row[col_lon]],
            radius=6, color='#2563EB', fill=True,
            fill_color='#3B82F6', fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=200) if popup_html else None,
            tooltip=str(row[col_label]) if col_label and col_label in row.index else None,
        ).add_to(cluster)

    return carte._repr_html_()


# ── Comparaison 2 cartes ──────────────────────────────────────────────────────
def generer_comparaison(
    df: pd.DataFrame,
    variable_gauche: str,
    variable_droite: str,
    colonne_geo: str,
    geojson_data: dict,
    cle_join: str,
    palette: str = 'bleu',
) -> dict:
    html_g = generer_choropletre(
        df=df.copy(), variable=variable_gauche, colonne_geo=colonne_geo,
        geojson_data=geojson_data, cle_join=cle_join,
        palette=palette, titre=variable_gauche,
    )
    html_d = generer_choropletre(
        df=df.copy(), variable=variable_droite, colonne_geo=colonne_geo,
        geojson_data=geojson_data, cle_join=cle_join,
        palette=palette, titre=variable_droite,
    )
    return {
        'carte_gauche':    html_g,
        'carte_droite':    html_d,
        'variable_gauche': variable_gauche,
        'variable_droite': variable_droite,
    }