from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Edicion(models.Model):
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre"
    )
    anio = models.PositiveIntegerField(
        unique=True,
        verbose_name="A├▒o"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripci├│n"
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de inicio"
    )
    fecha_fin = models.DateField(
        verbose_name="Fecha de finalizaci├│n"
    )
    activa = models.BooleanField(
        default=False,
        verbose_name="Activa"
    )

    class Meta:
        verbose_name = "Edici├│n"
        verbose_name_plural = "Ediciones"
        ordering = ["-anio"]

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError(
                "La fecha de finalizaci├│n no puede ser anterior "
                "a la fecha de inicio."
            )

    def __str__(self):
        return f"{self.nombre} ({self.anio})"


class Categoria(models.Model):
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.CASCADE,
        related_name="categorias",
        verbose_name="Edici├│n"
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripci├│n"
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )

    class Meta:
        verbose_name = "Categor├¡a"
        verbose_name_plural = "Categor├¡as"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "nombre"],
                name="categoria_unica_por_edicion"
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.edicion.anio}"


class Votacion(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PROGRAMADA = "PROGRAMADA", "Programada"
        ABIERTA = "ABIERTA", "Abierta"
        CERRADA = "CERRADA", "Cerrada"

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="votaciones",
        verbose_name="Categor├¡a"
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name="T├¡tulo"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripci├│n"
    )
    fecha_apertura = models.DateTimeField(
        verbose_name="Fecha y hora de apertura"
    )
    fecha_cierre = models.DateTimeField(
        verbose_name="Fecha y hora de cierre"
    )
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        verbose_name="Estado"
    )

    class Meta:
        verbose_name = "Votaci├│n"
        verbose_name_plural = "Votaciones"
        ordering = ["-fecha_apertura"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "titulo"],
                name="votacion_unica_por_categoria"
            )
        ]

    def clean(self):
        if self.fecha_cierre <= self.fecha_apertura:
            raise ValidationError(
                "La fecha de cierre debe ser posterior "
                "a la fecha de apertura."
            )

    @property
    def esta_abierta(self):
        ahora = timezone.now()

        return (
            self.estado == self.Estado.ABIERTA
            and self.fecha_apertura <= ahora <= self.fecha_cierre
        )

    def __str__(self):
        return self.titulo


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name="opciones",
        verbose_name="Votaci├│n"
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripci├│n"
    )
    imagen_url = models.URLField(
        blank=True,
        verbose_name="URL de la imagen"
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden de visualizaci├│n"
    )

    class Meta:
        verbose_name = "Opci├│n"
        verbose_name_plural = "Opciones"
        ordering = ["orden", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["votacion", "nombre"],
                name="opcion_unica_por_votacion"
            )
        ]


class Voto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="votos",
        verbose_name="Usuario",
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.PROTECT,
        related_name="votos",
        verbose_name="Edici├│n",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="votos",
        verbose_name="Categor├¡a",
    )
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.PROTECT,
        related_name="votos",
        verbose_name="Votaci├│n",
    )
    opcion = models.ForeignKey(
        Opcion,
        on_delete=models.PROTECT,
        related_name="votos",
        verbose_name="Opci├│n",
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora",
    )

    class Meta:
        verbose_name = "Voto"
        verbose_name_plural = "Votos"
        ordering = ["-fecha_hora"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "categoria", "edicion"],
                name="voto_unico_usuario_categoria_edicion",
            )
        ]

    def clean(self):
        errores = {}

        if self.categoria_id and self.edicion_id:
            if self.categoria.edicion_id != self.edicion_id:
                errores["categoria"] = (
                    "La categor├¡a no pertenece a la edici├│n seleccionada."
                )

        if self.votacion_id and self.categoria_id:
            if self.votacion.categoria_id != self.categoria_id:
                errores["votacion"] = (
                    "La votaci├│n no pertenece a la categor├¡a seleccionada."
                )

        if self.opcion_id and self.votacion_id:
            if self.opcion.votacion_id != self.votacion_id:
                errores["opcion"] = (
                    "La opci├│n no pertenece a la votaci├│n seleccionada."
                )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.usuario} - {self.categoria} - "
            f"{self.opcion}"
        )



    def __str__(self):
        return f"{self.nombre} - {self.votacion.titulo}"


class Votante(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="registro_votante",
        null=True,
        blank=True,
        verbose_name="Cuenta de usuario",
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.CASCADE,
        related_name="votantes",
        verbose_name="Edici├│n",
    )
    documento = models.CharField(max_length=32, verbose_name="Documento")
    correo = models.EmailField(max_length=254, verbose_name="Correo")
    habilitado = models.BooleanField(default=True, verbose_name="Habilitado")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Registrado")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        verbose_name = "Votante"
        verbose_name_plural = "Votantes"
        ordering = ["documento"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "documento"],
                name="votante_unico_por_edicion",
            )
        ]

    def __str__(self):
        return f"{self.documento} - {self.edicion.anio}"
