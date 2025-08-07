# forms.py
from django import forms
from .models import ComponenteMagazzino, Prodotto, Magazzino

class ProdottoForm(forms.ModelForm):
    class Meta:
        model = Prodotto
        fields = ['nome', 'prezzo', 'categoria', 'sottocategoria', 'stato']

class ComponenteMagazzinoForm(forms.ModelForm):
    class Meta:
        model = ComponenteMagazzino
        fields = ['magazzino', 'quantita_utilizzata', 'percentuale_maggiorazione', 'bloccante']

ComponenteMagazzinoFormSet = forms.inlineformset_factory(
    Prodotto,
    ComponenteMagazzino,
    form=ComponenteMagazzinoForm,
    extra=1,
    can_delete=True
)