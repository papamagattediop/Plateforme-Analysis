"""
utils.py — Dev 1 · Utilitaires de traitement
=============================================
Contient toutes les fonctions pures (sans Django) pour :
  - Lire un fichier CSV ou Excel avec pandas
  - Nettoyer le DataFrame (doublons, vides, encodage)
  - Détecter les types de colonnes
  - Générer un rapport de nettoyage complet
  - Sérialiser un DataFrame en JSON sûr
"""

import io
import json
import pandas as pd
import numpy as np
from datetime import datetime


# ─────────────────────────────────────────────
# 1. LECTURE DU FICHIER
# ─────────────────────────────────────────────

def lire_fichier(fichier) -> pd.DataFrame:
    """
    Lit un fichier uploadé (CSV ou Excel) et retourne un DataFrame pandas.
    Gère automatiquement les encodages courants (UTF-8, Latin-1, CP1252).

    Args:
        fichier: InMemoryUploadedFile Django

    Returns:
        pd.DataFrame

    Raises:
        ValueError si le format n'est pas supporté ou si la lecture échoue
    """
    nom = fichier.name.lower()

    # Lecture Excel (.xlsx ou .xls)
    if nom.endswith(('.xlsx', '.xls')):
        try:
            return pd.read_excel(fichier, engine='openpyxl' if nom.endswith('.xlsx') else 'xlrd')
        except Exception as e:
            raise ValueError(f"Impossible de lire le fichier Excel : {e}")

    # Lecture CSV avec détection automatique de l'encodage
    if nom.endswith('.csv'):
        # On essaie plusieurs encodages dans l'ordre
        encodages = ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']
        contenu = fichier.read()  # Lire les bytes une seule fois

        for encodage in encodages:
            try:
                df = pd.read_csv(
                    io.BytesIO(contenu),
                    encoding=encodage,
                    sep=None,          # Détection automatique du séparateur (,  ;  \t)
                    engine='python',
                    on_bad_lines='skip' # Ignorer les lignes malformées
                )
                return df
            except (UnicodeDecodeError, Exception):
                continue  # Essayer l'encodage suivant

        raise ValueError("Impossible de décoder le fichier CSV. Vérifiez l'encodage.")

    raise ValueError(f"Format '{nom.split('.')[-1]}' non supporté. Utilisez CSV ou Excel.")


# ─────────────────────────────────────────────
# 2. NETTOYAGE DU DATAFRAME
# ─────────────────────────────────────────────

