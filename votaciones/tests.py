from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Votante, Voto


class AdminAuthenticationTests(TestCase):
    def setUp(self):
        hoy = timezone.localdate()
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2088,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=3),
            activa=True,
        )
        self.admin = get_user_model().objects.create_user(
            username="admin",
            password="secure-test-password",
            is_staff=True,
        )

    def crear_votante(self, **overrides):
        datos = {
            "edicion": self.edicion,
            "documento": "12345678",
            "correo": "persona@example.com",
            "habilitado": True,
        }
        datos.update(overrides)
        return Votante.objects.create(**datos)

    def test_panel_requires_authenticated_staff_user(self):
        panel_routes = (
            "dashboard",
            "ediciones",
            "categorias",
            "votaciones",
            "opciones",
            "votantes",
            "reportes",
        )
        for route_name in panel_routes:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(f"panel:{route_name}"))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("public:login")))

    def test_staff_user_can_log_in_and_open_panel(self):
        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "administrador",
                "username": "admin",
                "password": "secure-test-password",
            },
        )

        self.assertRedirects(response, reverse("panel:dashboard"))
        self.assertEqual(
            self.client.get(reverse("panel:dashboard")).status_code,
            200,
        )

    def test_staff_login_does_not_redirect_to_external_url(self):
        response = self.client.post(
            reverse("public:login"),
            {
                "username": "admin",
                "password": "secure-test-password",
                "rol": "administrador",
                "next": "https://example.com/",
            },
        )

        self.assertRedirects(response, reverse("panel:dashboard"))

    def test_staff_login_redirects_to_requested_panel_page(self):
        response = self.client.post(
            f"{reverse('public:login')}?next={reverse('panel:votaciones')}",
            {
                "rol": "administrador",
                "username": "admin",
                "password": "secure-test-password",
            },
        )

        self.assertRedirects(response, reverse("panel:votaciones"))

    def test_non_staff_user_cannot_log_in_to_panel(self):
        get_user_model().objects.create_user(
            username="voter",
            password="secure-test-password",
        )

        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "administrador",
                "username": "voter",
                "password": "secure-test-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no tiene acceso al panel administrativo")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_administrator_login_rejects_an_incorrect_password(self):
        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "administrador",
                "username": "admin",
                "password": "cualquier-clave",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(reverse("public:cerrar_sesion"))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse("public:cerrar_sesion"))
        self.assertRedirects(post_response, reverse("public:inicio"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_page_has_voter_and_administrator_tabs(self):
        response = self.client.get(reverse("public:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acceso de Votantes:")
        self.assertContains(response, "Número de cédula")
        self.assertContains(response, "Área Administrativa:")
        self.assertContains(response, "Contraseña")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertNotContains(response, "cualquier clave")

    def test_voter_login_validates_roster_and_creates_django_session(self):
        votante = self.crear_votante()

        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": "12345678",
                "correo": "PERSONA@example.com",
                "acepta_datos": "on",
            },
        )

        self.assertRedirects(response, reverse("public:votaciones"))
        votante.refresh_from_db()
        self.assertIsNotNone(votante.usuario)
        self.assertTrue(votante.usuario.is_active)
        self.assertFalse(votante.usuario.is_staff)
        self.assertFalse(votante.usuario.has_usable_password())
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(votante.usuario_id),
        )
        usuario_id = votante.usuario_id
        self.client.post(
            reverse("public:cerrar_sesion"),
        )
        self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": "12345678",
                "correo": "persona@example.com",
                "acepta_datos": "on",
            },
        )
        votante.refresh_from_db()
        self.assertEqual(votante.usuario_id, usuario_id)
        self.assertEqual(get_user_model().objects.filter(is_staff=False).count(), 1)

    def test_voter_login_rejects_wrong_email_and_disabled_roster_entry(self):
        votante = self.crear_votante()
        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": votante.documento,
                "correo": "incorrecto@example.com",
                "acepta_datos": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "no coinciden con un votante habilitado del padrón",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

        votante.habilitado = False
        votante.save()
        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": votante.documento,
                "correo": votante.correo,
                "acepta_datos": "on",
            },
        )
        self.assertContains(
            response,
            "no coinciden con un votante habilitado del padrón",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_voter_login_requires_accepting_data_policy(self):
        self.crear_votante()

        response = self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": "12345678",
                "correo": "persona@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Debes aceptar la política de tratamiento de datos.",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_legacy_voter_access_route_uses_real_login(self):
        response = self.client.get(reverse("public:acceso_votante"))

        self.assertRedirects(response, reverse("public:login"))

    def test_voter_login_does_not_grant_panel_access(self):
        self.crear_votante()
        self.client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": "12345678",
                "correo": "persona@example.com",
                "acepta_datos": "on",
            },
        )

        response = self.client.get(reverse("panel:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("public:login")))

    def test_login_forms_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("public:login"))

        admin_response = client.post(
            reverse("public:login"),
            {
                "rol": "administrador",
                "username": self.admin.username,
                "password": "secure-test-password",
            },
        )
        self.assertEqual(admin_response.status_code, 403)

        voter_response = client.post(
            reverse("public:login"),
            {
                "rol": "votante",
                "documento": "12345678",
                "correo": "persona@example.com",
                "acepta_datos": "on",
            },
        )
        self.assertEqual(voter_response.status_code, 403)


class PublicVotingViewsTests(TestCase):
    def setUp(self):
        hoy = timezone.localdate()
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2090,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=3),
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Acordeonero",
        )
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Acordeonero profesional",
            descripcion="Votación pública de prueba.",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )
        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Participante uno",
        )

    def test_public_list_renders_current_database_votations(self):
        response = self.client.get(reverse("public:votaciones"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.votacion.titulo)
        self.assertContains(response, "Abierta")
        self.assertContains(response, 'id="countTodas">1</span>')
        self.assertContains(response, 'id="countAbiertas">1</span>')
        self.assertContains(response, 'data-source="database"')

    def test_public_list_counts_only_enabled_model_votations_by_live_status(self):
        ahora = timezone.now()
        self.votacion.estado = Votacion.Estado.PROGRAMADA
        self.votacion.fecha_apertura = ahora + timedelta(days=1)
        self.votacion.fecha_cierre = ahora + timedelta(days=2)
        self.votacion.save()
        Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votación cerrada",
            fecha_apertura=ahora - timedelta(days=3),
            fecha_cierre=ahora - timedelta(days=2),
            estado=Votacion.Estado.CERRADA,
        )
        Votacion.objects.create(
            categoria=self.categoria,
            titulo="Borrador privado",
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado=Votacion.Estado.BORRADOR,
        )
        categoria_inactiva = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría deshabilitada",
            activa=False,
        )
        Votacion.objects.create(
            categoria=categoria_inactiva,
            titulo="Votación no habilitada",
            fecha_apertura=ahora,
            fecha_cierre=ahora + timedelta(days=1),
            estado=Votacion.Estado.ABIERTA,
        )

        response = self.client.get(reverse("public:votaciones"))

        self.assertContains(response, 'id="countTodas">2</span>')
        self.assertContains(response, 'id="countProximas">1</span>')
        self.assertContains(response, 'id="countCerradas">1</span>')
        self.assertContains(response, "Votación cerrada")
        self.assertNotContains(response, "Borrador privado")
        self.assertNotContains(response, "Votación no habilitada")

    def test_detail_renders_only_active_options_for_selected_votation(self):
        response = self.client.get(
            reverse("public:detalle_votacion"),
            {"v": self.votacion.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.opcion.nombre)
        self.assertContains(response, "Inicia sesión como votante")

    def test_detail_returns_not_found_for_missing_votation(self):
        response = self.client.get(
            reverse("public:detalle_votacion"),
            {"v": self.votacion.pk + 100},
        )

        self.assertEqual(response.status_code, 404)

    def test_public_list_shows_empty_state_without_active_editions(self):
        self.edicion.activa = False
        self.edicion.save(update_fields=["activa"])

        response = self.client.get(reverse("public:votaciones"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No encontramos votaciones")


class AdminModelManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="manager",
            password="secure-test-password",
            is_staff=True,
        )
        self.client.force_login(self.admin)
        hoy = timezone.localdate()
        self.edicion = Edicion.objects.create(
            nombre="Festival de gestión",
            anio=2091,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=3),
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Acordeonero",
        )

    def crear_votacion(self, **overrides):
        ahora = timezone.now()
        valores = {
            "categoria": self.categoria,
            "titulo": "Concurso de prueba",
            "descripcion": "",
            "fecha_apertura": ahora + timedelta(days=1),
            "fecha_cierre": ahora + timedelta(days=2),
            "estado": Votacion.Estado.PROGRAMADA,
        }
        valores.update(overrides)
        return Votacion.objects.create(**valores)

    def test_created_edition_is_rendered_from_database(self):
        inicio = timezone.localdate() + timedelta(days=10)
        fin = inicio + timedelta(days=4)
        response = self.client.post(
            reverse("panel:ediciones"),
            {
                "nombre": "Nueva edición guardada",
                "anio": 2092,
                "descripcion": "Edición de prueba",
                "fecha_inicio": inicio.isoformat(),
                "fecha_fin": fin.isoformat(),
                "activa": "on",
            },
        )

        self.assertRedirects(response, reverse("panel:ediciones"))
        listing = self.client.get(reverse("panel:ediciones"))
        self.assertContains(listing, "Nueva edición guardada")
        self.assertContains(listing, 'data-source="database"')
        self.assertNotContains(listing, "histórico de demostración")

    def test_empty_edition_can_be_deleted_from_panel(self):
        edicion = Edicion.objects.create(
            nombre="Edición para eliminar",
            anio=2093,
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate() + timedelta(days=2),
        )
        listing = self.client.get(reverse("panel:ediciones"))
        self.assertContains(
            listing,
            reverse("panel:eliminar_edicion", args=[edicion.pk]),
        )

        response = self.client.post(
            reverse("panel:eliminar_edicion", args=[edicion.pk])
        )

        self.assertRedirects(response, reverse("panel:ediciones"))
        self.assertFalse(Edicion.objects.filter(pk=edicion.pk).exists())

    def test_edition_with_categories_or_voters_cannot_be_deleted(self):
        response = self.client.post(
            reverse("panel:eliminar_edicion", args=[self.edicion.pk])
        )

        self.assertRedirects(response, reverse("panel:ediciones"))
        self.assertTrue(Edicion.objects.filter(pk=self.edicion.pk).exists())
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertContains(
            self.client.get(reverse("panel:ediciones")),
            "Tiene registros asociados",
        )

        self.categoria.delete()
        Votante.objects.create(
            edicion=self.edicion,
            documento="12345678",
            correo="voter@example.com",
        )
        response = self.client.post(
            reverse("panel:eliminar_edicion", args=[self.edicion.pk])
        )

        self.assertRedirects(response, reverse("panel:ediciones"))
        self.assertTrue(Edicion.objects.filter(pk=self.edicion.pk).exists())
        self.assertTrue(Votante.objects.filter(edicion=self.edicion).exists())

    def test_management_pages_render_model_records(self):
        votacion = self.crear_votacion()
        opcion = Opcion.objects.create(votacion=votacion, nombre="Participante")

        categories_response = self.client.get(reverse("panel:categorias"))
        votes_response = self.client.get(reverse("panel:votaciones"))
        options_response = self.client.get(reverse("panel:opciones"))

        self.assertEqual(categories_response.status_code, 200)
        self.assertContains(categories_response, self.categoria.nombre)
        self.assertContains(categories_response, self.edicion.nombre)
        self.assertNotContains(categories_response, "Ediciones Registradas")
        self.assertEqual(votes_response.status_code, 200)
        self.assertContains(votes_response, votacion.titulo)
        self.assertEqual(options_response.status_code, 200)
        self.assertContains(options_response, opcion.nombre)

    def test_create_edit_and_delete_category(self):
        create_response = self.client.post(
            reverse("panel:categorias"),
            {
                "edicion": self.edicion.pk,
                "nombre": "Piqueria",
                "descripcion": "Competencia de improvisación",
                "activa": "on",
            },
        )
        self.assertRedirects(create_response, reverse("panel:categorias"))
        categoria = Categoria.objects.get(nombre="Piqueria")

        edit_response = self.client.post(
            reverse("panel:editar_categoria", args=[categoria.pk]),
            {
                "edicion": self.edicion.pk,
                "nombre": "Piqueria profesional",
                "descripcion": "Categoría actualizada",
                "activa": "on",
            },
        )
        self.assertRedirects(edit_response, reverse("panel:categorias"))
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, "Piqueria profesional")

        delete_response = self.client.post(
            reverse("panel:eliminar_categoria", args=[categoria.pk])
        )
        self.assertRedirects(delete_response, reverse("panel:categorias"))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_category_with_votations_cannot_be_deleted(self):
        self.crear_votacion()
        response = self.client.post(
            reverse("panel:eliminar_categoria", args=[self.categoria.pk])
        )

        self.assertRedirects(response, reverse("panel:categorias"))
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_import_census_csv_and_mask_pii_in_panel(self):
        csv_file = SimpleUploadedFile(
            "padron.csv",
            b"documento,correo\n123456789,persona@example.com\nABC-9876,otra@example.org\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk, "archivo": csv_file},
        )

        self.assertRedirects(
            response,
            f"{reverse('panel:votantes')}?edicion={self.edicion.pk}",
        )
        self.assertEqual(Votante.objects.filter(edicion=self.edicion).count(), 2)
        self.assertTrue(
            Votante.objects.filter(
                edicion=self.edicion,
                documento="123456789",
                correo="persona@example.com",
                habilitado=True,
            ).exists()
        )

        listing = self.client.get(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk},
        )
        self.assertContains(listing, "•••••6789")
        self.assertContains(listing, "p•••@example.com")
        self.assertNotContains(listing, "123456789")
        self.assertNotContains(listing, "persona@example.com")

    def test_import_semicolon_csv(self):
        csv_file = SimpleUploadedFile(
            "padron.csv",
            "documento;correo\n11223344;persona@example.com\n".encode(),
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk, "archivo": csv_file},
        )

        self.assertRedirects(
            response,
            f"{reverse('panel:votantes')}?edicion={self.edicion.pk}",
        )
        self.assertTrue(
            Votante.objects.filter(
                edicion=self.edicion,
                documento="11223344",
            ).exists()
        )

    def test_dashboard_shows_live_roster_count_for_active_edition(self):
        Votante.objects.create(
            edicion=self.edicion,
            documento="12345678",
            correo="first@example.com",
        )
        Votante.objects.create(
            edicion=self.edicion,
            documento="87654321",
            correo="second@example.com",
        )

        response = self.client.get(reverse("panel:dashboard"))

        self.assertContains(response, 'id="kpiVotantes">2</div>')
        self.assertContains(response, f"Votantes en Padrón ({self.edicion.anio})")

    def test_dashboard_metrics_and_recent_processes_use_database_records(self):
        ahora = timezone.now()
        abierta = self.crear_votacion(
            titulo="Votación vigente",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )
        self.crear_votacion(
            titulo="Votación futura",
            fecha_apertura=ahora + timedelta(days=1),
            fecha_cierre=ahora + timedelta(days=2),
            estado=Votacion.Estado.ABIERTA,
        )
        categoria_inactiva = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría deshabilitada",
            activa=False,
        )
        Votacion.objects.create(
            categoria=categoria_inactiva,
            titulo="Proceso no público",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )

        response = self.client.get(reverse("panel:dashboard"))

        self.assertContains(response, 'id="kpiEdiciones">1</div>')
        self.assertContains(response, 'id="kpiCategorias">1</div>')
        self.assertContains(response, 'id="kpiAbiertas">1</div>')
        self.assertContains(response, abierta.titulo)
        self.assertContains(response, "Próximamente")
        self.assertContains(response, "Proceso no público")
        self.assertContains(response, "No disponible")
        self.assertNotContains(response, "modo prototipo")
        self.assertNotContains(response, "registros de demostración")
        self.assertContains(response, 'data-source="database"')

    def test_invalid_census_csv_is_rejected_without_partial_import(self):
        csv_file = SimpleUploadedFile(
            "padron.csv",
            b"documento,correo\n123456789,persona@example.com\n,correo-invalido\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk, "archivo": csv_file},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se importó ningún registro")
        self.assertContains(response, "Fila 3")
        self.assertEqual(Votante.objects.filter(edicion=self.edicion).count(), 0)

    def test_duplicate_document_in_upload_rejects_entire_file(self):
        csv_file = SimpleUploadedFile(
            "padron.csv",
            b"documento,correo\n123456789,persona@example.com\n123456789,otra@example.com\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk, "archivo": csv_file},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "documento repetido en el archivo")
        self.assertEqual(Votante.objects.filter(edicion=self.edicion).count(), 0)

    def test_census_import_updates_existing_document_without_deleting_others(self):
        existing = Votante.objects.create(
            edicion=self.edicion,
            documento="123456789",
            correo="old@example.com",
        )
        untouched = Votante.objects.create(
            edicion=self.edicion,
            documento="99887766",
            correo="other@example.com",
        )
        csv_file = SimpleUploadedFile(
            "padron.csv",
            b"documento,correo\n123456789,new@example.com\n",
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("panel:votantes"),
            {"edicion": self.edicion.pk, "archivo": csv_file},
        )

        self.assertRedirects(
            response,
            f"{reverse('panel:votantes')}?edicion={self.edicion.pk}",
        )
        existing.refresh_from_db()
        self.assertEqual(existing.correo, "new@example.com")
        self.assertTrue(Votante.objects.filter(pk=untouched.pk).exists())
        self.assertEqual(Votante.objects.filter(edicion=self.edicion).count(), 2)

    def test_create_votation_from_panel_form(self):
        apertura = timezone.localtime(timezone.now() + timedelta(days=1))
        cierre = timezone.localtime(timezone.now() + timedelta(days=2))

        response = self.client.post(
            reverse("panel:crear_votacion"),
            {
                "categoria": self.categoria.pk,
                "titulo": "Nueva competencia",
                "descripcion": "Descripción de prueba",
                "fecha_apertura": apertura.strftime("%Y-%m-%dT%H:%M"),
                "fecha_cierre": cierre.strftime("%Y-%m-%dT%H:%M"),
                "estado": Votacion.Estado.PROGRAMADA,
            },
        )

        self.assertRedirects(response, reverse("panel:votaciones"))
        self.assertTrue(Votacion.objects.filter(titulo="Nueva competencia").exists())

    def test_create_and_delete_option_from_panel(self):
        votacion = self.crear_votacion()
        create_response = self.client.post(
            reverse("panel:crear_opcion"),
            {
                "votacion": votacion.pk,
                "nombre": "Participante nuevo",
                "descripcion": "",
                "imagen_url": "",
                "orden": 0,
            },
        )

        self.assertRedirects(create_response, reverse("panel:opciones"))
        opcion = Opcion.objects.get(votacion=votacion)
        delete_response = self.client.post(
            reverse("panel:eliminar_opcion", args=[opcion.pk])
        )
        self.assertRedirects(delete_response, reverse("panel:opciones"))
        self.assertFalse(Opcion.objects.filter(pk=opcion.pk).exists())

    def test_edit_votation_and_option_from_panel(self):
        votacion = self.crear_votacion()
        apertura = timezone.localtime(timezone.now() + timedelta(days=3))
        cierre = timezone.localtime(timezone.now() + timedelta(days=4))
        response = self.client.post(
            reverse("panel:editar_votacion", args=[votacion.pk]),
            {
                "categoria": self.categoria.pk,
                "titulo": "Concurso actualizado",
                "descripcion": "Actualizada",
                "fecha_apertura": apertura.strftime("%Y-%m-%dT%H:%M"),
                "fecha_cierre": cierre.strftime("%Y-%m-%dT%H:%M"),
                "estado": Votacion.Estado.PROGRAMADA,
            },
        )
        self.assertRedirects(response, reverse("panel:votaciones"))
        votacion.refresh_from_db()
        self.assertEqual(votacion.titulo, "Concurso actualizado")

        opcion = Opcion.objects.create(votacion=votacion, nombre="Nombre anterior")
        response = self.client.post(
            reverse("panel:editar_opcion", args=[opcion.pk]),
            {
                "votacion": votacion.pk,
                "nombre": "Nombre actualizado",
                "descripcion": "Nueva descripción",
                "imagen_url": "",
                "orden": 2,
                "activa": "on",
            },
        )
        self.assertRedirects(response, reverse("panel:opciones"))
        opcion.refresh_from_db()
        self.assertEqual(opcion.nombre, "Nombre actualizado")
        self.assertEqual(opcion.orden, 2)

    def test_open_votation_cannot_be_edited_or_deleted(self):
        ahora = timezone.now()
        votacion = self.crear_votacion(
            fecha_apertura=ahora - timedelta(minutes=5),
            fecha_cierre=ahora + timedelta(minutes=5),
            estado=Votacion.Estado.ABIERTA,
        )

        edit_response = self.client.post(
            reverse("panel:editar_votacion", args=[votacion.pk]),
            {"titulo": "Cambio no permitido"},
        )
        delete_response = self.client.post(
            reverse("panel:eliminar_votacion", args=[votacion.pk])
        )

        votacion.refresh_from_db()
        self.assertRedirects(edit_response, reverse("panel:votaciones"))
        self.assertRedirects(delete_response, reverse("panel:votaciones"))
        self.assertEqual(votacion.titulo, "Concurso de prueba")
        self.assertTrue(Votacion.objects.filter(pk=votacion.pk).exists())

    def test_open_votation_options_cannot_be_added_edited_or_deleted(self):
        ahora = timezone.now()
        votacion = self.crear_votacion(
            fecha_apertura=ahora - timedelta(minutes=5),
            fecha_cierre=ahora + timedelta(minutes=5),
            estado=Votacion.Estado.ABIERTA,
        )
        opcion = Opcion.objects.create(votacion=votacion, nombre="Participante")

        create_response = self.client.post(
            reverse("panel:crear_opcion"),
            {
                "votacion": votacion.pk,
                "nombre": "Otro participante",
                "descripcion": "",
                "imagen_url": "",
                "orden": 0,
            },
        )
        edit_response = self.client.post(
            reverse("panel:editar_opcion", args=[opcion.pk]),
            {
                "votacion": votacion.pk,
                "nombre": "Nombre cambiado",
                "descripcion": "",
                "imagen_url": "",
                "orden": 0,
                "activa": "on",
            },
        )
        delete_response = self.client.post(
            reverse("panel:eliminar_opcion", args=[opcion.pk])
        )

        opcion.refresh_from_db()
        self.assertEqual(Opcion.objects.filter(votacion=votacion).count(), 1)
        self.assertEqual(opcion.nombre, "Participante")
        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "No se pueden agregar opciones")
        self.assertRedirects(edit_response, reverse("panel:opciones"))
        self.assertRedirects(delete_response, reverse("panel:opciones"))


