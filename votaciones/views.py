from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    AccesoVotanteForm,
    CategoriaForm,
    CensoUploadForm,
    ConfirmarVotoForm,
    EdicionForm,
    OpcionForm,
    VotoForm,
    VotacionForm,
)
from .models import Categoria, Edicion, Opcion, Votacion, Votante, Voto


def _votaciones_publicas():
    return (
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .filter(categoria__activa=True, categoria__edicion__activa=True)
        .exclude(estado=Votacion.Estado.BORRADOR)
    )


def _actualizar_estado_publico(votacion, ahora):
    if (
        votacion.estado == Votacion.Estado.ABIERTA
        and votacion.fecha_apertura <= ahora <= votacion.fecha_cierre
    ):
        votacion.estado_publico = "abierta"
    elif (
        votacion.estado in (Votacion.Estado.PROGRAMADA, Votacion.Estado.ABIERTA)
        and ahora < votacion.fecha_apertura
    ):
        votacion.estado_publico = "proxima"
    elif votacion.estado == Votacion.Estado.BORRADOR:
        votacion.estado_publico = "borrador"
    else:
        votacion.estado_publico = "cerrada"


def _votaciones_activas():
    ahora = timezone.now()
    votaciones = list(_votaciones_publicas())
    for votacion in votaciones:
        _actualizar_estado_publico(votacion, ahora)
    return votaciones


# Portal público

def inicio(request):
    return render(
        request,
        "public/inicio.html",
        {"votaciones_destacadas": list(_votaciones_activas()[:3])},
    )


def votaciones_publicas(request):
    votaciones = _votaciones_activas()
    return render(
        request,
        "public/votaciones.html",
        {
            "votaciones": votaciones,
            "total_votaciones": len(votaciones),
            "total_abiertas": sum(
                votacion.estado_publico == "abierta" for votacion in votaciones
            ),
            "total_proximas": sum(
                votacion.estado_publico == "proxima" for votacion in votaciones
            ),
            "total_cerradas": sum(
                votacion.estado_publico == "cerrada" for votacion in votaciones
            ),
            "edicion_activa": Edicion.objects.filter(activa=True).first(),
        },
    )


