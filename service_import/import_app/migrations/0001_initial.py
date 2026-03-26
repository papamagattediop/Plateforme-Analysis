from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_fichier', models.CharField(help_text="Nom original du fichier uploadé", max_length=255)),
                ('fichier', models.FileField(help_text="Fichier stocké sur le serveur", upload_to='uploads/')),
                ('date_upload', models.DateTimeField(auto_now_add=True, help_text="Date/heure d'upload automatique")),
                ('date_modif', models.DateTimeField(auto_now=True, help_text="Dernière modification")),
                ('nb_lignes', models.IntegerField(default=0, help_text="Nombre de lignes après nettoyage")),
                ('nb_colonnes', models.IntegerField(default=0, help_text="Nombre de colonnes détectées")),
                ('has_date', models.BooleanField(default=False, help_text="True si une colonne datetime est détectée → active M5")),
                ('statut', models.CharField(
                    choices=[
                        ('en_attente', 'En attente de traitement'),
                        ('en_traitement', 'En cours de traitement'),
                        ('traite', 'Traité avec succès'),
                        ('erreur', 'Erreur lors du traitement'),
                    ],
                    default='en_attente',
                    max_length=20,
                )),
                ('rapport_nettoyage', models.JSONField(blank=True, default=dict, help_text="Rapport JSON")),
                ('donnees_json', models.JSONField(blank=True, default=list, help_text="Données nettoyées en JSON")),
            ],
            options={
                'verbose_name': 'Dataset',
                'verbose_name_plural': 'Datasets',
                'db_table': 'datasets',
                'ordering': ['-date_upload'],
            },
        ),
        migrations.CreateModel(
            name='ColonneInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset', models.ForeignKey(
                    help_text="Dataset auquel appartient cette colonne",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='colonnes',
                    to='import_app.dataset',
                )),
                ('nom', models.CharField(help_text="Nom de la colonne dans le fichier", max_length=255)),
                ('type_detecte', models.CharField(
                    choices=[
                        ('numeric', 'Numérique'),
                        ('categorical', 'Catégoriel'),
                        ('datetime', 'Date / Heure'),
                        ('text', 'Texte libre'),
                        ('boolean', 'Booléen'),
                        ('inconnu', 'Type inconnu'),
                    ],
                    help_text="Type détecté automatiquement par utils.py",
                    max_length=20,
                )),
                ('nb_valeurs_manquantes', models.IntegerField(default=0)),
                ('nb_valeurs_uniques', models.IntegerField(default=0)),
                ('exemple_valeurs', models.JSONField(blank=True, default=list, help_text="3-5 exemples de valeurs")),
            ],
            options={
                'verbose_name': 'Colonne',
                'verbose_name_plural': 'Colonnes',
                'db_table': 'colonnes_info',
                'ordering': ['nom'],
                'unique_together': {('dataset', 'nom')},
            },
        ),
        migrations.CreateModel(
            name='TraitementLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset', models.ForeignKey(
                    help_text="Dataset concerné",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='traitements',
                    to='import_app.dataset',
                )),
                ('type_traitement', models.CharField(
                    choices=[
                        ('import', 'Import initial'),
                        ('suppression_doublons', 'Suppression des doublons'),
                        ('suppression_vides', 'Suppression lignes vides'),
                        ('correction_types', 'Correction des types'),
                        ('renommage_colonne', 'Renommage de colonne'),
                        ('suppression_colonne', 'Suppression de colonne'),
                        ('remplacement_valeur', 'Remplacement de valeur'),
                        ('normalisation', 'Normalisation'),
                        ('encodage', 'Correction encodage'),
                        ('autre', 'Autre traitement'),
                    ],
                    max_length=30,
                )),
                ('description', models.TextField(help_text="Description lisible du traitement effectué")),
                ('date_traitement', models.DateTimeField(default=django.utils.timezone.now)),
                ('details', models.JSONField(blank=True, default=dict, help_text="Détails JSON")),
                ('snapshot_avant', models.JSONField(blank=True, default=list, help_text="Snapshot des données avant modification")),
            ],
            options={
                'verbose_name': 'Log de traitement',
                'verbose_name_plural': 'Logs de traitements',
                'db_table': 'traitements_log',
                'ordering': ['-date_traitement'],
            },
        ),
        migrations.CreateModel(
            name='ExportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset', models.ForeignKey(
                    help_text="Dataset exporté",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exports',
                    to='import_app.dataset',
                )),
                ('format_export', models.CharField(
                    choices=[('csv', 'CSV'), ('xlsx', 'Excel (.xlsx)'), ('json', 'JSON')],
                    max_length=10,
                )),
                ('date_export', models.DateTimeField(auto_now_add=True)),
                ('chemin_fichier', models.CharField(blank=True, help_text="Chemin du fichier exporté", max_length=500)),
            ],
            options={
                'verbose_name': 'Export',
                'verbose_name_plural': 'Exports',
                'db_table': 'exports_log',
                'ordering': ['-date_export'],
            },
        ),
    ]