class VotoModelTests(TestCase):
    def setUp(self):
        usuario_model = get_user_model()

        self.usuario = usuario_model.objects.create_user(
            username="votante_prueba",
            password="ClaveSegura123!",
        )

        hoy = timezone.localdate()
        ahora = timezone.now()

        self.edicion = Edicion.objects.create(
            nombre="Festival Vallenato",
            anio=2027,
            descripcion="Edición de prueba",
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=5),
            activa=True,
        )

        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Acordeonero profesional",
            descripcion="Categoría de prueba",
            activa=True,
        )

        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votación principal",
            descripcion="Votación de prueba",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )

        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Participante uno",
            descripcion="Opción de prueba",
            activa=True,
            orden=1,
        )

    def test_registra_voto_valido(self):
        voto = Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        self.assertEqual(Voto.objects.count(), 1)
        self.assertEqual(voto.usuario, self.usuario)
        self.assertEqual(voto.categoria, self.categoria)
        self.assertEqual(voto.edicion, self.edicion)

    def test_rechaza_segundo_voto_en_misma_categoria_y_edicion(self):
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        with self.assertRaises(ValidationError):
            Voto.objects.create(
                usuario=self.usuario,
                edicion=self.edicion,
                categoria=self.categoria,
                votacion=self.votacion,
                opcion=self.opcion,
            )

        self.assertEqual(Voto.objects.count(), 1)

    def test_permite_votar_en_categoria_diferente(self):
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Canción inédita",
            descripcion="Segunda categoría",
            activa=True,
        )

        otra_votacion = Votacion.objects.create(
            categoria=otra_categoria,
            titulo="Votación canción inédita",
            fecha_apertura=timezone.now() - timedelta(hours=1),
            fecha_cierre=timezone.now() + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )

        otra_opcion = Opcion.objects.create(
            votacion=otra_votacion,
            nombre="Canción de prueba",
            activa=True,
            orden=1,
        )

        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=otra_categoria,
            votacion=otra_votacion,
            opcion=otra_opcion,
        )

        self.assertEqual(Voto.objects.count(), 2)

    def test_rechaza_opcion_de_otra_votacion(self):
        otra_votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Otra votación",
            fecha_apertura=timezone.now() - timedelta(hours=1),
            fecha_cierre=timezone.now() + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )

        opcion_incorrecta = Opcion.objects.create(
            votacion=otra_votacion,
            nombre="Opción incorrecta",
            activa=True,
            orden=1,
        )

        with self.assertRaises(ValidationError):
            Voto.objects.create(
                usuario=self.usuario,
                edicion=self.edicion,
                categoria=self.categoria,
                votacion=self.votacion,
                opcion=opcion_incorrecta,
            )

        self.assertEqual(Voto.objects.count(), 0)


