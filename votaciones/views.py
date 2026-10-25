from django.shortcuts import render


# Portal público

def inicio(request):
    return render(request, "public/inicio.html")


def votaciones_publicas(request):
    return render(request, "public/votaciones.html")


def detalle_votacion(request):
    return render(request, "public/detalle_votacion.html")


def acceso_votante(request):
    return render(request, "public/acceso_votante.html")


def confirmar_voto(request):
    return render(request, "public/confirmar_voto.html")


def comprobante(request):
    return render(request, "public/comprobante.html")


def resultados(request):
    return render(request, "public/resultados.html")


def guia(request):
    return render(request, "public/guia.html")


def privacidad(request):
    return render(request, "public/privacidad.html")


def login(request):
    return render(request, "public/login.html")


# Panel administrativo personalizado

def panel_dashboard(request):
    return render(request, "panel/dashboard.html")


def panel_ediciones(request):
    return render(request, "panel/ediciones.html")


def panel_categorias(request):
    return render(request, "panel/categorias.html")


def panel_votaciones(request):
    return render(request, "panel/votaciones.html")


def panel_opciones(request):
    return render(request, "panel/opciones.html")


def panel_votantes(request):
    return render(request, "panel/votantes.html")


def panel_reportes(request):
    return render(request, "panel/reportes.html")