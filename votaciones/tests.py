from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Votante


class AdminAuthenticationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="admin",
            password="secure-test-password",
            is_staff=True,
        )

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
            {"username": "admin", "password": "secure-test-password"},
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
                "next": "https://example.com/",
            },
        )

        self.assertRedirects(response, reverse("panel:dashboard"))

    def test_staff_login_redirects_to_requested_panel_page(self):
        response = self.client.post(
            f"{reverse('public:login')}?next={reverse('panel:votaciones')}",
            {"username": "admin", "password": "secure-test-password"},
        )

        self.assertRedirects(response, reverse("panel:votaciones"))

    def test_non_staff_user_cannot_log_in_to_panel(self):
        get_user_model().objects.create_user(
            username="voter",
            password="secure-test-password",
        )

        response = self.client.post(
            reverse("public:login"),
            {"username": "voter", "password": "secure-test-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no tiene acceso al panel administrativo")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(reverse("public:cerrar_sesion"))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse("public:cerrar_sesion"))
        self.assertRedirects(post_response, reverse("public:inicio"))
        self.assertNotIn("_auth_user_id", self.client.session)


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
        self.assertContains(response, "registro de votos")

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
