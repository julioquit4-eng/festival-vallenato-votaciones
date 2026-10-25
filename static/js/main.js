/* ==========================================================================
   main.js — Núcleo de interfaz compartido (portal + panel)
   --------------------------------------------------------------------------
   Expone un único espacio de nombres global: window.VF
   • VF.url(nombre, params)  -> URLs definidas en <script id="app-urls"> (generadas con {% url %})
   • VF.toast(msg, tipo)     -> mensajes de éxito / advertencia / error / información
   • VF.confirm({...})       -> confirmación modal (Promise<boolean>)
   • VF.validate(form, fn)   -> validación VISUAL de formularios (no sustituye al servidor)
   • VF.pages[pageId]        -> inicializadores por pantalla (voting.js / admin.js)
   IMPORTANTE: este archivo no implementa seguridad ni lógica de negocio real.
   ========================================================================== */
(function (window, document) {
  'use strict';

  var VF = window.VF = window.VF || {};
  VF.pages = VF.pages || {};

  /* ------------------------------ URLs ---------------------------------- */
  VF.urls = (function () {
    var node = document.getElementById('app-urls');
    if (!node) return {};
    try { return JSON.parse(node.textContent); } catch (e) { console.warn('[VF] app-urls inválido', e); return {}; }
  })();

  VF.url = function (name, params) {
    var base = VF.urls[name] || '#';
    if (!params) return base;
    var qs = new URLSearchParams();
    Object.keys(params).forEach(function (k) {
      if (params[k] !== null && params[k] !== undefined && params[k] !== '') qs.append(k, params[k]);
    });
    var s = qs.toString();
    return s ? base + (base.indexOf('?') > -1 ? '&' : '?') + s : base;
  };
  VF.static = function (path) { return (VF.urls.static || '') + path; };
  VF.param = function (key) { return new URLSearchParams(window.location.search).get(key); };

  /* ------------------------------ Utilidades ---------------------------- */
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  VF.esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ESC[c]; }); };
  VF.data = window.VFDemo ? window.VFDemo.data : null;
  VF.q = window.VFDemo ? window.VFDemo.q : null;
  VF.clone = function (o) { return typeof structuredClone === 'function' ? structuredClone(o) : JSON.parse(JSON.stringify(o)); };

  var dateFmt = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });
  var dateTimeFmt = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' });
  VF.fmtDate = function (iso) { if (!iso) return 'Sin fecha'; var d = new Date(iso); return isNaN(d) ? 'Sin fecha' : dateFmt.format(d); };
  VF.fmtDateTime = function (iso) { if (!iso) return 'Sin fecha'; var d = new Date(iso); return isNaN(d) ? 'Sin fecha' : dateTimeFmt.format(d); };
  VF.fmtNum = function (n) { return new Intl.NumberFormat('es-CO').format(n); };
  VF.fmtPct = function (n) { return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(n) + ' %'; };

  /* Tonos de los avatares ficticios */
  VF.TONES = [['#183B56', '#10243A'], ['#8E3A27', '#4A1E16'], ['#1F5A4A', '#0F2F28'], ['#5B4A8A', '#2C2347']];
  VF.avatar = function (op, extraClass) {
    var t = VF.TONES[(op && op.tono) || 0] || VF.TONES[0];
    return '<div class="vf-avatar ' + (extraClass || '') + '" style="--vf-av-a:' + t[0] + ';--vf-av-b:' + t[1] + '" role="img" aria-label="Imagen ilustrativa ficticia de ' + VF.esc(op.nombre) + '">' + VF.esc(op.iniciales) + '</div>';
  };

  /* ------------------------------ Estados ------------------------------- */
  VF.STATUS = {
    abierta: { label: 'Abierta', icon: 'bi-unlock-fill' },
    proxima: { label: 'Próximamente', icon: 'bi-hourglass-split' },
    cerrada: { label: 'Cerrada', icon: 'bi-lock-fill' },
    pausada: { label: 'Pausada', icon: 'bi-pause-circle-fill' },
    borrador: { label: 'Borrador', icon: 'bi-pencil-square' },
    publicado: { label: 'Resultados publicados', icon: 'bi-patch-check-fill' },
    pendiente: { label: 'Pendiente de publicación', icon: 'bi-clock-history' },
    activa: { label: 'Activa', icon: 'bi-check-circle-fill' },
    inactiva: { label: 'Inactiva', icon: 'bi-dash-circle' },
    habilitado: { label: 'Habilitado', icon: 'bi-person-check-fill' },
    inhabilitado: { label: 'No habilitado', icon: 'bi-person-x-fill' }
  };
  VF.statusBadge = function (key, opts) {
    var m = VF.STATUS[key] || { label: key, icon: 'bi-circle' };
    var sim = opts && opts.simulated ? ' vf-status--simulado' : '';
    return '<span class="vf-status vf-status--' + VF.esc(key) + sim + '"><i class="bi ' + m.icon + '" aria-hidden="true"></i>' + VF.esc((opts && opts.label) || m.label) + '</span>';
  };
  VF.demoTag = function (text) { return '<span class="vf-badge vf-badge--yellow"><i class="bi bi-music-note-beamed" aria-hidden="true"></i>' + VF.esc(text || 'Festival 2027') + '</span>'; };

  /* ------------------------------ Toasts -------------------------------- */
  var TOAST_ICON = { success: 'bi-check-circle-fill', danger: 'bi-x-octagon-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
  VF.toast = function (message, type) {
    type = type || 'info';
    var region = document.getElementById('vfToastRegion');
    if (!region || !window.bootstrap) { window.alert(message); return; }
    var el = document.createElement('div');
    el.className = 'toast vf-toast vf-toast--' + type;
    el.setAttribute('role', type === 'danger' ? 'alert' : 'status');
    el.setAttribute('aria-live', type === 'danger' ? 'assertive' : 'polite');
    el.setAttribute('aria-atomic', 'true');
    el.innerHTML = '<div class="toast-body"><i class="bi ' + TOAST_ICON[type] + '" aria-hidden="true"></i><div class="flex-grow-1">' + VF.esc(message) + '</div>' +
      '<button type="button" class="btn-close ms-2" data-bs-dismiss="toast" aria-label="Cerrar mensaje"></button></div>';
    region.appendChild(el);
    el.addEventListener('hidden.bs.toast', function () { el.remove(); });
    new window.bootstrap.Toast(el, { delay: type === 'danger' ? 7000 : 5000 }).show();
  };
  VF.SIM_MSG = 'Cambio simulado en memoria: no se guardó en ninguna base de datos.';

  /* --------------------------- Confirmación modal ----------------------- */
  VF.confirm = function (opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      var modalEl = document.getElementById('vfConfirmModal');
      if (!modalEl || !window.bootstrap) { resolve(window.confirm(opts.message || '¿Confirmas la acción?')); return; }
      modalEl.querySelector('#vfConfirmTitle').textContent = opts.title || 'Confirmar acción';
      modalEl.querySelector('#vfConfirmMessage').textContent = opts.message || '';
      var note = modalEl.querySelector('#vfConfirmNote');
      note.textContent = opts.note || '';
      note.hidden = !opts.note;
      var icon = modalEl.querySelector('#vfConfirmIcon');
      icon.className = 'vf-icon-circle ' + (opts.variant === 'danger' ? 'vf-icon-circle--danger' : 'vf-icon-circle--night');
      icon.innerHTML = '<i class="bi ' + (opts.icon || 'bi-question-lg') + '" aria-hidden="true"></i>';
      var ok = modalEl.querySelector('#vfConfirmOk');
      ok.textContent = opts.confirmText || 'Confirmar';
      ok.className = 'btn ' + (opts.variant === 'danger' ? 'btn-danger' : 'btn-vf');
      var result = false;
      var ctrl = new AbortController();
      ok.addEventListener('click', function () { result = true; modal.hide(); }, { signal: ctrl.signal });
      modalEl.addEventListener('hidden.bs.modal', function () { ctrl.abort(); resolve(result); }, { signal: ctrl.signal });
      var modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    });
  };

  /* ------------------------- Validación de formularios ------------------ */
  function feedbackFor(field) {
    var id = (field.id || field.name) + '-error';
    var fb = document.getElementById(id);
    if (!fb) {
      fb = document.createElement('div');
      fb.className = 'invalid-feedback';
      fb.id = id;
      var anchor = field.closest('.form-check') || field.closest('.input-group') || field;
      if (anchor === field) field.insertAdjacentElement('afterend', fb); else anchor.appendChild(fb);
    }
    var described = (field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
    if (described.indexOf(id) === -1) { described.push(id); field.setAttribute('aria-describedby', described.join(' ')); }
    return fb;
  }
  function messageFor(field) {
    var v = field.validity;
    if (v.valueMissing) return field.dataset.msgRequired || 'Este campo es obligatorio.';
    if (v.typeMismatch) return field.dataset.msgType || 'El formato no es válido.';
    if (v.patternMismatch) return field.dataset.msgPattern || 'El formato no es válido.';
    if (v.tooShort || v.tooLong) return field.dataset.msgLength || field.validationMessage;
    if (v.rangeUnderflow || v.rangeOverflow) return field.dataset.msgRange || field.validationMessage;
    return field.validationMessage || 'Revisa este campo.';
  }
  VF.setFieldState = function (field, valid, message) {
    field.classList.toggle('is-invalid', !valid);
    field.setAttribute('aria-invalid', valid ? 'false' : 'true');
    var fb = feedbackFor(field);
    fb.textContent = valid ? '' : (message || messageFor(field));
    var wrap = field.closest('.vf-input-icon');
    if (wrap) wrap.classList.toggle('has-error', !valid);
  };
  /**
   * Valida un formulario. `custom(form)` puede llamar a field.setCustomValidity('mensaje').
   * Devuelve true si es válido. Enfoca el primer campo inválido.
   */
  VF.validate = function (form, custom) {
    var fields = Array.prototype.slice.call(form.querySelectorAll('input, select, textarea')).filter(function (f) {
      return !f.disabled && f.type !== 'hidden' && f.type !== 'radio' && f.type !== 'submit' && f.type !== 'button';
    });
    fields.forEach(function (f) { f.setCustomValidity(''); });
    if (typeof custom === 'function') custom(form);
    var firstInvalid = null;
    fields.forEach(function (f) {
      var ok = f.checkValidity();
      VF.setFieldState(f, ok);
      if (!ok && !firstInvalid) firstInvalid = f;
    });
    form.dataset.validated = 'true';
    if (firstInvalid) firstInvalid.focus();
    return !firstInvalid;
  };
  /* Revalidación en vivo de un campo después del primer intento de envío */
  document.addEventListener('input', function (e) {
    var f = e.target;
    if (!f.form || f.form.dataset.validated !== 'true' || f.type === 'radio') return;
    if (f.validity.customError) return; // los errores personalizados se recalculan al enviar
    VF.setFieldState(f, f.checkValidity());
  });
  document.addEventListener('change', function (e) {
    var f = e.target;
    if (!f.form || f.form.dataset.validated !== 'true' || f.type === 'radio') return;
    f.setCustomValidity('');
    VF.setFieldState(f, f.checkValidity());
  });
  VF.resetForm = function (form) {
    form.reset();
    delete form.dataset.validated;
    form.querySelectorAll('.is-invalid').forEach(function (f) { f.classList.remove('is-invalid'); f.removeAttribute('aria-invalid'); });
  };

  /* --------------------------- Descarga de archivos ---------------------- */
  VF.download = function (filename, content, mime) {
    var blob = new Blob(['\ufeff' + content], { type: mime || 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  };

  /* ------------------------ Comportamientos globales -------------------- */
  function initGlobal() {
    var body = document.body;

    // Aviso si Bootstrap no cargó (CDN sin conexión)
    if (!window.bootstrap) {
      var warn = document.createElement('div');
      warn.className = 'vf-alert vf-alert--warning m-3';
      warn.setAttribute('role', 'alert');
      warn.innerHTML = '<i class="bi bi-wifi-off" aria-hidden="true"></i><div><strong>No se pudo cargar Bootstrap.</strong>El prototipo usa Bootstrap desde un CDN y requiere conexión a Internet.</div>';
      body.prepend(warn);
    }

    // Navegación activa
    var section = body.dataset.section;
    document.querySelectorAll('[data-nav]').forEach(function (link) {
      if (link.dataset.nav === section) { link.classList.add('active'); link.setAttribute('aria-current', 'page'); }
    });

    // Sombra del encabezado al hacer scroll
    var header = document.querySelector('.site-header');
    if (header) {
      var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }

    // Delegación de acciones comunes (un único listener)
    document.addEventListener('click', function (e) {
      var printBtn = e.target.closest('[data-action="print"]');
      if (printBtn) { e.preventDefault(); window.print(); return; }

      var ni = e.target.closest('[data-not-implemented]');
      if (ni) { e.preventDefault(); VF.toast(ni.dataset.notImplemented || 'Función pendiente de integración con el backend.', 'info'); return; }

      var pw = e.target.closest('[data-toggle-password]');
      if (pw) {
        var input = document.getElementById(pw.dataset.togglePassword);
        if (!input) return;
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        pw.setAttribute('aria-pressed', String(show));
        pw.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
        pw.innerHTML = '<i class="bi ' + (show ? 'bi-eye-slash' : 'bi-eye') + '" aria-hidden="true"></i>';
      }
    });

    // Inicializador de la pantalla actual
    var page = body.dataset.page;
    if (page && typeof VF.pages[page] === 'function') {
      try { VF.pages[page](); } catch (err) { console.error('[VF] Error al iniciar la pantalla ' + page, err); }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initGlobal);
  else initGlobal();
})(window, document);
