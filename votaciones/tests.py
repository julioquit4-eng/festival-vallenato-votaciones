from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Voto


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

class ApiCategoriasTests(TestCase):
    def setUp(self):
        hoy = timezone.localdate()
        ahora = timezone.now()

        self.edicion = Edicion.objects.create(
            nombre="Festival API",
            anio=2030,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=5),
            activa=True,
        )

        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoria API",
            activa=True,
        )

        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votacion API",
            fecha_apertura=ahora - timedelta(hours=1),
            fecha_cierre=ahora + timedelta(hours=1),
            estado=Votacion.Estado.ABIERTA,
        )

        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Opcion API",
            activa=True,
            orden=1,
        )

    def test_api_categorias_responde_200(self):
        response = self.client.get("/api/categorias/")

        self.assertEqual(response.status_code, 200)

    def test_api_categorias_retorna_json(self):
        response = self.client.get("/api/categorias/")

        self.assertEqual(
            response["Content-Type"],
            "application/json",
        )

    def test_api_categorias_incluye_categorias_y_opciones(self):
        response = self.client.get("/api/categorias/")
        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["categorias"][0]["nombre"],
            "Categoria API",
        )
        self.assertEqual(
            data[0]["categorias"][0]["votaciones"][0]["opciones"][0]["nombre"],
            "Opcion API",
        )
