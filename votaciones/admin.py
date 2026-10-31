from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion, Voto


admin.site.register(Edicion)
admin.site.register(Categoria)
admin.site.register(Votacion)
admin.site.register(Opcion)
admin.site.register(Voto)