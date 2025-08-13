import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bar_site.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print("✅ Superuser 'admin' creato.")
else:
    print("ℹ️ Superuser 'admin' già esistente.")


from bar.core import Stato
# Lista degli stati da inserire
stati = [
    ('non_trovato', 'Non trovato'),
    ('completato', 'Completato'),
    ('in_preparazione', 'In Preparazione'),
    ('in_attesa', 'In Attesa'),
    ('pronto', 'Pronto'),
    ('parzialmente_completato', 'Parzialmente evaso'),
]

for chiave, valore in stati:
    if not Stato.objects.filter(chiave=chiave).exists():
        Stato.objects.create(chiave=chiave, valore=valore)
        print(f"✅ Stato '{chiave}' creato.")
    else:
        print(f"ℹ️ Stato '{chiave}' già esistente.")