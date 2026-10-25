/* ==========================================================================
   voting.js — Lógica de navegación e interactividad del Portal Público
   --------------------------------------------------------------------------
   Controla:
   - Pantalla 1: Inicio (Render de tarjetas destacadas, contadores).
   - Pantalla 2: Votaciones (Filtros por chip de estado y buscador por texto).
   - Pantalla 3: Detalle de votación (Selección exclusiva de candidatos).
   - Pantalla 4: Validación del votante (Formularios accesibles, Habeas Data).
   - Pantalla 5: Confirmación de voto (Resumen, modal de confirmación definitiva).
   - Pantalla 6: Comprobante (Impresión y generación de hash simulado).
   - Pantalla 7: Resultados públicos (Filtro por edición, barras porcentuales).
   ========================================================================== */
(function (window, document, VF) {
  'use strict';

  if (!VF) return;

  // Estado temporal de la sesión del votante en memoria durante el recorrido del prototipo
  // No persiste en localStorage/cookies para garantizar confidencialidad y datos ficticios.
  var sessionVoterState = {
    selectedVoteId: 'v-prof',
    selectedOptionId: null,
    voterDoc: null,
    voterEmail: null
  };

  /* Helper para recuperar parámetro URL o fallback a sesión */
  function getActiveVoteId() {
    var p = VF.param('v');
    return p || sessionVoterState.selectedVoteId || 'v-prof';
  }

  /* -------------------------------------------------------------------------
     PANTALLA 1: INICIO
     ------------------------------------------------------------------------- */
  VF.pages.inicio = function () {
    // Slider interactivo de Tradición (Inspirado en Referencias 1 y 3)
    var slides = [
      {
        img: 'img/hero-acordeon.jpg',
        badge: '<i class="bi bi-music-note-beamed"></i> Aire de Paseo · Rey Vallenato',
        badgeClass: 'vf-badge--yellow',
        title: 'La Majestad del Acordeón',
        desc: 'Los grandes juglares compiten por la corona suprema del Festival en la mítica plaza Alfonso López.'
      },
      {
        img: 'img/danza-pilon.jpg',
        badge: '<i class="bi bi-people-fill"></i> Tradición Popular · Desfile de Piloneras',
        badgeClass: 'vf-badge--royal',
        title: 'El Baile del Pilón Vallenato',
        desc: 'El desfile que abre el Festival: miles de danzantes llenan las calles de Valledupar con polleras y sombreros vueltiaos.'
      },
      {
        img: 'img/sombrero-acordeon.jpg',
        badge: '<i class="bi bi-chat-quote-fill"></i> Piqueria Mayor · Verso y Repentismo',
        badgeClass: 'vf-badge--orange',
        title: 'El Duelo de los Repentistas',
        desc: 'La agudeza mental campesina llevada a su máxima expresión en coplas improvisadas al ritmo de la caja y guacharaca.'
      },
      {
        img: 'img/paisaje-cesar.jpg',
        badge: '<i class="bi bi-tree-fill"></i> Canción Inédita · Tierra de Cantores',
        badgeClass: 'vf-badge--green',
        title: 'Poesía Hecha Canción',
        desc: 'Nuevos compositores defienden las melodías nacidas entre el río Guatapurí y la imponente Sierra Nevada.'
      }
    ];

    // --- MOVILIDAD E INTERACTIVIDAD DE .hero__visual ---
    var heroVisual = document.querySelector('.hero__visual');
    var slideImg = document.getElementById('heroSlideImg');
    var slideBadge = document.getElementById('heroSlideBadge');
    var slideTitle = document.getElementById('heroSlideTitle');
    var slideDesc = document.getElementById('heroSlideDesc');
    var slideCounter = document.getElementById('heroSliderCounter');
    var slideDots = document.querySelectorAll('.hero-slider-dot');
    var slideCard = document.getElementById('heroSlideCard');
    var stickers = document.querySelectorAll('.folklore-sticker');

    var curSlide = 0;

    function updateSlide(idx) {
      curSlide = (idx + slides.length) % slides.length;
      var s = slides[curSlide];
      if (slideCard) {
        slideCard.style.opacity = '0.35';
        slideCard.style.transform = 'scale(0.98)';
        setTimeout(function() {
          if (slideImg) slideImg.src = VF.static ? VF.static(s.img) : '../static/' + s.img;
          if (slideBadge) {
            slideBadge.className = 'vf-badge ' + s.badgeClass + ' mb-1';
            slideBadge.innerHTML = s.badge;
          }
          if (slideTitle) slideTitle.textContent = s.title;
          if (slideDesc) slideDesc.textContent = s.desc;
          if (slideCounter) slideCounter.textContent = '0' + (curSlide + 1) + ' / 0' + slides.length;
          slideDots.forEach(function(dot, dIdx) {
            dot.classList.toggle('is-active', dIdx === curSlide);
          });
          slideCard.style.opacity = '1';
          slideCard.style.transform = '';
        }, 160);
      }
    }

    var btnPrev = document.getElementById('heroSliderPrev');
    var btnNext = document.getElementById('heroSliderNext');
    if (btnPrev) btnPrev.addEventListener('click', function() { updateSlide(curSlide - 1); });
    if (btnNext) btnNext.addEventListener('click', function() { updateSlide(curSlide + 1); });

    slideDots.forEach(function(dot) {
      dot.addEventListener('click', function() {
        var idx = parseInt(this.dataset.slide, 10);
        if (!isNaN(idx)) updateSlide(idx);
      });
    });

    // Auto-avance suave cada 6s
    var sliderTimer = setInterval(function() {
      updateSlide(curSlide + 1);
    }, 6000);

    if (heroVisual) {
      heroVisual.addEventListener('mouseenter', function() { clearInterval(sliderTimer); });
      heroVisual.addEventListener('mouseleave', function() {
        clearInterval(sliderTimer);
        sliderTimer = setInterval(function() { updateSlide(curSlide + 1); }, 6000);
        // Reset transform al salir el cursor
        if (slideCard) {
          slideCard.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
        }
        stickers.forEach(function(st) {
          st.style.transform = '';
        });
      });

      // Efecto interactivo de perspectiva y movilidad al mover el ratón (Tilt & Parallax)
      heroVisual.addEventListener('mousemove', function(e) {
        var rect = heroVisual.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var centerX = rect.width / 2;
        var centerY = rect.height / 2;
        
        var deltaX = (x - centerX) / centerX; // -1 a 1
        var deltaY = (y - centerY) / centerY; // -1 a 1

        // Inclinación 3D para la tarjeta
        if (slideCard) {
          var tiltX = (deltaY * -7).toFixed(2);
          var tiltY = (deltaX * 7).toFixed(2);
          slideCard.style.transform = 'perspective(1000px) rotateX(' + tiltX + 'deg) rotateY(' + tiltY + 'deg) translateZ(6px)';
        }

        // Movilidad reactiva en stickers flotantes
        stickers.forEach(function(st, idx) {
          var factor = (idx + 1) * 12;
          st.style.transform = 'translate(' + (-deltaX * factor) + 'px, ' + (-deltaY * factor) + 'px)';
        });
      });
    }

    var container = document.getElementById('featuredVotes');
    var statAbiertas = document.querySelector('[data-stat="abiertas"]');
    if (!VF.data) return;

    var abiertas = VF.data.votaciones.filter(function (v) { return v.estado === 'abierta'; });
    if (statAbiertas) statAbiertas.textContent = abiertas.length;

    if (!container) return;
    container.innerHTML = '';

    // Mostramos hasta 3 votaciones destacadas
    var destacadas = VF.data.votaciones.slice(0, 3);
    destacadas.forEach(function (v, idx) {
      var cat = VF.q.categoria(v.categoriaId);
      var col = document.createElement('div');
      col.className = 'col-md-6 col-lg-4 vf-reveal vf-reveal-' + (idx + 1);

      var mediaHtml = '';
      if (v.imagen) {
        mediaHtml = '<img src="' + VF.static(v.imagen) + '" alt="' + VF.esc(v.imagenAlt || v.nombre) + '" loading="lazy">';
      } else {
        mediaHtml = '<div class="vf-art vf-art--' + (v.arte || 'night') + '"><i class="bi ' + (v.icono || 'bi-music-note-beamed') + '"></i></div>';
      }

      var actionBtn = '';
      if (v.estado === 'abierta') {
        actionBtn = '<a href="' + VF.url('detalle', { v: v.id }) + '" class="btn btn-vf btn-sm w-100">Ver candidatos y votar <i class="bi bi-arrow-right"></i></a>';
      } else if (v.estado === 'proxima') {
        actionBtn = '<button class="btn btn-vf-outline btn-sm w-100 is-locked" aria-disabled="true" title="Esta votación aún no inicia"><i class="bi bi-hourglass-split"></i> Próximamente</button>';
      } else {
        actionBtn = '<a href="' + VF.url('resultados') + '" class="btn btn-vf-outline btn-sm w-100"><i class="bi bi-bar-chart"></i> Ver resultados</a>';
      }

      var accents = ['vf-card--window-yellow', 'vf-card--window-royal', 'vf-card--window-orange', 'vf-card--window-green', 'vf-card--window-red'];
      var cardAccent = accents[idx % accents.length];

      col.innerHTML = 
        '<article class="vf-card vote-card ' + cardAccent + '">' +
          '<div class="vote-card__media">' +
            mediaHtml +
            '<div class="vote-card__status">' + VF.statusBadge(v.estado) + '</div>' +
            '<span class="vote-card__num">0' + (idx + 1) + '</span>' +
          '</div>' +
          '<div class="vote-card__body">' +
            '<span class="vote-card__cat">' + VF.esc(cat ? cat.nombre : 'Festival 2027') + '</span>' +
            '<h3 class="vote-card__title h4"><a href="' + VF.url('detalle', { v: v.id }) + '" class="text-decoration-none text-dark">' + VF.esc(v.nombre) + '</a></h3>' +
            '<p class="vote-card__desc">' + VF.esc(v.descripcion) + '</p>' +
            '<div class="vote-card__dates">' +
              '<i class="bi bi-calendar3"></i><span>Cierre: ' + VF.fmtDate(v.cierre) + '</span>' +
            '</div>' +
          '</div>' +
          '<div class="vote-card__foot">' + actionBtn + '</div>' +
        '</article>';

      container.appendChild(col);
    });
  };

  /* -------------------------------------------------------------------------
     PANTALLA 2: LISTADO DE VOTACIONES
     ------------------------------------------------------------------------- */
  VF.pages.votaciones = function () {
    var container = document.getElementById('votesListContainer');
    var emptyBox = document.getElementById('noVotesFound');
    var searchInput = document.getElementById('searchVotesInput');
    var chipButtons = document.querySelectorAll('[data-status-filter]');
    var currentFilter = 'todas';
    var currentSearch = '';

    if (!VF.data) return;

    // Actualizar contadores en los chips
    var todas = VF.data.votaciones.length;
    var ab = VF.data.votaciones.filter(function (v) { return v.estado === 'abierta'; }).length;
    var px = VF.data.votaciones.filter(function (v) { return v.estado === 'proxima'; }).length;
    var cr = VF.data.votaciones.filter(function (v) { return v.estado === 'cerrada'; }).length;

    var elTodas = document.getElementById('countTodas');
    var elAb = document.getElementById('countAbiertas');
    var elPx = document.getElementById('countProximas');
    var elCr = document.getElementById('countCerradas');
    if (elTodas) elTodas.textContent = todas;
    if (elAb) elAb.textContent = ab;
    if (elPx) elPx.textContent = px;
    if (elCr) elCr.textContent = cr;

    function renderFiltered() {
      var filtered = VF.data.votaciones.filter(function (v) {
        var matchStatus = (currentFilter === 'todas') || (v.estado === currentFilter);
        var matchText = true;
        if (currentSearch.trim() !== '') {
          var cat = VF.q.categoria(v.categoriaId);
          var q = currentSearch.toLowerCase();
          var hayEnNombre = v.nombre.toLowerCase().indexOf(q) > -1;
          var hayEnDesc = v.descripcion.toLowerCase().indexOf(q) > -1;
          var hayEnCat = cat && cat.nombre.toLowerCase().indexOf(q) > -1;
          matchText = hayEnNombre || hayEnDesc || hayEnCat;
        }
        return matchStatus && matchText;
      });

      container.innerHTML = '';
      if (filtered.length === 0) {
        emptyBox.classList.remove('d-none');
        return;
      }
      emptyBox.classList.add('d-none');

      filtered.forEach(function (v, idx) {
        var cat = VF.q.categoria(v.categoriaId);
        var col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';

        var mediaHtml = '';
        if (v.imagen) {
          mediaHtml = '<img src="' + VF.static(v.imagen) + '" alt="' + VF.esc(v.imagenAlt || v.nombre) + '" loading="lazy">';
        } else {
          mediaHtml = '<div class="vf-art vf-art--' + (v.arte || 'night') + '"><i class="bi ' + (v.icono || 'bi-music-note-beamed') + '"></i></div>';
        }

        var actionBtn = '';
        if (v.estado === 'abierta') {
          actionBtn = '<a href="' + VF.url('detalle', { v: v.id }) + '" class="btn btn-vf btn-sm w-100">Participar y votar <i class="bi bi-arrow-right"></i></a>';
        } else if (v.estado === 'proxima') {
          actionBtn = '<button class="btn btn-vf-outline btn-sm w-100 is-locked" aria-disabled="true"><i class="bi bi-hourglass-split"></i> Votación Próxima</button>';
        } else {
          actionBtn = v.resultadosPublicados ? 
            '<a href="' + VF.url('resultados') + '" class="btn btn-vf-outline btn-sm w-100"><i class="bi bi-bar-chart"></i> Consultar resultados</a>' :
            '<button class="btn btn-vf-outline btn-sm w-100 is-locked" aria-disabled="true"><i class="bi bi-lock-fill"></i> Resultados en proceso</button>';
        }

        var accents = ['vf-card--window-yellow', 'vf-card--window-royal', 'vf-card--window-orange', 'vf-card--window-green', 'vf-card--window-red'];
        var cardAccent = accents[idx % accents.length];

        col.innerHTML = 
          '<article class="vf-card vote-card ' + cardAccent + '">' +
            '<div class="vote-card__media">' +
              mediaHtml +
              '<div class="vote-card__status">' + VF.statusBadge(v.estado) + '</div>' +
            '</div>' +
            '<div class="vote-card__body">' +
              '<span class="vote-card__cat">' + VF.esc(cat ? cat.nombre : 'Festival 2027') + '</span>' +
              '<h3 class="vote-card__title h4"><a href="' + VF.url('detalle', { v: v.id }) + '" class="text-decoration-none text-dark">' + VF.esc(v.nombre) + '</a></h3>' +
              '<p class="vote-card__desc">' + VF.esc(v.descripcion) + '</p>' +
              '<div class="vote-card__dates">' +
                '<i class="bi bi-clock"></i><span>Apertura: ' + VF.fmtDate(v.apertura) + ' | Cierre: ' + VF.fmtDate(v.cierre) + '</span>' +
              '</div>' +
            '</div>' +
            '<div class="vote-card__foot">' + actionBtn + '</div>' +
          '</article>';

        container.appendChild(col);
      });
    }

    chipButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        chipButtons.forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        btn.setAttribute('aria-pressed', 'true');
        currentFilter = btn.dataset.statusFilter;
        renderFiltered();
      });
    });

    if (searchInput) {
      searchInput.addEventListener('input', function (e) {
        currentSearch = e.target.value;
        renderFiltered();
      });
    }

    var resetBtn = document.getElementById('btnResetFilters');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        currentFilter = 'todas';
        currentSearch = '';
        if (searchInput) searchInput.value = '';
        chipButtons.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.statusFilter === 'todas'); });
        renderFiltered();
      });
    }

    renderFiltered();
  };

  /* -------------------------------------------------------------------------
     PANTALLA 3: DETALLE DE VOTACIÓN Y SELECCIÓN EXCLUSIVA DE CANDIDATOS
     ------------------------------------------------------------------------- */
  VF.pages.detalle_votacion = function () {
    var voteId = getActiveVoteId();
    sessionVoterState.selectedVoteId = voteId;

    var vote = VF.q.votacion(voteId) || VF.data.votaciones[0];
    var cat = VF.q.categoria(vote.categoriaId);
    var opciones = VF.q.opcionesDe(vote.id);

    // Actualizar Encabezado
    var elTitle = document.getElementById('voteTitle');
    var elDesc = document.getElementById('voteDescription');
    var elBreadcrumb = document.getElementById('breadcrumbCurrentVote');
    var elCat = document.getElementById('voteCategoryBadge');
    var elStatusContainer = document.getElementById('voteStatusBadgeContainer');
    var elDates = document.getElementById('voteDatesInfo');

    if (elTitle) elTitle.textContent = vote.nombre;
    if (elDesc) elDesc.textContent = vote.descripcion;
    if (elBreadcrumb) elBreadcrumb.textContent = vote.nombre;
    if (elCat) elCat.textContent = cat ? cat.nombre : 'Festival 2027';
    if (elStatusContainer) elStatusContainer.innerHTML = VF.statusBadge(vote.estado);
    if (elDates) elDates.innerHTML = '<i class="bi bi-clock me-1"></i>Periodo: ' + VF.fmtDate(vote.apertura) + ' - ' + VF.fmtDate(vote.cierre);

    var grid = document.getElementById('candidatesGrid');
    var alertNotOpen = document.getElementById('voteNotOpenAlert');
    var btnContinue = document.getElementById('btnContinueSelection');
    var summaryText = document.getElementById('selectedOptionSummaryText');
    var errEl = document.getElementById('selectionErrorMsg');
    var form = document.getElementById('voteSelectionForm');

    // Regla de Negocio: Si no está abierta, no permite selección activa
    if (vote.estado !== 'abierta') {
      if (alertNotOpen) alertNotOpen.classList.remove('d-none');
      if (btnContinue) {
        btnContinue.disabled = true;
        btnContinue.classList.add('disabled');
        btnContinue.textContent = 'Votación ' + vote.estado;
      }
    }

    if (!grid) return;
    grid.innerHTML = '';

    opciones.forEach(function (op) {
      var col = document.createElement('div');
      col.className = 'col-sm-6 col-lg-4';

      var tagsHtml = '';
      if (op.datos && op.datos.length) {
        tagsHtml = op.datos.map(function (d) { return '<span>' + VF.esc(d) + '</span>'; }).join('');
      }

      var disabledAttr = (vote.estado !== 'abierta' || op.estado !== 'activa') ? 'disabled' : '';
      var disabledClass = disabledAttr ? ' is-disabled' : '';

      col.innerHTML = 
        '<label class="option-card' + disabledClass + '" for="optRadio_' + op.id + '">' +
          '<input type="radio" name="candidateOption" id="optRadio_' + op.id + '" value="' + op.id + '" ' + disabledAttr + ' required>' +
          '<div class="option-card__check" aria-hidden="true"><i class="bi bi-check-lg"></i></div>' +
          VF.avatar(op) +
          '<div class="option-card__body">' +
            '<span class="vf-status vf-status--borrador py-0 px-2 small">Participante oficial</span>' +
            '<h3 class="h5 mt-2 mb-1">' + VF.esc(op.nombre) + '</h3>' +
            '<p class="small text-muted mb-0">' + VF.esc(op.descripcion) + '</p>' +
            (tagsHtml ? '<div class="option-card__meta">' + tagsHtml + '</div>' : '') +
            '<div class="option-card__selected"><i class="bi bi-check-circle-fill me-1"></i>Opción seleccionada</div>' +
          '</div>' +
        '</label>';

      grid.appendChild(col);
    });

    // Control de selección exclusiva
    grid.addEventListener('change', function (e) {
      if (e.target && e.target.name === 'candidateOption') {
        sessionVoterState.selectedOptionId = e.target.value;
        var chosen = VF.q.opcion(e.target.value);
        if (summaryText && chosen) {
          summaryText.textContent = 'Seleccionaste: ' + chosen.nombre;
          summaryText.classList.remove('text-muted');
          summaryText.classList.add('text-success', 'fw-bold');
        }
        if (errEl) errEl.style.setProperty('display', 'none', 'important');
      }
    });

    // Envío a validación mediante el modal de identidad
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var selected = form.querySelector('input[name="candidateOption"]:checked');
        if (!selected) {
          if (errEl) errEl.style.setProperty('display', 'block', 'important');
          VF.toast('Por favor selecciona una opción para continuar.', 'warning');
          return;
        }
        sessionVoterState.selectedOptionId = selected.value;

        // Abrir la ventana modal de validación de identidad
        var modalEl = document.getElementById('voterAccessModal');
        if (modalEl && window.bootstrap) {
          var modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
          modal.show();
        } else {
          // Fallback en caso de no contar con bootstrap modal
          window.location.href = VF.url('acceso', { v: vote.id, opt: selected.value });
        }
      });
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 4: VALIDACIÓN DEL VOTANTE (ACCESO)
     ------------------------------------------------------------------------- */
  VF.pages.acceso_votante = function () {
    var voteId = getActiveVoteId();
    var optId = VF.param('opt') || sessionVoterState.selectedOptionId || 'op-01';
    sessionVoterState.selectedVoteId = voteId;
    sessionVoterState.selectedOptionId = optId;

    var vote = VF.q.votacion(voteId) || VF.data.votaciones[0];
    var opcion = VF.q.opcion(optId) || VF.data.opciones[0];

    var elVoteTitle = document.getElementById('authVoteTitleSummary');
    var elCandidate = document.getElementById('authCandidateSummary');
    if (elVoteTitle) elVoteTitle.textContent = vote.nombre;
    if (elCandidate) elCandidate.textContent = 'Candidato: ' + opcion.nombre;

    var form = document.getElementById('voterLoginForm');
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var isValid = VF.validate(form);
        if (!isValid) {
          VF.toast('Por favor completa todos los campos requeridos correctamente.', 'danger');
          return;
        }

        var doc = document.getElementById('cedulaInput').value.trim();
        var email = document.getElementById('correoInput').value.trim();

        // Enmascaramos datos en memoria temporal (no guardar en claro)
        sessionVoterState.voterDoc = 'C.C. ••••••' + doc.slice(-3);
        sessionVoterState.voterEmail = email.replace(/(.{2})(.*)(?=@)/, function (_, a, b) { return a + '•••'; });

        VF.toast('Identidad validada en modo demostración.', 'success');
        setTimeout(function () {
          window.location.href = VF.url('confirmar', { v: vote.id, opt: opcion.id });
        }, 400);
      });
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 5: CONFIRMACIÓN DEL VOTO Y SEGUNDA CONFIRMACIÓN MODAL
     ------------------------------------------------------------------------- */
  VF.pages.confirmar_voto = function () {
    var voteId = getActiveVoteId();
    var optId = VF.param('opt') || sessionVoterState.selectedOptionId || 'op-01';

    var vote = VF.q.votacion(voteId) || VF.data.votaciones[0];
    var cat = VF.q.categoria(vote.categoriaId);
    var opcion = VF.q.opcion(optId) || VF.data.opciones[0];

    // Poblar resumen en la interfaz
    var elVote = document.getElementById('confVoteName');
    var elCat = document.getElementById('confCategoryName');
    var elCandidate = document.getElementById('confCandidateName');
    var elDesc = document.getElementById('confCandidateDesc');
    var elAvatar = document.getElementById('confAvatarContainer');
    var elDoc = document.getElementById('confVoterDoc');
    var elEmail = document.getElementById('confVoterEmail');

    if (elVote) elVote.textContent = vote.nombre;
    if (elCat) elCat.textContent = cat ? cat.nombre : 'Festival 2027';
    if (elCandidate) elCandidate.textContent = opcion.nombre;
    if (elDesc) elDesc.textContent = opcion.descripcion;
    if (elAvatar) elAvatar.innerHTML = VF.avatar(opcion);

    if (elDoc && sessionVoterState.voterDoc) elDoc.textContent = sessionVoterState.voterDoc;
    if (elEmail && sessionVoterState.voterEmail) elEmail.textContent = sessionVoterState.voterEmail;

    var btnTrigger = document.getElementById('btnTriggerModalConfirm');
    var modalEl = document.getElementById('modalFinalConfirm');
    var btnDefinitive = document.getElementById('btnDefinitiveConfirmVote');
    var modalCandidateName = document.getElementById('modalConfirmCandidate');
    var modalCategoryName = document.getElementById('modalConfirmCategory');

    if (modalCandidateName) modalCandidateName.textContent = opcion.nombre;
    if (modalCategoryName) modalCategoryName.textContent = cat ? cat.nombre : vote.nombre;

    if (btnTrigger && modalEl && window.bootstrap) {
      btnTrigger.addEventListener('click', function () {
        var modal = new window.bootstrap.Modal(modalEl);
        modal.show();
      });
    }

    if (btnDefinitive) {
      btnDefinitive.addEventListener('click', function () {
        btnDefinitive.disabled = true;
        btnDefinitive.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Registrando voto...';

        setTimeout(function () {
          window.location.href = VF.url('comprobante', { v: vote.id, opt: opcion.id });
        }, 600);
      });
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 6: COMPROBANTE DE VOTO
     ------------------------------------------------------------------------- */
  VF.pages.comprobante = function () {
    var voteId = getActiveVoteId();
    var vote = VF.q.votacion(voteId) || VF.data.votaciones[0];
    var cat = VF.q.categoria(vote.categoriaId);

    var elVote = document.getElementById('rcptVoteTitle');
    var elCat = document.getElementById('rcptCategoryTitle');
    var elTime = document.getElementById('rcptTimestamp');
    var elVoter = document.getElementById('rcptVoterMask');
    var elCode = document.getElementById('rcptHashCode');

    if (elVote) elVote.textContent = vote.nombre;
    if (elCat) elCat.textContent = cat ? cat.nombre : 'Festival 2027';
    if (elTime) elTime.textContent = VF.fmtDateTime(new Date().toISOString());
    if (elVoter && sessionVoterState.voterDoc) elVoter.textContent = sessionVoterState.voterDoc;

    if (elCode) {
      // Generación de un identificador simulado único para la demostración
      var rand = Math.random().toString(36).substring(2, 6).toUpperCase();
      elCode.textContent = 'VF2027-SIM-' + rand + '-C78A-94DF';
    }
  };

  /* -------------------------------------------------------------------------
     PANTALLA 7: RESULTADOS PÚBLICOS AUTORIZADOS
     ------------------------------------------------------------------------- */
  VF.pages.resultados = function () {
    var container = document.getElementById('resultsListContainer');
    var selectEdition = document.getElementById('resultsEditionSelect');
    if (!VF.data || !container) return;

    function renderEditionResults(edId) {
      container.innerHTML = '';
      var votacionesCerradas = VF.data.votaciones.filter(function (v) {
        return v.edicionId === edId && v.estado === 'cerrada';
      });

      if (votacionesCerradas.length === 0) {
        container.innerHTML = 
          '<div class="vf-empty">' +
            '<i class="bi bi-clock-history"></i>' +
            '<h3>No hay resultados publicados para esta edición</h3>' +
            '<p class="text-muted">Las votaciones aún se encuentran en periodo de recepción o en fase de validación técnica de escrutinios.</p>' +
          '</div>';
        return;
      }

      votacionesCerradas.forEach(function (v) {
        var cat = VF.q.categoria(v.categoriaId);
        var card = document.createElement('div');
        card.className = 'vf-card vf-card--pad mb-4 result-card';

        // Si la votación está cerrada pero NO tiene resultados autorizados para publicación:
        if (!v.resultadosPublicados) {
          card.innerHTML = 
            '<div class="result-card__head">' +
              '<div>' +
                '<span class="vf-status vf-status--cerrada mb-1"><i class="bi bi-lock-fill"></i> Votación Cerrada</span>' +
                '<h2 class="h4">' + VF.esc(v.nombre) + '</h2>' +
                '<span class="text-muted small">Categoría: ' + VF.esc(cat ? cat.nombre : '') + '</span>' +
              '</div>' +
              '<span class="vf-status vf-status--pendiente"><i class="bi bi-clock"></i> Resultados en proceso</span>' +
            '</div>' +
            '<div class="result-locked">' +
              '<i class="bi bi-shield-lock"></i>' +
              '<div>' +
                '<strong>Resultados en proceso de auditoría y validación</strong>' +
                '<p class="small mb-0">De acuerdo con las reglas de transparencia, las cifras oficiales serán divulgadas una vez concluya el escrutinio final.</p>' +
              '</div>' +
            '</div>';
          container.appendChild(card);
          return;
        }

        // Si los resultados están publicados, calcular porcentajes legítimos de los datos demo
        var resultadosLista = VF.data.resultados[v.id] || [];
        var totalVotos = resultadosLista.reduce(function (sum, item) { return sum + item.votos; }, 0);

        var rowsHtml = '';
        var maxVotos = Math.max.apply(null, resultadosLista.map(function (r) { return r.votos; }));

        resultadosLista.forEach(function (res) {
          var op = VF.q.opcion(res.opcionId);
          var pct = totalVotos > 0 ? (res.votos / totalVotos * 100) : 0;
          var isLeader = res.votos === maxVotos;
          var leadClass = isLeader ? ' vf-bar--lead' : '';

          rowsHtml += 
            '<div class="vf-bar' + leadClass + '">' +
              '<div class="vf-bar__head">' +
                '<span>' + (isLeader ? '<i class="bi bi-trophy-fill text-gold me-1" title="Opción más votada"></i>' : '') + 
                '<strong>' + VF.esc(op ? op.nombre : 'Opción') + '</strong></span>' +
                '<span>' + VF.fmtNum(res.votos) + ' votos (' + VF.fmtPct(pct) + ')</span>' +
              '</div>' +
              '<div class="progress" role="progressbar" aria-valuenow="' + pct.toFixed(1) + '" aria-valuemin="0" aria-valuemax="100">' +
                '<div class="progress-bar" style="width: ' + pct.toFixed(1) + '%"></div>' +
              '</div>' +
            '</div>';
        });

        card.innerHTML = 
          '<div class="result-card__head">' +
            '<div>' +
              '<span class="vf-status vf-status--publicado mb-1"><i class="bi bi-patch-check-fill"></i> Resultados Publicados</span>' +
              '<h2 class="h4">' + VF.esc(v.nombre) + '</h2>' +
              '<span class="text-muted small">Categoría: ' + VF.esc(cat ? cat.nombre : '') + ' | Total votos procesados: <strong>' + VF.fmtNum(totalVotos) + '</strong></span>' +
            '</div>' +
            '<span class="vf-badge vf-badge--green"><i class="bi bi-patch-check"></i>Escrutinio Oficial</span>' +
          '</div>' +
          '<div class="mt-4">' + rowsHtml + '</div>' +
          '<div class="pt-3 border-top d-flex justify-content-between align-items-center text-muted small">' +
            '<span><i class="bi bi-calendar-check me-1"></i>Publicado el: ' + VF.fmtDate(v.fechaPublicacion) + '</span>' +
            '<span class="fst-italic">Escrutinio validado por la comisión técnica</span>' +
          '</div>';

        container.appendChild(card);
      });
    }

    if (selectEdition) {
      selectEdition.addEventListener('change', function (e) {
        renderEditionResults(e.target.value);
      });
    }
  };
  /* -------------------------------------------------------------------------
     MANEJO DEL MODAL DE ACCESO DEL VOTANTE (GLOBAL)
     ------------------------------------------------------------------------- */
  function initVoterModalHandler() {
    var modalForm = document.getElementById('modalVoterForm');
    if (!modalForm) return;

    modalForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var isValid = VF.validate(modalForm);
      if (!isValid) {
        VF.toast('Por favor completa todos los campos requeridos.', 'danger');
        return;
      }

      var doc = document.getElementById('modalCedulaInput').value.trim();
      var email = document.getElementById('modalCorreoInput').value.trim();

      // Guardar en sesión de memoria del prototipo
      sessionVoterState.voterDoc = 'C.C. ••••••' + doc.slice(-3);
      sessionVoterState.voterEmail = email.replace(/(.{2})(.*)(?=@)/, function (_, a, b) { return a + '•••'; });

      // Ocultar modal
      var modalEl = document.getElementById('voterAccessModal');
      if (modalEl && window.bootstrap) {
        var modal = window.bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }

      VF.toast('Identidad validada con éxito.', 'success');

      // Si ya hay opción elegida, ir a confirmar voto; si no, ir a listado de votaciones
      setTimeout(function () {
        var vId = sessionVoterState.selectedVoteId || 'v-prof';
        var oId = sessionVoterState.selectedOptionId;
        if (oId) {
          window.location.href = VF.url('confirmar', { v: vId, opt: oId });
        } else {
          window.location.href = VF.url('votaciones');
        }
      }, 400);
    });
  }

  /* -------------------------------------------------------------------------
     MANEJO DEL MODAL DE INICIO DE SESIÓN (LOGIN MODAL GLOBAL)
     ------------------------------------------------------------------------- */
  function initLoginModalHandler() {
    // Votante en Modal
    var modalVoterForm = document.getElementById('modalVoterLoginForm');
    if (modalVoterForm) {
      modalVoterForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!VF.validate(modalVoterForm)) {
          VF.toast('Por favor completa todos los campos requeridos.', 'danger');
          return;
        }

        var doc = document.getElementById('modalLoginCedula').value.trim();
        var email = document.getElementById('modalLoginCorreo').value.trim();

        sessionVoterState.voterDoc = 'C.C. ••••••' + doc.slice(-3);
        sessionVoterState.voterEmail = email.replace(/(.{2})(.*)(?=@)/, function (_, a, b) { return a + '•••'; });

        var modalEl = document.getElementById('loginModal');
        if (modalEl && window.bootstrap) {
          var modal = window.bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();
        }

        VF.toast('¡Identidad validada con éxito! Ingresando a las votaciones...', 'success');
        setTimeout(function () {
          window.location.href = VF.url('votaciones');
        }, 500);
      });
    }

    // Administrador en Modal
    var modalAdminForm = document.getElementById('modalAdminLoginForm');
    if (modalAdminForm) {
      modalAdminForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!VF.validate(modalAdminForm)) {
          VF.toast('Ingresa tu usuario y contraseña institucional.', 'danger');
          return;
        }

        var modalEl = document.getElementById('loginModal');
        if (modalEl && window.bootstrap) {
          var modal = window.bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();
        }

        VF.toast('¡Credenciales autorizadas! Accediendo al Panel de Control...', 'success');
        setTimeout(function () {
          window.location.href = VF.url('panel_dashboard');
        }, 500);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initVoterModalHandler();
      initLoginModalHandler();
    });
  } else {
    initVoterModalHandler();
    initLoginModalHandler();
  }

  /* -------------------------------------------------------------------------
     PANTALLAS INFORMATIVAS Y AUTENTICACIÓN
     ------------------------------------------------------------------------- */
  VF.pages.guia = function () {};
  VF.pages.privacidad = function () {};

  VF.pages.login = function () {
    // Formulario de Votante
    var voterForm = document.getElementById('voterDirectLoginForm');
    if (voterForm) {
      voterForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!VF.validate(voterForm)) {
          VF.toast('Por favor completa todos los campos requeridos.', 'danger');
          return;
        }

        var cedula = document.getElementById('loginCedula').value.trim();
        var correo = document.getElementById('loginCorreo').value.trim();

        sessionVoterState.voterDoc = 'C.C. ••••••' + cedula.slice(-3);
        sessionVoterState.voterEmail = correo.replace(/(.{2})(.*)(?=@)/, function (_, a, b) { return a + '•••'; });

        VF.toast('¡Identidad validada con éxito! Ingresando a las votaciones...', 'success');
        setTimeout(function () {
          window.location.href = VF.url('votaciones');
        }, 500);
      });
    }

    // Formulario de Administrador
    var adminForm = document.getElementById('adminLoginForm');
    if (adminForm) {
      adminForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!VF.validate(adminForm)) {
          VF.toast('Ingresa tu usuario y contraseña institucional.', 'danger');
          return;
        }

        VF.toast('¡Credenciales autorizadas! Accediendo al Panel de Control...', 'success');
        setTimeout(function () {
          window.location.href = VF.url('panel_dashboard');
        }, 500);
      });
    }
  };

})(window, document, window.VF);
