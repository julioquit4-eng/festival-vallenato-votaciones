/* ==========================================================================
   demo-data.js — DATOS DE DEMOSTRACIÓN (100 % ficticios)
   --------------------------------------------------------------------------
   • Ningún nombre, fecha, cifra ni resultado de este archivo es oficial.
   • Las personas, canciones y agrupaciones son inventadas para el prototipo.
   • Los documentos y correos ya vienen ENMASCARADOS y usan el dominio reservado
     ejemplo.com: no hay datos personales reales.
   • INTEGRACIÓN DJANGO: este archivo debe desaparecer. Cada pantalla deberá
     recibir estos datos desde el contexto de su vista (o desde endpoints que
     el backend defina). Ver docs/INTEGRACION_DJANGO.md.
   ========================================================================== */
(function (window) {
  'use strict';

  var data = {
    meta: {
      esDemo: true,
      aviso: 'Datos de demostración: información ficticia, no oficial.',
      // Si el backend autoriza expresamente mostrar resultados parciales, se pondría en true.
      resultadosParcialesAutorizados: false
    },

    edicionActualId: 'ed-2027',

    ediciones: [
      { id: 'ed-2027', nombre: 'Festival de la Leyenda Vallenata 2027', anio: 2027, estado: 'activa', descripcion: 'Edición de referencia para el prototipo.' },
      { id: 'ed-2026', nombre: 'Edición 2026 (histórico de demostración)', anio: 2026, estado: 'inactiva', descripcion: 'Edición ficticia para mostrar resultados publicados.' },
      { id: 'ed-2028', nombre: 'Edición 2028 (borrador de demostración)', anio: 2028, estado: 'borrador', descripcion: 'Edición en preparación.' }
    ],

    categorias: [
      { id: 'cat-prof',      edicionId: 'ed-2027', nombre: 'Acordeonero profesional', descripcion: 'Intérpretes de acordeón con trayectoria profesional.', activa: true },
      { id: 'cat-cancion',   edicionId: 'ed-2027', nombre: 'Canción inédita',         descripcion: 'Obras originales que no han sido grabadas comercialmente.', activa: true },
      { id: 'cat-piloneras', edicionId: 'ed-2027', nombre: 'Piloneras',               descripcion: 'Agrupaciones de danza tradicional.', activa: true },
      { id: 'cat-juvenil',   edicionId: 'ed-2027', nombre: 'Acordeonero juvenil',     descripcion: 'Nuevos talentos del acordeón.', activa: true },
      { id: 'cat-piqueria',  edicionId: 'ed-2027', nombre: 'Piquería',                descripcion: 'Duelo de versos improvisados.', activa: true },
      { id: 'cat-infantil',  edicionId: 'ed-2027', nombre: 'Acordeonero infantil',    descripcion: 'Categoría desactivada en esta demostración.', activa: false },
      { id: 'cat-26-prof',   edicionId: 'ed-2026', nombre: 'Acordeonero profesional', descripcion: 'Categoría histórica de demostración.', activa: true },
      { id: 'cat-26-cancion',edicionId: 'ed-2026', nombre: 'Canción inédita',         descripcion: 'Categoría histórica de demostración.', activa: true }
    ],

    /* estado: abierta | proxima | cerrada | pausada | borrador
       resultadosPublicados: solo aplica a votaciones cerradas */
    votaciones: [
      { id: 'v-prof', edicionId: 'ed-2027', categoriaId: 'cat-prof',
        nombre: 'Favorito del público: acordeonero profesional',
        descripcion: 'Elige al intérprete que, a tu juicio, mejor representa la tradición del acordeón vallenato.',
        imagen: 'img/hero-acordeon.jpg', imagenAlt: 'Acordeón de botones con fuelle rojo y dorado sobre una silla de madera',
        estado: 'abierta', apertura: '2026-10-20T08:00', cierre: '2026-11-15T18:00', resultadosPublicados: false },
      { id: 'v-cancion', edicionId: 'ed-2027', categoriaId: 'cat-cancion',
        nombre: 'Canción inédita favorita',
        descripcion: 'Escucha y escoge la obra inédita que más te conmueva entre las finalistas de ejemplo.',
        imagen: null, arte: 'terra', icono: 'bi-music-note-list',
        estado: 'abierta', apertura: '2026-10-20T08:00', cierre: '2026-11-15T18:00', resultadosPublicados: false },
      { id: 'v-piloneras', edicionId: 'ed-2027', categoriaId: 'cat-piloneras',
        nombre: 'Agrupación de piloneras del público',
        descripcion: 'Votación del público para las agrupaciones de danza tradicional.',
        imagen: null, arte: 'green', icono: 'bi-people-fill',
        estado: 'proxima', apertura: '2027-02-01T08:00', cierre: '2027-03-15T18:00', resultadosPublicados: false },
      { id: 'v-juvenil', edicionId: 'ed-2027', categoriaId: 'cat-juvenil',
        nombre: 'Revelación juvenil del acordeón',
        descripcion: 'Reconocimiento del público a los nuevos talentos.',
        imagen: 'img/instrumentos.jpg', imagenAlt: 'Caja vallenata, guacharaca y acordeón sobre un tejido de colores',
        estado: 'proxima', apertura: '2027-02-01T08:00', cierre: '2027-03-15T18:00', resultadosPublicados: false },
      { id: 'v-piqueria', edicionId: 'ed-2027', categoriaId: 'cat-piqueria',
        nombre: 'Mejor dúo de piquería (preselección)',
        descripcion: 'Preselección del público para el duelo de versos.',
        imagen: 'img/paisaje-cesar.jpg', imagenAlt: 'Valle verde con río y montañas nevadas al amanecer',
        estado: 'cerrada', apertura: '2026-09-01T08:00', cierre: '2026-09-30T18:00', resultadosPublicados: true, fechaPublicacion: '2026-10-02T10:00' },
      { id: 'v-26-prof', edicionId: 'ed-2026', categoriaId: 'cat-26-prof',
        nombre: 'Favorito del público 2026 (histórico)',
        descripcion: 'Votación histórica de demostración con resultados publicados.',
        imagen: null, arte: 'night', icono: 'bi-trophy',
        estado: 'cerrada', apertura: '2026-03-01T08:00', cierre: '2026-04-10T18:00', resultadosPublicados: true, fechaPublicacion: '2026-04-12T09:00' },
      { id: 'v-26-cancion', edicionId: 'ed-2026', categoriaId: 'cat-26-cancion',
        nombre: 'Canción inédita 2026 (histórico)',
        descripcion: 'Votación cerrada cuyos resultados aún no se han publicado.',
        imagen: null, arte: 'terra', icono: 'bi-vinyl',
        estado: 'cerrada', apertura: '2026-03-01T08:00', cierre: '2026-04-10T18:00', resultadosPublicados: false }
    ],

    /* Opciones (candidatos). Todas son ficticias. */
    opciones: [
      { id: 'op-01', votacionId: 'v-prof', nombre: 'Mateo Larrañaga', iniciales: 'ML', descripcion: 'Acordeonero de ejemplo con repertorio de paseo y merengue.', datos: ['Paseo', 'Merengue'], estado: 'activa', tono: 0 },
      { id: 'op-02', votacionId: 'v-prof', nombre: 'Samuel Arévalo',  iniciales: 'SA', descripcion: 'Intérprete ficticio reconocido por sus sones tradicionales.', datos: ['Son', 'Puya'], estado: 'activa', tono: 1 },
      { id: 'op-03', votacionId: 'v-prof', nombre: 'Julián Pacheco',  iniciales: 'JP', descripcion: 'Participante de demostración con estilo sabanero.', datos: ['Paseo', 'Son'], estado: 'activa', tono: 2 },
      { id: 'op-04', votacionId: 'v-prof', nombre: 'Andrés Ibarra',   iniciales: 'AI', descripcion: 'Perfil de ejemplo para probar la selección exclusiva.', datos: ['Merengue', 'Puya'], estado: 'activa', tono: 3 },

      { id: 'op-05', votacionId: 'v-cancion', nombre: 'Brisa de mi tierra', iniciales: 'BT', descripcion: 'Obra ficticia · Autoría: compositora de ejemplo.', datos: ['Paseo'], estado: 'activa', tono: 1 },
      { id: 'op-06', votacionId: 'v-cancion', nombre: 'Cartas al río',      iniciales: 'CR', descripcion: 'Obra ficticia · Autoría: compositor de ejemplo.',  datos: ['Paseo'], estado: 'activa', tono: 2 },
      { id: 'op-07', votacionId: 'v-cancion', nombre: 'Verano en el valle', iniciales: 'VV', descripcion: 'Obra ficticia · Autoría: dúo de ejemplo.',        datos: ['Merengue'], estado: 'activa', tono: 0 },

      { id: 'op-08', votacionId: 'v-piloneras', nombre: 'Agrupación Sol Naciente', iniciales: 'SN', descripcion: 'Agrupación de danza de ejemplo.', datos: ['Danza'], estado: 'activa', tono: 2 },
      { id: 'op-09', votacionId: 'v-piloneras', nombre: 'Colectivo Raíces',        iniciales: 'CR', descripcion: 'Agrupación de danza de ejemplo.', datos: ['Danza'], estado: 'activa', tono: 3 },

      { id: 'op-10', votacionId: 'v-juvenil', nombre: 'Lucas Montaño', iniciales: 'LM', descripcion: 'Participante juvenil ficticio.', datos: ['Juvenil'], estado: 'activa', tono: 0 },
      { id: 'op-11', votacionId: 'v-juvenil', nombre: 'Sara Ovalle',   iniciales: 'SO', descripcion: 'Participante juvenil ficticia.', datos: ['Juvenil'], estado: 'borrador', tono: 1 },

      { id: 'op-12', votacionId: 'v-piqueria', nombre: 'Dúo Verso Vivo',      iniciales: 'VV', descripcion: 'Dúo de improvisación ficticio.', datos: ['Décima'], estado: 'activa', tono: 3 },
      { id: 'op-13', votacionId: 'v-piqueria', nombre: 'Dúo Décima Ligera',   iniciales: 'DL', descripcion: 'Dúo de improvisación ficticio.', datos: ['Décima'], estado: 'activa', tono: 0 },
      { id: 'op-14', votacionId: 'v-piqueria', nombre: 'Dúo Contrapunteo',    iniciales: 'DC', descripcion: 'Dúo de improvisación ficticio.', datos: ['Décima'], estado: 'activa', tono: 2 },

      { id: 'op-15', votacionId: 'v-26-prof', nombre: 'Ricardo Fuentes',   iniciales: 'RF', descripcion: 'Participante histórico ficticio.', datos: [], estado: 'activa', tono: 1 },
      { id: 'op-16', votacionId: 'v-26-prof', nombre: 'Iván Salcedo',      iniciales: 'IS', descripcion: 'Participante histórico ficticio.', datos: [], estado: 'activa', tono: 2 },
      { id: 'op-17', votacionId: 'v-26-prof', nombre: 'Nicolás Peñaloza',  iniciales: 'NP', descripcion: 'Participante histórico ficticio.', datos: [], estado: 'activa', tono: 3 },
      { id: 'op-18', votacionId: 'v-26-prof', nombre: 'Tomás Rangel',      iniciales: 'TR', descripcion: 'Participante histórico ficticio.', datos: [], estado: 'activa', tono: 0 },

      { id: 'op-19', votacionId: 'v-26-cancion', nombre: 'Luna de diciembre', iniciales: 'LD', descripcion: 'Obra histórica ficticia.', datos: [], estado: 'activa', tono: 1 },
      { id: 'op-20', votacionId: 'v-26-cancion', nombre: 'El último fuelle',  iniciales: 'UF', descripcion: 'Obra histórica ficticia.', datos: [], estado: 'activa', tono: 3 }
    ],

    /* Conteos ficticios. Solo existen para votaciones CERRADAS.
       El portal público solo los muestra si resultadosPublicados === true. */
    resultados: {
      'v-piqueria':   [ { opcionId: 'op-12', votos: 241 }, { opcionId: 'op-13', votos: 187 }, { opcionId: 'op-14', votos: 106 } ],
      'v-26-prof':    [ { opcionId: 'op-15', votos: 228 }, { opcionId: 'op-16', votos: 174 }, { opcionId: 'op-17', votos: 131 }, { opcionId: 'op-18', votos: 79 } ],
      'v-26-cancion': [ { opcionId: 'op-19', votos: 301 }, { opcionId: 'op-20', votos: 262 } ]
    },

    /* Padrón de demostración: valores agregados coherentes con los resultados anteriores */
    padron: {
      'ed-2027': { registrados: 1320, habilitados: 1250, incompletos: 37 },
      'ed-2026': { registrados: 1010, habilitados: 980,  incompletos: 12 },
      'ed-2028': { registrados: 0,    habilitados: 0,    incompletos: 0 }
    },

    /* Resumen que se muestra al simular la carga de un CSV (NO se lee el archivo) */
    simulacionCargaCsv: {
      filasValidas: 118,
      filasInvalidas: 7,
      motivos: [
        { motivo: 'Correo con formato no válido', filas: 3 },
        { motivo: 'Documento vacío', filas: 2 },
        { motivo: 'Registro duplicado', filas: 2 }
      ]
    },

    /* Registros del padrón ya enmascarados (ficticios) */
    votantes: [
      { id: 'vt-01', edicionId: 'ed-2027', documento: '••••••0101', correo: 'vo•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-02', edicionId: 'ed-2027', documento: '••••••0102', correo: 'pa•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-03', edicionId: 'ed-2027', documento: '••••••0103', correo: '—',                 habilitado: false, completo: false },
      { id: 'vt-04', edicionId: 'ed-2027', documento: '••••••0104', correo: 'ci•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-05', edicionId: 'ed-2027', documento: '••••••0105', correo: 'mu•••@ejemplo.com', habilitado: false, completo: true },
      { id: 'vt-06', edicionId: 'ed-2027', documento: '••••••0106', correo: 'fe•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-07', edicionId: 'ed-2027', documento: '—',          correo: 'ac•••@ejemplo.com', habilitado: false, completo: false },
      { id: 'vt-08', edicionId: 'ed-2027', documento: '••••••0108', correo: 'ca•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-09', edicionId: 'ed-2026', documento: '••••••0109', correo: 'gu•••@ejemplo.com', habilitado: true,  completo: true },
      { id: 'vt-10', edicionId: 'ed-2026', documento: '••••••0110', correo: 'so•••@ejemplo.com', habilitado: true,  completo: true }
    ],

    /* Alertas informativas del dashboard */
    alertas: [
      { tipo: 'warning', titulo: 'Reglas pendientes de aprobación', texto: 'La regla de voto único (por categoría o por votación) aún debe ser aprobada por la organización.' },
      { tipo: 'info', titulo: 'Padrón con registros incompletos', texto: '37 registros de demostración no tienen todos los datos requeridos.' },
      { tipo: 'demo', titulo: 'Modo prototipo', texto: 'Las acciones de este panel se simulan en memoria y se pierden al recargar la página.' }
    ]
  };

  /* Consultas de apoyo sobre los datos de demostración */
  var api = {
    edicion: function (id) { return data.ediciones.find(function (e) { return e.id === id; }) || null; },
    categoria: function (id) { return data.categorias.find(function (c) { return c.id === id; }) || null; },
    votacion: function (id) { return data.votaciones.find(function (v) { return v.id === id; }) || null; },
    opcion: function (id) { return data.opciones.find(function (o) { return o.id === id; }) || null; },
    opcionesDe: function (votacionId) { return data.opciones.filter(function (o) { return o.votacionId === votacionId; }); },
    votacionesDe: function (edicionId) { return data.votaciones.filter(function (v) { return v.edicionId === edicionId; }); },
    categoriasDe: function (edicionId) { return data.categorias.filter(function (c) { return c.edicionId === edicionId; }); }
  };

  window.VFDemo = Object.freeze({ data: data, q: api });
})(window);