def nettoyer_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Applique un nettoyage automatique complet sur le DataFrame.
    Retourne le DataFrame nettoyé + un rapport détaillé.

    Opérations effectuées :
      1. Suppression des lignes entièrement vides
      2. Suppression des doublons exacts
      3. Nettoyage des noms de colonnes (espaces, casse)
      4. Correction des séparateurs décimaux (virgule → point)
      5. Suppression des espaces en trop dans les chaînes

    Args:
        df: DataFrame brut

    Returns:
        (df_nettoye, rapport) où rapport est un dict JSON-sérialisable
    """
    rapport = {
        'nb_lignes_initiales':  len(df),
        'nb_colonnes_initiales': len(df.columns),
        'operations': []  # Liste des opérations effectuées
    }

    # ── Étape 1 : Nettoyage des noms de colonnes ──
    colonnes_avant = list(df.columns)
    df.columns = (
        df.columns
        .str.strip()                   # Supprimer les espaces en début/fin
        .str.lower()                   # Mettre en minuscules
        .str.replace(r'\s+', '_', regex=True)  # Espaces → underscores
        .str.replace(r'[^\w]', '_', regex=True) # Caractères spéciaux → underscores
    )
    colonnes_renommees = [
        {'avant': a, 'apres': b}
        for a, b in zip(colonnes_avant, df.columns)
        if a != b
    ]
    if colonnes_renommees:
        rapport['operations'].append({
            'type': 'renommage_colonnes',
            'detail': colonnes_renommees
        })

    # ── Étape 2 : Suppression des lignes entièrement vides ──
    nb_avant = len(df)
    df = df.dropna(how='all')
    nb_lignes_vides = nb_avant - len(df)
    rapport['operations'].append({
        'type': 'suppression_lignes_vides',
        'nb_supprimees': nb_lignes_vides
    })

    # ── Étape 3 : Suppression des doublons exacts ──
    nb_avant = len(df)
    df = df.drop_duplicates()
    nb_doublons = nb_avant - len(df)
    rapport['operations'].append({
        'type': 'suppression_doublons',
        'nb_supprimes': nb_doublons
    })

    # ── Étape 4 : Correction des virgules décimales → points ──
    colonnes_corrigees = []
    for col in df.columns:
        if df[col].dtype == object:
            # Détecter si la colonne contient des nombres avec virgule (ex: "3,14")
            test = df[col].dropna().astype(str).str.match(r'^\d+,\d+$')
            if test.any():
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                try:
                    df[col] = pd.to_numeric(df[col])
                    colonnes_corrigees.append(col)
                except Exception:
                    pass  # Pas convertible, on laisse en texte

    if colonnes_corrigees:
        rapport['operations'].append({
            'type': 'correction_decimales',
            'colonnes': colonnes_corrigees
        })

    # ── Étape 5 : Suppression des espaces superflus dans les strings ──
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

    # ── Résumé final ──
    rapport['nb_lignes_finales']  = len(df)
    rapport['nb_colonnes_finales'] = len(df.columns)
    rapport['nb_lignes_supprimees_total'] = rapport['nb_lignes_initiales'] - len(df)

    return df, rapport


# ─────────────────────────────────────────────
# 3. DÉTECTION DES TYPES DE COLONNES
# ─────────────────────────────────────────────

def detect_types(df: pd.DataFrame) -> dict:
    """
    Analyse chaque colonne du DataFrame et retourne un dict {nom_colonne: type}.

    Types possibles : 'numeric', 'categorical', 'datetime', 'text', 'boolean'

    La règle datetime est importante : si une colonne est détectée comme date,
    le flag has_date du Dataset sera mis à True → active M5 chez Dev 2.

    Args:
        df: DataFrame nettoyé

    Returns:
        dict {nom_colonne: type_string}
    """
    types = {}

    for col in df.columns:
        serie = df[col].dropna()

        # Colonne vide → inconnu
        if len(serie) == 0:
            types[col] = 'inconnu'
            continue

        # ── Booléen ──
        if pd.api.types.is_bool_dtype(serie):
            types[col] = 'boolean'
            continue

        # ── Numérique (int ou float détecté par pandas) ──
        if pd.api.types.is_numeric_dtype(serie):
            types[col] = 'numeric'
            continue

        # ── Datetime déjà parsé par pandas ──
        if pd.api.types.is_datetime64_any_dtype(serie):
            types[col] = 'datetime'
            continue

        # ── Tentative de conversion datetime sur les colonnes texte ──
        if serie.dtype == object:
            # Vérification rapide par regex avant d'appeler pd.to_datetime
            sample = serie.head(20).astype(str)
            import re
            _DATE_RE = re.compile(
                r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}'   # YYYY-MM-DD ou YYYY/MM/DD
                r'|^\d{1,2}[-/]\d{1,2}[-/]\d{4}'  # DD-MM-YYYY
                r'|^\d{4}\d{2}\d{2}$'              # YYYYMMDD
            )
            if sample.str.match(_DATE_RE).mean() >= 0.8:
                try:
                    pd.to_datetime(sample, errors='raise')
                    types[col] = 'datetime'
                    continue
                except Exception:
                    pass

            # ── Catégoriel vs Texte libre ──
            # Heuristique : si le ratio valeurs_uniques / total < 5% → catégoriel
            nb_unique = serie.nunique()
            ratio_unique = nb_unique / len(serie)

            if nb_unique <= 2:
                # Seulement 2 valeurs distinctes → probablement booléen/binaire
                types[col] = 'categorical'
            elif ratio_unique < 0.05 or nb_unique < 30:
                # Peu de valeurs uniques → catégoriel (ex: région, sexe, statut)
                types[col] = 'categorical'
            else:
                # Beaucoup de valeurs uniques → texte libre (ex: noms, adresses)
                types[col] = 'text'
            continue

        # Fallback
        types[col] = 'inconnu'

    return types


# ─────────────────────────────────────────────
# 4. STATISTIQUES PAR COLONNE (pour ColonneInfo)
# ─────────────────────────────────────────────

def stats_colonne(df: pd.DataFrame, col: str) -> dict:
    """
    Calcule les statistiques rapides d'une colonne pour pré-remplir ColonneInfo.
    Ces stats sont transmises à Dev 2 pour éviter des recalculs.

    Returns:
        dict avec nb_manquantes, nb_uniques, exemples
    """
    serie = df[col]
    exemples = serie.dropna().head(5).tolist()

    # Convertir les types numpy en types Python natifs pour JSON
    exemples = [
        val.item() if isinstance(val, (np.integer, np.floating)) else val
        for val in exemples
    ]

    return {
        'nb_valeurs_manquantes': int(serie.isna().sum()),
        'nb_valeurs_uniques':    int(serie.nunique()),
        'exemple_valeurs':       exemples,
    }


# ─────────────────────────────────────────────
# 5. SÉRIALISATION JSON SÛRE
# ─────────────────────────────────────────────

def dataframe_to_json(df: pd.DataFrame) -> list:
    """
    Convertit un DataFrame en liste de dicts JSON-sérialisables.
    Gère les types numpy (int64, float64, NaT, NaN) qui ne sont pas
    sérialisables par défaut.

    Returns:
        list de dicts (un dict par ligne)
    """
    # Convertir les dates en string ISO
    for col in df.select_dtypes(include=['datetime64']).columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d').where(df[col].notna(), None)

    # Remplacer NaN/NaT par None (→ null en JSON)
    df = df.where(pd.notnull(df), None)

    # Convertir en records
    records = df.to_dict(orient='records')

    # Convertir les types numpy restants
    def convertir(val):
        if isinstance(val, (np.integer,)):
            return int(val)
        if isinstance(val, (np.floating,)):
            return float(val) if not np.isnan(val) else None
        if isinstance(val, np.bool_):
            return bool(val)
        return val

    return [
        {k: convertir(v) for k, v in row.items()}
        for row in records
    ]
