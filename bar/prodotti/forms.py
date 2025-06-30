from django import forms
from .models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO

class ProdottoForm(forms.ModelForm):
    categoria = forms.ChoiceField(
        choices=CATEGORIE_PRODOTTO,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sottocategoria = forms.ChoiceField(
        choices=SOTTOCATEGORIE_PRODOTTO,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Prodotto
        fields = ['nome', 'prezzo', 'categoria', 'sottocategoria']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'prezzo': forms.NumberInput(attrs={'class': 'form-control'}),
        }