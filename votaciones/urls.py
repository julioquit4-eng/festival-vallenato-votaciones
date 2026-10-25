from django.urls import path

from . import views


public_patterns = (
    [
        path("", views.inicio, name="inicio"),
        path(
            "votaciones/",
            views.votaciones_publicas,
            name="votaciones",
        ),
        path(
            "votaciones/detalle/",
            views.detalle_votacion,
            name="detalle_votacion",
        ),
        path(
            "votaciones/acceso/",
            views.acceso_votante,
            name="acceso_votante",
        ),
        path(
            "votaciones/confirmar/",
            views.confirmar_voto,
            name="confirmar_voto",
        ),
        path(
            "votaciones/comprobante/",
            views.comprobante,
            name="comprobante",
        ),
        path(
            "resultados/",
            views.resultados,
            name="resultados",
        ),
        path(
            "guia/",
            views.guia,
            name="guia",
        ),
        path(
            "privacidad/",
            views.privacidad,
            name="privacidad",
        ),
        path(
            "login/",
            views.login,
            name="login",
        ),
    ],
    "public",
)


panel_patterns = (
    [
        path(
            "",
            views.panel_dashboard,
            name="dashboard",
        ),
        path(
            "ediciones/",
            views.panel_ediciones,
            name="ediciones",
        ),
        path(
            "categorias/",
            views.panel_categorias,
            name="categorias",
        ),
        path(
            "votaciones/",
            views.panel_votaciones,
            name="votaciones",
        ),
        path(
            "opciones/",
            views.panel_opciones,
            name="opciones",
        ),
        path(
            "votantes/",
            views.panel_votantes,
            name="votantes",
        ),
        path(
            "reportes/",
            views.panel_reportes,
            name="reportes",
        ),
    ],
    "panel",
)