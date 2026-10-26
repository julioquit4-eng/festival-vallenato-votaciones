# Sistema Web de Votaciones

Proyecto académico desarrollado para gestionar las ediciones, categorías, votaciones y opciones del Festival de la Leyenda Vallenata.

## Tecnologías utilizadas

- Python 3.12
- Django 5.2
- MySQL 8.0
- HTML5
- CSS3
- Bootstrap
- JavaScript
- Git y GitHub

## Estructura principal

El sistema implementa la siguiente relación:

Edición → Categoría → Votación → Opción

Una edición puede contener varias categorías, cada categoría puede incluir varias votaciones y cada votación puede disponer de múltiples opciones.

## Requisitos previos

Antes de ejecutar el proyecto se requiere:

- Python 3.12 o una versión compatible.
- MySQL Server 8.0.
- Git.
- Visual Studio Code u otro editor de código.

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/julioquit4-eng/festival-vallenato-votaciones.git
cd festival-vallenato-votaciones
```

### 2. Instalar dependencias y configurar el entorno

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con las credenciales de tu instalación local de MySQL y una clave
secreta de Django. Crea la base de datos indicada en `DB_NAME` antes de
continuar.

### 3. Preparar la base de datos e iniciar el servidor

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La cuenta creada con `createsuperuser` puede iniciar sesión en `/login/` y
acceder al panel administrativo. Las rutas del panel requieren una cuenta con
permisos de personal (`is_staff`).

La página pública de votaciones obtiene ediciones, categorías, votaciones y
opciones de MySQL. La autenticación de votantes y el registro/publicación de
votos siguen pendientes porque aún no existe un padrón ni un modelo de
sufragios. No se cargan datos de prueba.

Desde el panel también se pueden crear, editar y eliminar votaciones y sus
opciones. Para proteger la integridad del proceso, una votación abierta y sus
opciones no se pueden editar ni eliminar hasta que cierre.

La sección de categorías permite consultar, crear y editar categorías
asociadas a una edición. No se puede eliminar una categoría que ya tenga
votaciones vinculadas.

El censo electoral se importa desde el panel por edición, usando un CSV UTF-8
con columnas `documento` y `correo` (máximo 5 MB y 10.000 registros). La carga
valida el archivo completo antes de guardarlo. Si un documento ya existe en
esa edición, se actualiza su correo; los registros que no aparecen en el CSV
no se eliminan. El padrón se guarda en la base de datos y se muestra enmascarado
en el panel. Tras incorporar el modelo del padrón, aplica la migración:

```bash
python manage.py migrate
```
