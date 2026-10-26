import csv
import io

from django import forms
from django.core.exceptions import ValidationError

from .models import Categoria, Edicion, Opcion, Votacion


class EdicionForm(forms.ModelForm):
    class Meta:
        model = Edicion
        fields = [
            "nombre",
            "anio",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "activa",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "anio": forms.NumberInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error(
                "fecha_fin",
                "La fecha de finalización no puede ser anterior a la fecha de inicio.",
            )

        return cleaned_data


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["edicion", "nombre", "descripcion", "activa"]
        widgets = {
            "edicion": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class VotacionForm(forms.ModelForm):
    class Meta:
        model = Votacion
        fields = [
            "categoria",
            "titulo",
            "descripcion",
            "fecha_apertura",
            "fecha_cierre",
            "estado",
        ]
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "fecha_apertura": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "fecha_cierre": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }
        input_formats = ["%Y-%m-%dT%H:%M"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("fecha_apertura", "fecha_cierre"):
            self.fields[field_name].input_formats = ["%Y-%m-%dT%H:%M"]


class OpcionForm(forms.ModelForm):
    class Meta:
        model = Opcion
        fields = [
            "votacion",
            "nombre",
            "descripcion",
            "imagen_url",
            "activa",
            "orden",
        ]
        widgets = {
            "votacion": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "imagen_url": forms.URLInput(attrs={"class": "form-control"}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "orden": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class CensoUploadForm(forms.Form):
    edicion = forms.ModelChoiceField(
        queryset=Edicion.objects.all(),
        label="Edición del padrón",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    archivo = forms.FileField(
        label="Archivo CSV",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
    )

    max_file_size = 5 * 1024 * 1024
    max_rows = 10000
    max_reported_errors = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registros = []
        self.resumen_errores = []

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if not archivo.name.lower().endswith(".csv"):
            raise ValidationError("Selecciona un archivo con extensión .csv.")
        if archivo.size > self.max_file_size:
            raise ValidationError("El archivo no puede superar 5 MB.")

        try:
            contenido = archivo.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationError(
                "El archivo debe estar codificado como UTF-8."
            ) from exc

        try:
            try:
                dialect = csv.Sniffer().sniff(
                    contenido[:4096],
                    delimiters=",;",
                )
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(
                io.StringIO(contenido, newline=""),
                dialect=dialect,
            )
            if not reader.fieldnames:
                raise ValidationError("El CSV está vacío o no tiene encabezados.")

            encabezados = {
                (header or "").strip().lower(): header
                for header in reader.fieldnames
            }
            if "documento" not in encabezados or "correo" not in encabezados:
                raise ValidationError(
                    "El encabezado debe incluir las columnas documento y correo."
                )

            vistos = set()
            errores = []
            registros = []
            for numero_fila, fila in enumerate(reader, start=2):
                if numero_fila > self.max_rows + 1:
                    errores.append(
                        f"El archivo supera el límite de {self.max_rows} registros."
                    )
                    break

                documento = (fila.get(encabezados["documento"]) or "").strip().upper()
                correo = (fila.get(encabezados["correo"]) or "").strip().lower()
                if not documento and not correo:
                    continue

                errores_fila = []
                if None in fila:
                    errores_fila.append("hay más valores que columnas")
                if not documento:
                    errores_fila.append("documento vacío")
                elif len(documento) > 32:
                    errores_fila.append("documento supera 32 caracteres")
                if not correo:
                    errores_fila.append("correo vacío")
                else:
                    try:
                        forms.EmailField(max_length=254).clean(correo)
                    except ValidationError:
                        errores_fila.append("correo no válido")
                if documento and documento in vistos:
                    errores_fila.append("documento repetido en el archivo")
                if documento:
                    vistos.add(documento)

                if errores_fila:
                    errores.append(
                        f"Fila {numero_fila}: {', '.join(errores_fila)}."
                    )
                else:
                    registros.append(
                        {"documento": documento, "correo": correo}
                    )

            if not registros and not errores:
                errores.append("El archivo no contiene registros.")

        except csv.Error as exc:
            raise ValidationError("No se pudo interpretar el archivo CSV.") from exc

        if errores:
            self.resumen_errores = errores[: self.max_reported_errors]
            if len(errores) > self.max_reported_errors:
                self.resumen_errores.append(
                    f"Hay {len(errores) - self.max_reported_errors} errores adicionales."
                )
            raise ValidationError(
                f"El archivo tiene {len(errores)} fila(s) inválida(s). No se importó ningún registro."
            )

        self.registros = registros
        return archivo
