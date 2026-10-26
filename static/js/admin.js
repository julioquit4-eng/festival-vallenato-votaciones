/* ==========================================================================
   admin.js — Lógica interactiva del Panel Administrativo
   --------------------------------------------------------------------------
   Controla:
   - Pantalla 9: Dashboard (KPIs y tabla de procesos recientes).
   - Pantalla 10: Ediciones y Categorías (Creación y edición simulada).
   - Pantalla 11: Opciones y Candidatos (Bloqueo si el proceso está Abierto).
   - Pantalla 12: Votaciones (Validación de fechas: fin > inicio, confirmaciones).
   - Pantalla 13: Censo y Padrón (Simulación de carga CSV con filas inválidas).
   - Pantalla 14: Reportes (Cálculo de participación y descarga CSV demo).
   ========================================================================== */
(function (window, document, VF) {
  'use strict';

  if (!VF) return;

  /* -------------------------------------------------------------------------
     PANTALLA 9: DASHBOARD ADMINISTRATIVO
     ------------------------------------------------------------------------- */
  VF.pages.dashboard = function () {
    if (!VF.data) return;

    var tbody = document.querySelector('#dashVotesTable tbody');
    var alertsBox = document.getElementById('dashAlertsContainer');

    if (
      (tbody && tbody.dataset.source === 'database') ||
      (alertsBox && alertsBox.dataset.source === 'database')
    ) return;

    // Cargar alertas
    if (alertsBox && VF.data.alertas) {
      alertsBox.innerHTML = '';
      VF.data.alertas.forEach(function (al) {
        var alertDiv = document.createElement('div');
        alertDiv.className = 'vf-alert vf-alert--' + al.tipo + ' p-2';
        alertDiv.innerHTML = 
          '<i class="bi ' + (al.tipo === 'warning' ? 'bi-exclamation-triangle' : 'bi-info-circle') + '"></i>' +
          '<div class="small"><strong>' + VF.esc(al.titulo) + '</strong><p class="mb-0 text-muted">' + VF.esc(al.texto) + '</p></div>';
        alertsBox.appendChild(alertDiv);
      });
    }

    // Cargar tabla de votaciones recientes
    if (tbody) {
      tbody.innerHTML = '';
      var votaciones = VF.data.votaciones.slice(0, 5);
      votaciones.forEach(function (v) {
        var cat = VF.q.categoria(v.categoriaId);
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td><strong>' + VF.esc(v.nombre) + '</strong><br><small class="text-muted">' + VF.esc(cat ? cat.nombre : '') + '</small></td>' +
          '<td><span class="small text-muted">' + VF.fmtDate(v.apertura) + ' - ' + VF.fmtDate(v.cierre) + '</span></td>' +
          '<td>' + VF.statusBadge(v.estado) + '</td>' +
          '<td class="text-end">' +
            '<a href="' + VF.url('panel_votaciones') + '" class="btn btn-sm btn-vf-outline btn-icon" title="Editar proceso"><i class="bi bi-pencil"></i></a>' +
          '</td>';
        tbody.appendChild(tr);
      });
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 10: EDICIONES Y CATEGORÍAS
     ------------------------------------------------------------------------- */
  VF.pages.ediciones = VF.pages.categorias = function () {
    if (!VF.data) return;

    var edTable = document.querySelector('#editionsTable tbody');
    var catTable = document.querySelector('#categoriesTable tbody');
    if (
      (edTable && edTable.dataset.source === 'database') ||
      (catTable && catTable.dataset.source === 'database')
    ) return;

    // Render Ediciones
    if (edTable) {
      edTable.innerHTML = '';
      VF.data.ediciones.forEach(function (ed) {
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td><strong>' + VF.esc(ed.nombre) + '</strong><br><small class="text-muted">Año: ' + ed.anio + '</small></td>' +
          '<td>' + VF.statusBadge(ed.estado) + '</td>' +
          '<td class="text-end">' +
            '<button class="btn btn-sm btn-vf-outline btn-icon me-1" onclick="VF.toast(\'' + VF.SIM_MSG + '\', \'info\')" title="Editar"><i class="bi bi-pencil"></i></button>' +
          '</td>';
        edTable.appendChild(tr);
      });
    }

    // Render Categorías
    if (catTable) {
      catTable.innerHTML = '';
      VF.data.categorias.forEach(function (cat) {
        var ed = VF.q.edicion(cat.edicionId);
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td><strong>' + VF.esc(cat.nombre) + '</strong><br><small class="text-muted">' + VF.esc(ed ? ed.nombre : '') + '</small></td>' +
          '<td>' + (cat.activa ? VF.statusBadge('activa') : VF.statusBadge('inactiva')) + '</td>' +
          '<td class="text-end">' +
            '<button class="btn btn-sm btn-vf-outline btn-icon" onclick="VF.toast(\'' + VF.SIM_MSG + '\', \'info\')" title="Configurar"><i class="bi bi-gear"></i></button>' +
          '</td>';
        catTable.appendChild(tr);
      });
    }

    // Modales de creación simulada
    var btnNewEd = document.getElementById('btnOpenNewEditionModal');
    var modalEdEl = document.getElementById('editionModal');
    var formEd = document.getElementById('editionForm');
    if (btnNewEd && modalEdEl && window.bootstrap) {
      var modalEd = new window.bootstrap.Modal(modalEdEl);
      btnNewEd.addEventListener('click', function () { modalEd.show(); });
      if (formEd) {
        formEd.addEventListener('submit', function (e) {
          e.preventDefault();
          if (!VF.validate(formEd)) return;
          modalEd.hide();
          VF.toast('Edición guardada exitosamente. ' + VF.SIM_MSG, 'success');
        });
      }
    }

    var btnNewCat = document.getElementById('btnOpenNewCatModal');
    var modalCatEl = document.getElementById('categoryModal');
    var formCat = document.getElementById('categoryForm');
    if (btnNewCat && modalCatEl && window.bootstrap) {
      var modalCat = new window.bootstrap.Modal(modalCatEl);
      btnNewCat.addEventListener('click', function () { modalCat.show(); });
      if (formCat) {
        formCat.addEventListener('submit', function (e) {
          e.preventDefault();
          if (!VF.validate(formCat)) return;
          modalCat.hide();
          VF.toast('Categoría registrada con éxito. ' + VF.SIM_MSG, 'success');
        });
      }
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 11: OPCIONES Y CANDIDATOS
     ------------------------------------------------------------------------- */
  VF.pages.opciones = function () {
    if (!VF.data) return;

    var filterSelect = document.getElementById('optFilterVoteSelect');
    var tbody = document.querySelector('#optionsAdminTable tbody');
    var alertActive = document.getElementById('alertVoteActiveWarning');
    var btnAddOption = document.getElementById('btnOpenNewOptionModal');

    // Poblar Selector
    if (filterSelect) {
      filterSelect.innerHTML = '';
      VF.data.votaciones.forEach(function (v) {
        var opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.nombre + ' (' + v.estado + ')';
        filterSelect.appendChild(opt);
      });
    }

    function renderOptionsForVote(voteId) {
      var vote = VF.q.votacion(voteId);
      var opciones = VF.q.opcionesDe(voteId);
      var isVoteOpen = vote && vote.estado === 'abierta';

      // Regla de Negocio: Restricción si el proceso está Abierto
      if (isVoteOpen) {
        alertActive.classList.remove('d-none');
        if (btnAddOption) {
          btnAddOption.disabled = true;
          btnAddOption.classList.add('disabled');
          btnAddOption.title = 'No se pueden añadir candidatos mientras la votación esté abierta.';
        }
      } else {
        alertActive.classList.add('d-none');
        if (btnAddOption) {
          btnAddOption.disabled = false;
          btnAddOption.classList.remove('disabled');
          btnAddOption.title = '';
        }
      }

      tbody.innerHTML = '';
      if (opciones.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No hay candidatos asignados a esta votación.</td></tr>';
        return;
      }

      opciones.forEach(function (op) {
        var tr = document.createElement('tr');
        var editDisabled = isVoteOpen ? ' disabled title="Bloqueado por regla de negocio: votación activa"' : '';
        
        tr.innerHTML = 
          '<td>' +
            '<div class="d-flex align-items-center gap-2">' +
              '<div class="vf-avatar--sm text-white" style="background:#183B56; display:grid; place-items:center; border-radius:0.4rem; font-size:0.75rem;">' + VF.esc(op.iniciales) + '</div>' +
              '<div><strong>' + VF.esc(op.nombre) + '</strong><br><small class="text-muted">' + VF.esc(op.descripcion) + '</small></div>' +
            '</div>' +
          '</td>' +
          '<td><small class="text-muted">' + VF.esc(vote ? vote.nombre : '') + '</small></td>' +
          '<td>' + (op.datos ? op.datos.map(function(d){ return '<span class="badge bg-light text-dark border me-1">' + VF.esc(d) + '</span>'; }).join('') : '—') + '</td>' +
          '<td>' + VF.statusBadge(op.estado) + '</td>' +
          '<td class="text-end">' +
            '<button class="btn btn-sm btn-vf-outline btn-icon"' + editDisabled + ' onclick="VF.toast(\'' + (isVoteOpen ? 'Acción no permitida: la votación está abierta.' : VF.SIM_MSG) + '\', \'' + (isVoteOpen ? 'danger' : 'info') + '\')">' +
              '<i class="bi ' + (isVoteOpen ? 'bi-lock-fill' : 'bi-pencil') + '"></i>' +
            '</button>' +
          '</td>';

        tbody.appendChild(tr);
      });
    }

    if (filterSelect) {
      filterSelect.addEventListener('change', function (e) {
        renderOptionsForVote(e.target.value);
      });
      renderOptionsForVote(filterSelect.value);
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 12: GESTIÓN DE VOTACIONES
     ------------------------------------------------------------------------- */
  VF.pages.votaciones_admin = function () {
    if (!VF.data) return;

    var tbody = document.querySelector('#adminVotesTable tbody');
    var btnNew = document.getElementById('btnOpenNewVoteProcessModal');
    var modalEl = document.getElementById('voteProcessModal');
    var form = document.getElementById('voteProcessForm');
    var catSelect = document.getElementById('vpCategorySelect');

    if (!tbody) return;

    // Llenar categorías en modal
    if (catSelect) {
      catSelect.innerHTML = '';
      VF.data.categorias.forEach(function (c) {
        var opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.nombre;
        catSelect.appendChild(opt);
      });
    }

    function renderVotesTable() {
      tbody.innerHTML = '';
      VF.data.votaciones.forEach(function (v) {
        var cat = VF.q.categoria(v.categoriaId);
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td><strong>' + VF.esc(v.nombre) + '</strong></td>' +
          '<td><small class="text-muted">' + VF.esc(cat ? cat.nombre : '') + '</small></td>' +
          '<td><small>' + VF.fmtDate(v.apertura) + '</small></td>' +
          '<td><small>' + VF.fmtDate(v.cierre) + '</small></td>' +
          '<td>' + VF.statusBadge(v.estado) + '</td>' +
          '<td class="text-end">' +
            '<div class="btn-group btn-group-sm">' +
              '<button type="button" class="btn btn-vf-outline btn-icon" title="Cambiar estado" data-action="toggle-status" data-id="' + v.id + '"><i class="bi bi-arrow-repeat"></i></button>' +
              '<button type="button" class="btn btn-vf-outline btn-icon" title="Editar proceso" onclick="VF.toast(\'' + VF.SIM_MSG + '\', \'info\')"><i class="bi bi-pencil"></i></button>' +
            '</div>' +
          '</td>';
        tbody.appendChild(tr);
      });
    }

    // Modal de Nuevo Proceso
    if (btnNew && modalEl && window.bootstrap) {
      var modal = new window.bootstrap.Modal(modalEl);
      btnNew.addEventListener('click', function () { modal.show(); });

      if (form) {
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var start = document.getElementById('vpStartDateInput');
          var end = document.getElementById('vpEndDateInput');
          var feedback = document.getElementById('dateOrderFeedback');

          // Validación de regla: fecha fin > inicio
          if (start.value && end.value && new Date(end.value) <= new Date(start.value)) {
            end.classList.add('is-invalid');
            if (feedback) feedback.style.display = 'block';
            VF.toast('La fecha de cierre debe ser posterior a la fecha de apertura.', 'danger');
            return;
          } else {
            end.classList.remove('is-invalid');
            if (feedback) feedback.style.display = 'none';
          }

          if (!VF.validate(form)) return;
          modal.hide();
          VF.toast('Proceso de votación configurado con éxito. ' + VF.SIM_MSG, 'success');
        });
      }
    }

    // Cambio de estado crítico con confirmación modal
    if (tbody) {
      tbody.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-action="toggle-status"]');
        if (!btn) return;
        var voteId = btn.dataset.id;
        var vote = VF.q.votacion(voteId);

        VF.confirm({
          title: '¿Modificar estado del proceso?',
          message: 'Estás a punto de alterar el estado de la votación "' + (vote ? vote.nombre : '') + '". Esta acción influye de inmediato en la habilitación del portal público.',
          note: 'Operación simulada en memoria para el prototipo.',
          confirmText: 'Sí, cambiar estado',
          variant: 'warning',
          icon: 'bi-exclamation-triangle-fill'
        }).then(function (confirmed) {
          if (confirmed) {
            vote.estado = vote.estado === 'abierta' ? 'cerrada' : 'abierta';
            renderVotesTable();
            VF.toast('Estado modificado a ' + vote.estado + '. ' + VF.SIM_MSG, 'success');
          }
        });
      });
    }

    renderVotesTable();
  };

  /* -------------------------------------------------------------------------
     PANTALLA 13: PADRÓN DE VOTANTES Y CARGA CSV
     ------------------------------------------------------------------------- */
  VF.pages.votantes = function () {
    if (!VF.data) return;

    var tbody = document.querySelector('#votersTable tbody');
    if (tbody && tbody.dataset.source === 'database') return;
    var dropzone = document.getElementById('csvDropzone');
    var fileInput = document.getElementById('csvFileInput');
    var fileNameEl = document.getElementById('selectedFileName');
    var btnSim = document.getElementById('btnSimulateUpload');
    var summaryBox = document.getElementById('uploadSummaryBox');
    var form = document.getElementById('csvUploadForm');

    // Render tabla con datos enmascarados
    if (tbody) {
      tbody.innerHTML = '';
      VF.data.votantes.forEach(function (vt) {
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td><span class="vf-mono">' + VF.esc(vt.documento) + '</span></td>' +
          '<td><span class="vf-mono">' + VF.esc(vt.correo) + '</span></td>' +
          '<td>' + (vt.habilitado ? VF.statusBadge('habilitado') : VF.statusBadge('inhabilitado')) + '</td>' +
          '<td>' + (vt.completo ? '<span class="text-success small"><i class="bi bi-check-circle-fill me-1"></i>Completo</span>' : '<span class="text-danger small"><i class="bi bi-x-circle-fill me-1"></i>Incompleto</span>') + '</td>';
        tbody.appendChild(tr);
      });
    }

    // Manejo de archivo CSV (simulado)
    if (fileInput) {
      fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
          var name = fileInput.files[0].name;
          if (fileNameEl) {
            fileNameEl.textContent = 'Archivo seleccionado: ' + name;
            fileNameEl.classList.remove('d-none');
          }
          if (btnSim) btnSim.disabled = false;
        }
      });
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (summaryBox) summaryBox.classList.remove('d-none');
        VF.toast('Archivo CSV analizado correctamente (modo simulación).', 'success');
      });
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 14: REPORTES Y RESULTADOS ADMINISTRATIVOS
     ------------------------------------------------------------------------- */
  VF.pages.reportes = function () {
    if (!VF.data) return;

    var selectVote = document.getElementById('reportVoteSelect');
    var repCensus = document.getElementById('repCensus');
    var repTotalVotes = document.getElementById('repTotalVotes');
    var repParticipation = document.getElementById('repParticipationPct');
    var tbody = document.querySelector('#reportResultsTable tbody');
    var btnExport = document.getElementById('btnExportDemoCsv');

    // Poblar Selector con Votaciones Cerradas (con resultados demo)
    if (selectVote) {
      selectVote.innerHTML = '';
      VF.data.votaciones.filter(function (v) { return v.estado === 'cerrada'; }).forEach(function (v) {
        var opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.nombre;
        selectVote.appendChild(opt);
      });
    }

    function renderReportForVote(voteId) {
      var resultados = VF.data.resultados[voteId] || [];
      var total = resultados.reduce(function (sum, item) { return sum + item.votos; }, 0);
      var censo = 1250; // valor demo asignado
      var pctPart = censo > 0 ? (total / censo * 100) : 0;

      if (repCensus) repCensus.textContent = VF.fmtNum(censo);
      if (repTotalVotes) repTotalVotes.textContent = VF.fmtNum(total);
      if (repParticipation) repParticipation.textContent = VF.fmtPct(pctPart);

      tbody.innerHTML = '';
      resultados.sort(function (a, b) { return b.votos - a.votos; });

      resultados.forEach(function (r, index) {
        var op = VF.q.opcion(r.opcionId);
        var pct = total > 0 ? (r.votos / total * 100) : 0;
        var tr = document.createElement('tr');
        tr.innerHTML = 
          '<td class="text-center fw-bold">' + (index + 1) + '°</td>' +
          '<td><strong>' + VF.esc(op ? op.nombre : 'Opción') + '</strong></td>' +
          '<td>' + VF.fmtNum(r.votos) + ' votos</td>' +
          '<td>' + VF.fmtPct(pct) + '</td>' +
          '<td style="min-width: 140px;">' +
            '<div class="progress" style="height: 10px;">' +
              '<div class="progress-bar bg-primary" style="width: ' + pct.toFixed(1) + '%"></div>' +
            '</div>' +
          '</td>';
        tbody.appendChild(tr);
      });
    }

    if (selectVote) {
      selectVote.addEventListener('change', function (e) {
        renderReportForVote(e.target.value);
      });
      renderReportForVote(selectVote.value);
    }

    // Exportación simulada a CSV
    if (btnExport) {
      btnExport.addEventListener('click', function () {
        var vote = VF.q.votacion(selectVote.value);
        var resultados = VF.data.resultados[selectVote.value] || [];
        var csvContent = 'Posicion,Candidato,Votos,Porcentaje\n';
        resultados.forEach(function (r, i) {
          var op = VF.q.opcion(r.opcionId);
          csvContent += (i + 1) + ',"' + (op ? op.nombre : 'Opción') + '",' + r.votos + '\n';
        });

        VF.download('Reporte_Demo_' + (vote ? vote.id : 'votacion') + '.csv', csvContent);
        VF.toast('Reporte exportado exitosamente con datos de demostración.', 'info');
      });
    }
  };

})(window, document, window.VF);