def detalle_votacion(request):
    votacion = get_object_or_404(
        _votaciones_publicas(),
        pk=request.GET.get("v"),
    )
    _actualizar_estado_publico(votacion, timezone.now())

    opciones = votacion.opciones.filter(activa=True)
    voto_url = reverse("public:emitir_voto", args=[votacion.pk])
    puede_votar = (
        request.user.is_authenticated
        and not request.user.is_staff
        and Votante.objects.filter(
            usuario=request.user,
            edicion=votacion.categoria.edicion,
            habilitado=True,
        ).exists()
    )
    return render(
        request,
        "public/detalle_votacion.html",
        {
            "votacion": votacion,
            "opciones": opciones,
            "voto_form": VotoForm(votacion),
            "voto_url": voto_url,
            "puede_votar": puede_votar,
            "votacion_habilitada": (
                votacion.esta_abierta
                and votacion.categoria.activa
                and votacion.categoria.edicion.activa
            ),
            "login_url": f"{reverse('public:login')}?next={voto_url}",
            "ya_voto": (
                request.user.is_authenticated
                and Voto.objects.filter(
                    usuario=request.user,
                    categoria=votacion.categoria,
                    edicion=votacion.categoria.edicion,
                ).exists()
            ),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def emitir_voto(request, votacion_id):
    votacion = get_object_or_404(
        Votacion.objects.select_related("categoria", "categoria__edicion"),
        pk=votacion_id,
    )
    esta_en_padron = Votante.objects.filter(
        usuario=request.user,
        edicion=votacion.categoria.edicion,
        habilitado=True,
    ).exists()
    if request.user.is_staff or not esta_en_padron:
        messages.error(
            request,
            "Solo un votante habilitado en el padrón de esta edición puede votar.",
        )
        return redirect("public:votaciones")

    votacion.estado_publico = (
        "abierta" if votacion.esta_abierta else "cerrada"
    )
    votar_url = reverse("public:emitir_voto", args=[votacion.pk])
    opciones = votacion.opciones.filter(activa=True)
    ya_voto = Voto.objects.filter(
        usuario=request.user,
        categoria=votacion.categoria,
        edicion=votacion.categoria.edicion,
    ).exists()

    if request.method == "GET":
        form = VotoForm(votacion)
        if not votacion.esta_abierta:
            messages.error(request, "Esta votación no está abierta.")
        elif not votacion.categoria.activa or not votacion.categoria.edicion.activa:
            messages.error(
                request,
                "La categoría o edición no está habilitada para votar.",
            )
        elif ya_voto:
            messages.error(request, "Ya registraste un voto en esta categoría.")
        return render(
            request,
            "public/detalle_votacion.html",
            {
                "votacion": votacion,
                "opciones": opciones,
                "voto_form": form,
                "voto_url": votar_url,
                "puede_votar": True,
                "votacion_habilitada": (
                    votacion.esta_abierta
                    and votacion.categoria.activa
                    and votacion.categoria.edicion.activa
                ),
                "ya_voto": ya_voto,
            },
        )

    if not votacion.esta_abierta:
        messages.error(request, "Esta votación no está abierta.")
    elif not votacion.categoria.activa or not votacion.categoria.edicion.activa:
        messages.error(
            request,
            "La categoría o edición no está habilitada para votar.",
        )
    elif ya_voto:
        messages.error(request, "Ya registraste un voto en esta categoría.")
    else:
        confirmation = request.POST.get("confirmar") == "1"
        form_class = ConfirmarVotoForm if confirmation else VotoForm
        form = form_class(votacion, request.POST)

        if form.is_valid():
            opcion = form.cleaned_data["opcion"]
            if not confirmation:
                return render(
                    request,
                    "public/confirmar_voto.html",
                    {
                        "votacion": votacion,
                        "opcion": opcion,
                        "voto_url": votar_url,
                    },
                )

            try:
                with transaction.atomic():
                    voto = Voto.objects.create(
                        usuario=request.user,
                        edicion=opcion.votacion.categoria.edicion,
                        categoria=opcion.votacion.categoria,
                        votacion=opcion.votacion,
                        opcion=opcion,
                    )
            except IntegrityError:
                if Voto.objects.filter(
                    usuario=request.user,
                    categoria=votacion.categoria,
                    edicion=votacion.categoria.edicion,
                ).exists():
                    messages.error(
                        request,
                        "Ya registraste un voto en esta categoría.",
                    )
                else:
                    raise
            except ValidationError:
                if Voto.objects.filter(
                    usuario=request.user,
                    categoria=votacion.categoria,
                    edicion=votacion.categoria.edicion,
                ).exists():
                    messages.error(
                        request,
                        "Ya registraste un voto en esta categoría.",
                    )
                else:
                    messages.error(
                        request,
                        "No fue posible validar la opción seleccionada.",
                    )
            else:
                messages.success(request, "Tu voto se registró correctamente.")
                return redirect(
                    "public:comprobante_voto",
                    voto_id=voto.pk,
                )
        else:
            for error in form.errors.get("opcion", []):
                messages.error(request, error)

    form = VotoForm(votacion, request.POST)
    return render(
        request,
        "public/detalle_votacion.html",
        {
            "votacion": votacion,
            "opciones": opciones,
            "voto_form": form,
            "voto_url": votar_url,
            "puede_votar": True,
            "votacion_habilitada": (
                votacion.esta_abierta
                and votacion.categoria.activa
                and votacion.categoria.edicion.activa
            ),
            "ya_voto": ya_voto,
        },
    )


def acceso_votante(request):
    return redirect("public:login")


def confirmar_voto(request):
    return redirect("public:votaciones")


def comprobante(request):
    return redirect("public:votaciones")


@login_required
def comprobante_voto(request, voto_id):
    voto = get_object_or_404(
        Voto.objects.select_related("categoria", "categoria__edicion", "votacion"),
        pk=voto_id,
        usuario=request.user,
    )
    return render(request, "public/comprobante.html", {"voto": voto})


@login_required
def categorias_votadas(request):
    votos = Voto.objects.filter(usuario=request.user).select_related(
        "categoria",
        "categoria__edicion",
        "votacion",
    )
    return render(
        request,
        "public/categorias_votadas.html",
        {"votos": votos},
    )


def resultados(request):
    return render(request, "public/resultados.html")


def guia(request):
    return render(request, "public/guia.html")


def privacidad(request):
    return render(request, "public/privacidad.html")


def login(request):
    if request.user.is_staff:
        return redirect("panel:dashboard")

    rol = request.POST.get("rol") or request.GET.get("rol")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if rol not in {"votante", "administrador"}:
        rol = (
            "administrador"
            if next_url.startswith(reverse("panel:dashboard"))
            else "votante"
        )

    admin_form = AuthenticationForm(
        request,
        data=request.POST
        if request.method == "POST" and rol == "administrador"
        else None,
    )
    votante_form = AccesoVotanteForm(
        request.POST if request.method == "POST" and rol == "votante" else None,
    )

    if request.method == "POST" and rol == "administrador":
        if admin_form.is_valid():
            usuario = admin_form.get_user()
            if not usuario.is_staff:
                admin_form.add_error(
                    None,
                    "Esta cuenta no tiene acceso al panel administrativo.",
                )
            else:
                auth_login(request, usuario)
                request.session.set_expiry(
                    None if request.POST.get("recordar_sesion") else 0
                )
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect("panel:dashboard")

    if request.method == "POST" and rol == "votante" and votante_form.is_valid():
        edicion = Edicion.objects.filter(activa=True).order_by("-anio").first()
        if edicion is None:
            votante_form.add_error(
                None,
                "El padrón de votantes no está habilitado actualmente.",
            )
        else:
            with transaction.atomic():
                votante = (
                    Votante.objects.select_for_update()
                    .select_related("usuario")
                    .filter(
                        edicion=edicion,
                        documento__iexact=votante_form.cleaned_data["documento"],
                        correo__iexact=votante_form.cleaned_data["correo"],
                        habilitado=True,
                    )
                    .first()
                )
                if votante is None:
                    votante_form.add_error(
                        None,
                        "El documento y correo no coinciden con un votante habilitado del padrón.",
                    )
                else:
                    usuario = votante.usuario
                    if usuario is None:
                        usuario_model = get_user_model()
                        usuario = usuario_model.objects.create_user(
                            username=f"votante-{uuid4().hex}",
                        )
                        usuario.set_unusable_password()
                        usuario.save(update_fields=["password"])
                        votante.usuario = usuario
                        votante.save(update_fields=["usuario", "actualizado_en"])

                    if not usuario.is_active or usuario.is_staff:
                        votante_form.add_error(
                            None,
                            "No fue posible iniciar sesión con este registro del padrón.",
                        )
                    else:
                        auth_login(
                            request,
                            usuario,
                            backend="django.contrib.auth.backends.ModelBackend",
                        )
                        if next_url and url_has_allowed_host_and_scheme(
                            next_url,
                            allowed_hosts={request.get_host()},
                            require_https=request.is_secure(),
                        ):
                            return redirect(next_url)
                        return redirect("public:votaciones")

    return render(
        request,
        "public/login.html",
        {
            "admin_form": admin_form,
            "votante_form": votante_form,
            "active_tab": rol,
            "next": next_url,
        },
    )


@require_POST
def cerrar_sesion(request):
    auth_logout(request)
    return redirect("public:inicio")


# Panel administrativo personalizado

@staff_member_required(login_url="public:login")
def panel_dashboard(request):
    ahora = timezone.now()
    edicion_padron = Edicion.objects.filter(activa=True).first()
    total_votantes = (
        Votante.objects.filter(edicion=edicion_padron).count()
        if edicion_padron
        else 0
    )
    total_ediciones = Edicion.objects.count()
    total_categorias = Categoria.objects.filter(activa=True).count()
    votaciones_abiertas = _votaciones_publicas().filter(
        estado=Votacion.Estado.ABIERTA,
        fecha_apertura__lte=ahora,
        fecha_cierre__gte=ahora,
    ).count()
    votaciones = list(
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .order_by("-fecha_apertura")[:10]
    )
    for votacion in votaciones:
        if not votacion.categoria.activa or not votacion.categoria.edicion.activa:
            votacion.estado_publico = "no_disponible"
        else:
            _actualizar_estado_publico(votacion, ahora)

    alertas = []
    if not edicion_padron:
        alertas.append({
            "tipo": "warning",
            "titulo": "No hay una edición activa",
            "texto": "Activa una edición para administrar su padrón de votantes.",
        })
    elif total_votantes == 0:
        alertas.append({
            "tipo": "warning",
            "titulo": "Padrón sin registros",
            "texto": f"La edición {edicion_padron.anio} todavía no tiene votantes.",
        })
    if total_categorias == 0:
        alertas.append({
            "tipo": "warning",
            "titulo": "No hay categorías habilitadas",
            "texto": "Crea o habilita categorías para configurar procesos de votación.",
        })
    if votaciones_abiertas == 0:
        alertas.append({
            "tipo": "info",
            "titulo": "Sin votaciones abiertas",
            "texto": "No hay procesos abiertos para participación en este momento.",
        })

    return render(
        request,
        "panel/dashboard.html",
        {
            "edicion_padron": edicion_padron,
            "total_votantes": total_votantes,
            "total_ediciones": total_ediciones,
            "total_categorias": total_categorias,
            "total_votaciones_abiertas": votaciones_abiertas,
            "votaciones": votaciones,
            "alertas": alertas,
        },
    )


@staff_member_required(login_url="public:login")
def panel_ediciones(request):
    ediciones = Edicion.objects.annotate(
        total_categorias=Count("categorias", distinct=True),
        total_votantes=Count("votantes", distinct=True),
    ).order_by("-anio")
    edicion_form = EdicionForm()

    if request.method == "POST":
        edicion_form = EdicionForm(request.POST)
        if edicion_form.is_valid():
            edicion_form.save()
            messages.success(request, "Edición guardada correctamente.")
            return redirect("panel:ediciones")

    return render(
        request,
        "panel/ediciones.html",
        {"ediciones": ediciones, "edicion_form": edicion_form},
    )


@staff_member_required(login_url="public:login")
@require_POST
def panel_eliminar_edicion(request, pk):
    with transaction.atomic():
        edicion = get_object_or_404(
            Edicion.objects.select_for_update(),
            pk=pk,
        )
        if edicion.categorias.exists() or edicion.votantes.exists():
            messages.error(
                request,
                "No se puede eliminar una edición que tiene categorías o votantes asociados.",
            )
        else:
            edicion.delete()
            messages.success(request, "Edición eliminada correctamente.")
    return redirect("panel:ediciones")


@staff_member_required(login_url="public:login")
def panel_categorias(request):
    categorias = Categoria.objects.select_related("edicion").order_by("edicion__anio", "nombre")
    form = CategoriaForm()

    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría guardada correctamente.")
            return redirect("panel:categorias")

    return render(
        request,
        "panel/categorias.html",
        {
            "categorias": categorias,
            "form": form,
            "hay_ediciones": Edicion.objects.exists(),
        },
    )


@staff_member_required(login_url="public:login")
def panel_editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    votacion_abierta = categoria.votaciones.filter(
        estado=Votacion.Estado.ABIERTA,
        fecha_apertura__lte=timezone.now(),
        fecha_cierre__gte=timezone.now(),
    ).exists()
    if votacion_abierta:
        messages.error(request, "No se puede modificar una categoría con una votación abierta.")
        return redirect("panel:categorias")

    form = CategoriaForm(request.POST or None, instance=categoria)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría actualizada correctamente.")
        return redirect("panel:categorias")

    return render(
        request,
        "panel/editar_categoria.html",
        {"categoria": categoria, "form": form},
    )


@staff_member_required(login_url="public:login")
@require_POST
def panel_eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if categoria.votaciones.exists():
        messages.error(
            request,
            "No se puede eliminar una categoría que ya tiene votaciones asociadas.",
        )
    else:
        categoria.delete()
        messages.success(request, "Categoría eliminada correctamente.")
    return redirect("panel:categorias")


@staff_member_required(login_url="public:login")
def panel_votaciones(request):
    votaciones = (
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .order_by("-fecha_apertura")
    )
    for votacion in votaciones:
        _actualizar_estado_publico(votacion, timezone.now())

    return render(
        request,
        "panel/votaciones.html",
        {"votaciones": votaciones, "form": VotacionForm()},
    )


@staff_member_required(login_url="public:login")
def panel_crear_votacion(request):
    if request.method != "POST":
        return redirect("panel:votaciones")

    form = VotacionForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Votación creada correctamente.")
        return redirect("panel:votaciones")

    votaciones = (
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .order_by("-fecha_apertura")
    )
    for votacion in votaciones:
        _actualizar_estado_publico(votacion, timezone.now())
    return render(
        request,
        "panel/votaciones.html",
        {"votaciones": votaciones, "form": form},
    )


@staff_member_required(login_url="public:login")
def panel_editar_votacion(request, pk):
    votacion = get_object_or_404(
        Votacion.objects.select_related("categoria", "categoria__edicion"),
        pk=pk,
    )
    if votacion.esta_abierta:
        messages.error(request, "No se puede modificar una votación abierta.")
        return redirect("panel:votaciones")

    form = VotacionForm(request.POST or None, instance=votacion)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Votación actualizada correctamente.")
        return redirect("panel:votaciones")

    return render(
        request,
        "panel/editar_votacion.html",
        {"form": form, "votacion": votacion},
    )


@staff_member_required(login_url="public:login")
@require_POST
def panel_eliminar_votacion(request, pk):
    votacion = get_object_or_404(Votacion, pk=pk)
    if votacion.esta_abierta:
        messages.error(request, "No se puede eliminar una votación abierta.")
    else:
        votacion.delete()
        messages.success(request, "Votación eliminada correctamente.")
    return redirect("panel:votaciones")


@staff_member_required(login_url="public:login")
def panel_opciones(request):
    votaciones = (
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .order_by("-fecha_apertura")
    )
    opciones = Opcion.objects.select_related(
        "votacion", "votacion__categoria", "votacion__categoria__edicion"
    ).order_by("votacion__titulo", "orden", "nombre")
    return render(
        request,
        "panel/opciones.html",
        {"votaciones": votaciones, "opciones": opciones, "form": OpcionForm()},
    )


@staff_member_required(login_url="public:login")
def panel_crear_opcion(request):
    if request.method != "POST":
        return redirect("panel:opciones")

    form = OpcionForm(request.POST)
    if form.is_valid():
        opcion = form.save(commit=False)
        if opcion.votacion.esta_abierta:
            form.add_error(
                "votacion",
                "No se pueden agregar opciones a una votación abierta.",
            )
        else:
            opcion.save()
            messages.success(request, "Opción agregada correctamente.")
            return redirect("panel:opciones")

    votaciones = (
        Votacion.objects.select_related("categoria", "categoria__edicion")
        .order_by("-fecha_apertura")
    )
    opciones = Opcion.objects.select_related(
        "votacion", "votacion__categoria", "votacion__categoria__edicion"
    ).order_by("votacion__titulo", "orden", "nombre")
    return render(
        request,
        "panel/opciones.html",
        {"votaciones": votaciones, "opciones": opciones, "form": form},
    )


@staff_member_required(login_url="public:login")
def panel_editar_opcion(request, pk):
    opcion = get_object_or_404(
        Opcion.objects.select_related("votacion"),
        pk=pk,
    )
    if opcion.votacion.esta_abierta:
        messages.error(request, "No se puede modificar una opción de una votación abierta.")
        return redirect("panel:opciones")

    form = OpcionForm(request.POST or None, instance=opcion)
    if request.method == "POST" and form.is_valid():
        updated_option = form.save(commit=False)
        if updated_option.votacion.esta_abierta:
            form.add_error(
                "votacion",
                "No se pueden asignar opciones a una votación abierta.",
            )
        else:
            updated_option.save()
            messages.success(request, "Opción actualizada correctamente.")
            return redirect("panel:opciones")

    return render(
        request,
        "panel/editar_opcion.html",
        {"form": form, "opcion": opcion},
    )


@staff_member_required(login_url="public:login")
@require_POST
def panel_eliminar_opcion(request, pk):
    opcion = get_object_or_404(Opcion.objects.select_related("votacion"), pk=pk)
    if opcion.votacion.esta_abierta:
        messages.error(request, "No se puede eliminar una opción de una votación abierta.")
    else:
        opcion.delete()
        messages.success(request, "Opción eliminada correctamente.")
    return redirect("panel:opciones")


@staff_member_required(login_url="public:login")
def panel_votantes(request):
    edicion_por_defecto = (
        Edicion.objects.filter(activa=True).first() or Edicion.objects.first()
    )
    selected_id = request.GET.get("edicion")
    if request.method == "POST":
        form = CensoUploadForm(request.POST, request.FILES)
        selected_id = request.POST.get("edicion")
        if form.is_valid():
            edicion = form.cleaned_data["edicion"]
            creados = 0
            actualizados = 0
            with transaction.atomic():
                for registro in form.registros:
                    _, creado = Votante.objects.update_or_create(
                        edicion=edicion,
                        documento=registro["documento"],
                        defaults={
                            "correo": registro["correo"],
                            "habilitado": True,
                        },
                    )
                    if creado:
                        creados += 1
                    else:
                        actualizados += 1
            messages.success(
                request,
                f"Padrón actualizado: {creados} nuevo(s), "
                f"{actualizados} actualizado(s) para {edicion.nombre}.",
            )
            return redirect(f"{reverse('panel:votantes')}?edicion={edicion.pk}")
    else:
        form = CensoUploadForm()

    selected_edicion = Edicion.objects.filter(pk=selected_id).first()
    if selected_edicion is None:
        selected_edicion = edicion_por_defecto
    if request.method == "GET" and selected_edicion:
        form.initial["edicion"] = selected_edicion.pk

    registros = Votante.objects.none()
    total_votantes = 0
    page_obj = None
    if selected_edicion:
        queryset = Votante.objects.filter(edicion=selected_edicion).order_by(
            "documento"
        )
        total_votantes = queryset.count()
        page_obj = Paginator(queryset, 50).get_page(request.GET.get("page"))
        registros = [
            {
                "documento": _enmascarar_documento(votante.documento),
                "correo": _enmascarar_correo(votante.correo),
                "habilitado": votante.habilitado,
            }
            for votante in page_obj.object_list
        ]

    return render(
        request,
        "panel/votantes.html",
        {
            "form": form,
            "ediciones": Edicion.objects.all(),
            "selected_edicion": selected_edicion,
            "votantes": registros,
            "total_votantes": total_votantes,
            "page_obj": page_obj,
            "upload_errors": getattr(form, "resumen_errores", []),
        },
    )


def _enmascarar_documento(documento):
    if len(documento) <= 4:
        return "••••"
    return f"{'•' * (len(documento) - 4)}{documento[-4:]}"


def _enmascarar_correo(correo):
    usuario, separador, dominio = correo.partition("@")
    if not separador:
        return "••••"
    return f"{usuario[:1]}•••@{dominio}"


@staff_member_required(login_url="public:login")
def panel_reportes(request):
    return render(request, "panel/reportes.html")