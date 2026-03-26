"""
Commande Django pour charger un fichier GeoJSON en base.

Usage :
    python manage.py charger_geojson \\
        --fichier senegal_regions.geojson \\
        --nom senegal_regions \\
        --label "Régions du Sénégal" \\
        --niveau region \\
        --cle_join nom_region
"""
import json
from django.core.management.base import BaseCommand, CommandError
from cartes_app.models import GeoJSONRegion


class Command(BaseCommand):
    help = 'Charge un fichier GeoJSON en base de données'

    def add_arguments(self, parser):
        parser.add_argument('--fichier',  required=True, help='Chemin vers le .geojson')
        parser.add_argument('--nom',      required=True, help='Identifiant unique (ex: senegal_regions)')
        parser.add_argument('--label',    required=True, help='Nom lisible (ex: Régions du Sénégal)')
        parser.add_argument('--niveau',   required=True, help='Niveau géo (region, departement, pays...)')
        parser.add_argument('--cle_join', required=True, help='Clé de jointure dans le GeoJSON')

    def handle(self, *args, **options):
        try:
            with open(options['fichier'], 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Fichier introuvable : {options['fichier']}")
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON invalide : {e}")

        # Vérifier que la clé de jointure existe dans au moins une feature
        features = geojson_data.get('features', [])
        if not features:
            raise CommandError("Le fichier GeoJSON ne contient aucune feature.")

        premiere = features[0].get('properties', {})
        if options['cle_join'] not in premiere:
            props_dispo = list(premiere.keys())
            raise CommandError(
                f"La clé '{options['cle_join']}' n'existe pas dans les propriétés.\n"
                f"Propriétés disponibles : {props_dispo}"
            )

        obj, created = GeoJSONRegion.objects.update_or_create(
            nom=options['nom'],
            defaults={
                'label':    options['label'],
                'niveau':   options['niveau'],
                'cle_join': options['cle_join'],
                'geojson':  geojson_data,
            },
        )

        action = 'Créé' if created else 'Mis à jour'
        nb_features = len(features)
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} : {obj.label} ({obj.nom}) — {nb_features} features"
            )
        )