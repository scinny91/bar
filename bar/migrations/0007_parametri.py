# Generated by Django 5.2.3 on 2025-07-15 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bar', '0006_ordineriga_opzioni_alter_prodotto_sottocategoria'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parametri',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chiave', models.CharField(max_length=50, unique=True)),
                ('valore', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('stato', 'Stato ordine'), ('opzione', 'Opzione prodotto'), ('categorie', 'Categorie prototto'), ('sottocategorie', 'Sottocategorie prodotto')], max_length=20)),
            ],
            options={
                'verbose_name_plural': 'Parametri',
                'unique_together': {('chiave', 'valore', 'tipo')},
            },
        ),
    ]
