from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion, Voto


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "anio",
        "fecha_inicio",
        "fecha_fin",
        "activa",
    )
    list_filter = ("activa", "anio")
    search_fields = ("nombre", "descripcion")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "edicion",
        "activa",
    )
    list_filter = ("activa", "edicion")
    search_fields = ("nombre", "descripcion")


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "categoria",
        "estado",
        "fecha_apertura",
        "fecha_cierre",
    )
    list_filter = ("estado", "categoria")
    search_fields = ("titulo", "descripcion")


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "votacion",
        "activa",
        "orden",
    )
    list_filter = ("activa", "votacion")
    search_fields = ("nombre", "descripcion")


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "edicion",
        "categoria",
        "votacion",
        "opcion",
        "fecha_hora",
    )
    list_filter = (
        "edicion",
        "categoria",
        "votacion",
        "fecha_hora",
    )
    search_fields = (
        "usuario__username",
        "edicion__nombre",
        "categoria__nombre",
        "votacion__titulo",
        "opcion__nombre",
    )