class FlujoRegistroVotoTests(TestCase):
    def setUp(self):
        usuario_model = get_user_model()
        hoy = timezone.localdate()
        ahora = timezone.now()
        self.edicion = Edicion.objects.create(
            nombre="Festival del voto",
            anio=2093,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=5),
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Acordeonero profesional",
            activa=True,
        )
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Elección de prueba",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )
        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Participante habilitado",
            activa=True,
        )
        self.usuario = usuario_model.objects.create_user(
            username="votante_flujo",
            password="ClaveSegura123!",
        )
        self.votante = Votante.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            documento="88776655",
            correo="votante@example.com",
            habilitado=True,
        )
        self.url = reverse(
            "public:emitir_voto",
            args=[self.votacion.pk],
        )
        self.client.force_login(self.usuario)

    def confirmar_voto(self, opcion=None):
        return self.client.post(
            self.url,
            {
                "opcion": (opcion or self.opcion).pk,
                "confirmar": "1",
            },
        )

    def test_registra_voto_valido_solo_despues_de_confirmacion_post(self):
        seleccion = self.client.post(
            self.url,
            {"opcion": self.opcion.pk},
        )

        self.assertEqual(seleccion.status_code, 200)
        self.assertContains(seleccion, "Confirma tu elección")
        self.assertContains(seleccion, "csrfmiddlewaretoken")
        self.assertEqual(Voto.objects.count(), 0)

        respuesta = self.client.post(
            self.url,
            {
                "opcion": self.opcion.pk,
                "confirmar": "1",
                "usuario": "99999",
                "categoria": "99999",
                "edicion": "99999",
            },
        )

        voto = Voto.objects.get()
        self.assertRedirects(
            respuesta,
            reverse("public:comprobante_voto", args=[voto.pk]),
        )
        self.assertEqual(voto.usuario, self.usuario)
        self.assertEqual(voto.edicion, self.edicion)
        self.assertEqual(voto.categoria, self.categoria)
        self.assertEqual(voto.votacion, self.votacion)
        self.assertEqual(voto.opcion, self.opcion)
        comprobante = self.client.get(
            reverse("public:comprobante_voto", args=[voto.pk])
        )
        self.assertContains(comprobante, "VF-1")
        self.assertContains(comprobante, self.votacion.titulo)

    def test_vote_requires_authenticated_user(self):
        self.client.logout()

        response = self.client.post(
            self.url,
            {"opcion": self.opcion.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("public:login"), response.url)
        self.assertIn("next=", response.url)
        self.assertEqual(Voto.objects.count(), 0)

    def test_voter_login_returns_to_requested_voting_flow(self):
        self.client.logout()

        response = self.client.post(
            f"{reverse('public:login')}?next={self.url}",
            {
                "rol": "votante",
                "documento": self.votante.documento,
                "correo": self.votante.correo,
                "acepta_datos": "on",
                "next": self.url,
            },
        )

        self.assertRedirects(response, self.url)
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(self.usuario.pk),
        )

    def test_staff_user_cannot_vote(self):
        admin = get_user_model().objects.create_user(
            username="admin_vote",
            password="ClaveSegura123!",
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            self.url,
            {"opcion": self.opcion.pk},
        )

        self.assertRedirects(response, reverse("public:votaciones"))
        self.assertEqual(Voto.objects.count(), 0)

    def test_user_not_in_voter_roster_cannot_vote(self):
        self.votante.delete()

        response = self.client.post(
            self.url,
            {"opcion": self.opcion.pk},
        )

        self.assertRedirects(response, reverse("public:votaciones"))
        self.assertEqual(Voto.objects.count(), 0)

    def test_duplicate_vote_is_rejected(self):
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        response = self.confirmar_voto()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya registraste un voto en esta categoría.")
        self.assertEqual(Voto.objects.count(), 1)

    def test_closed_votation_rejects_selection_and_confirmation(self):
        self.votacion.estado = Votacion.Estado.CERRADA
        self.votacion.save()

        response = self.confirmar_voto()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esta votación no está abierta.")
        self.assertEqual(Voto.objects.count(), 0)

    def test_inactive_category_or_edition_rejects_vote(self):
        self.categoria.activa = False
        self.categoria.save()

        response = self.confirmar_voto()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La categoría o edición no está habilitada para votar.",
        )
        self.assertEqual(Voto.objects.count(), 0)

    def test_inactive_edition_rejects_vote(self):
        self.edicion.activa = False
        self.edicion.save()

        response = self.confirmar_voto()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La categoría o edición no está habilitada para votar.",
        )
        self.assertEqual(Voto.objects.count(), 0)

    def test_option_from_another_votation_is_rejected(self):
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Otra categoría",
            activa=True,
        )
        otra_votacion = Votacion.objects.create(
            categoria=otra_categoria,
            titulo="Otra elección",
            fecha_apertura=timezone.now() - timedelta(hours=1),
            fecha_cierre=timezone.now() + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )
        opcion_ajena = Opcion.objects.create(
            votacion=otra_votacion,
            nombre="Opción de otra categoría",
            activa=True,
        )

        response = self.confirmar_voto(opcion_ajena)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La opción seleccionada no pertenece a esta votación o no está activa.",
        )
        self.assertEqual(Voto.objects.count(), 0)

    def test_inactive_option_is_rejected(self):
        self.opcion.activa = False
        self.opcion.save()

        response = self.confirmar_voto()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La opción seleccionada no pertenece a esta votación o no está activa.",
        )
        self.assertEqual(Voto.objects.count(), 0)

    def test_get_does_not_create_vote_and_post_requires_csrf(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(Voto.objects.count(), 0)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.usuario)
        post_response = csrf_client.post(
            self.url,
            {"opcion": self.opcion.pk},
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_participation_history_only_displays_own_votes(self):
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )
        otro_usuario = get_user_model().objects.create_user(
            username="otro_votante",
            password="ClaveSegura123!",
        )
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Otra categoría",
            activa=True,
        )
        otra_votacion = Votacion.objects.create(
            categoria=otra_categoria,
            titulo="Elección ajena",
            fecha_apertura=timezone.now() - timedelta(hours=1),
            fecha_cierre=timezone.now() + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )
        otra_opcion = Opcion.objects.create(
            votacion=otra_votacion,
            nombre="Opción ajena",
        )
        Voto.objects.create(
            usuario=otro_usuario,
            edicion=self.edicion,
            categoria=otra_categoria,
            votacion=otra_votacion,
            opcion=otra_opcion,
        )

        response = self.client.get(reverse("public:categorias_votadas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.categoria.nombre)
        self.assertNotContains(response, otra_categoria.nombre)
