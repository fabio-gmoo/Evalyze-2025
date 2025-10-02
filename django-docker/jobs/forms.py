from django import forms  # type: ignore
from .models import Vacante

class VacanteForm(forms.ModelForm):
    class Meta:
        model = Vacante
        fields = ["puesto","descripcion","requisitos","ubicacion","salario","tipo_contrato","activa","departamento"]
