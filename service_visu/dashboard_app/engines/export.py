"""
Moteur d'export PDF — ReportLab (compatible Windows sans GTK).
"""
from django.http import HttpResponse
import io


def exporter_dashboard_pdf(dashboard, widgets_data: list) -> HttpResponse:
    """
    Génère un PDF du dashboard avec ReportLab.
    Fonctionne sur Windows sans dépendances système (pas de GTK requis).
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, KeepTogether,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.graphics.shapes import Drawing, Rect, String
    except ImportError:
        raise ImportError(
            "ReportLab n'est pas installé. Lancez : pip install reportlab"
        )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.2*cm, bottomMargin=1.2*cm,
        title=dashboard.titre,
    )

    styles = getSampleStyleSheet()
    C_CLOUD  = colors.HexColor('#F0EEE9')
    C_BORDER = colors.HexColor('#E5E2DB')
    C_ACCENT = colors.HexColor('#2563EB')
    C_WHITE  = colors.white
    C_MUTED  = colors.HexColor('#8C9BAD')

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    s_titre    = ps('t', fontSize=15, fontName='Helvetica-Bold', textColor=colors.HexColor('#0D1B2A'), spaceAfter=2)
    s_meta     = ps('m', fontSize=9,  fontName='Helvetica',      textColor=colors.HexColor('#64748B'))
    s_brand    = ps('b', fontSize=12, fontName='Helvetica-Bold', textColor=C_ACCENT, alignment=TA_RIGHT)
    s_wt       = ps('wt', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#0D1B2A'), spaceAfter=6)
    s_cell     = ps('c',  fontSize=9,  fontName='Helvetica',      textColor=colors.HexColor('#0D1B2A'))
    s_th       = ps('th', fontSize=9,  fontName='Helvetica-Bold', textColor=colors.HexColor('#4A5568'))
    s_note     = ps('n',  fontSize=8,  fontName='Helvetica',      textColor=C_MUTED)
    s_empty    = ps('e',  fontSize=9,  fontName='Helvetica',      textColor=C_MUTED)

    elements = []
    page_w = landscape(A4)[0] - 3*cm

    # ── En-tête ───────────────────────────────────────────────────────────────
    date_str = dashboard.updated_at.strftime('%d/%m/%Y')
    header = Table([[
        Paragraph(
            f'<b>{dashboard.titre}</b><br/>'
            f'<font size="9" color="#64748B">'
            f'{dashboard.dataset_nom} · {dashboard.nb_widgets} widget(s) · {date_str}'
            f'</font>',
            s_titre,
        ),
        Paragraph('CensusAnalyse', s_brand),
    ]], colWidths=[page_w * 0.75, page_w * 0.25])
    header.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW',     (0,0), (-1,-1), 1.5, C_ACCENT),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 0.4*cm))

    col_w = (page_w - 0.5*cm) / 2

    def _widget_content(wd):
        widget = wd['widget']
        config = wd['config']
        items  = [Paragraph(widget.titre, s_wt)]

        if config.get('type') == 'table':
            colonnes = config.get('colonnes', [])
            lignes   = config.get('lignes', [])[:15]
            if colonnes:
                td = [[Paragraph(c, s_th) for c in colonnes]]
                for l in lignes:
                    td.append([Paragraph(str(v), s_cell) for v in l])
                cw = (col_w - 0.6*cm) / max(len(colonnes), 1)
                t = Table(td, colWidths=[cw]*len(colonnes), repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND',     (0,0), (-1,0), C_CLOUD),
                    ('GRID',           (0,0), (-1,-1), 0.5, C_BORDER),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_WHITE, C_CLOUD]),
                    ('FONTSIZE',       (0,0), (-1,-1), 9),
                    ('TOPPADDING',     (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING',  (0,0), (-1,-1), 3),
                    ('LEFTPADDING',    (0,0), (-1,-1), 5),
                    ('RIGHTPADDING',   (0,0), (-1,-1), 5),
                ]))
                items.append(t)
                nb = config.get('nb_total', len(lignes))
                if nb > 15:
                    items.append(Spacer(1, 3))
                    items.append(Paragraph(f'{nb} lignes — 15 affichées', s_note))

        elif config.get('data') and config['data'].get('labels'):
            labels  = config['data']['labels'][:12]
            ds      = config['data'].get('datasets', [])
            valeurs = ds[0].get('data', [])[:12] if ds else []

            if valeurs:
                vmax    = max((float(v) for v in valeurs if v is not None), default=1) or 1
                bar_h   = 10
                bar_gap = 5
                chart_w = col_w - 1.0*cm
                total_h = (bar_h + bar_gap) * len(valeurs) + 10

                d = Drawing(chart_w, total_h)
                for i, (lbl, val) in enumerate(zip(labels, valeurs)):
                    if val is None:
                        continue
                    vf    = float(val)
                    blen  = max((vf / vmax) * (chart_w - 95), 2)
                    y     = (len(valeurs) - i - 1) * (bar_h + bar_gap) + 5

                    r = Rect(90, y, blen, bar_h)
                    r.fillColor = C_ACCENT; r.strokeColor = None
                    d.add(r)

                    d.add(String(0, y+2, str(lbl)[:16], fontSize=7,
                                 fillColor=colors.HexColor('#4A5568')))

                    vs = f'{vf:,.0f}' if vf >= 100 else f'{vf:.1f}'
                    d.add(String(90 + blen + 4, y+2, vs, fontSize=7,
                                 fillColor=C_ACCENT))
                items.append(d)
        else:
            items.append(Paragraph('Données non disponibles', s_empty))

        return items

    # ── Grille 2 colonnes ─────────────────────────────────────────────────────
    for i in range(0, len(widgets_data), 2):
        pair = widgets_data[i:i+2]
        cells = []

        for wd in pair:
            inner = _widget_content(wd)
            ct = Table([[item] for item in inner], colWidths=[col_w - 0.4*cm])
            ct.setStyle(TableStyle([
                ('BOX',           (0,0), (-1,-1), 0.8, C_BORDER),
                ('BACKGROUND',    (0,0), (0,0),   C_CLOUD),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ]))
            cells.append(ct)

        while len(cells) < 2:
            cells.append(Paragraph('', styles['Normal']))

        row = Table([cells], colWidths=[col_w, col_w])
        row.setStyle(TableStyle([
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(KeepTogether(row))
        elements.append(Spacer(1, 0.3*cm))

    doc.build(elements)
    buffer.seek(0)

    nom = dashboard.titre.replace(' ', '_').lower()
    resp = HttpResponse(buffer.read(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{nom}.pdf"'
    return resp