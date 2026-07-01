/**
 * filtros_admin.js
 * Motor de filtros cliente-side para las tablas del panel de admin.
 * No depende de ninguna librería externa.
 *
 * Uso:
 *   1. En el <tbody> de la tabla: id="tbody-XXX"
 *   2. En cada <tr> de datos: atributo data-filtrable + data-CAMPO="valor"
 *   3. En los controles de filtro: data-filtro="CAMPO" data-modo="contains|exact|range"
 *   4. Al final del template: inicializarFiltro({ barraId, tbodyId, contadorId })
 */
'use strict';

function inicializarFiltro(config) {
  const barra  = document.getElementById(config.barraId);
  const tbody  = document.getElementById(config.tbodyId);
  if (!barra || !tbody) return;

  const controles = barra.querySelectorAll('[data-filtro]');
  // Solo las filas que tienen data-filtrable (excluye la fila vacía del {% empty %})
  const filas  = Array.from(tbody.querySelectorAll('tr[data-filtrable]'));
  const total  = filas.length;
  const ctr    = document.getElementById(config.contadorId);

  function evaluar(tr) {
    return Array.from(controles).every(ctrl => {
      const campo = ctrl.dataset.filtro;
      const modo  = ctrl.dataset.modo || 'contains';
      const val   = ctrl.value.trim().toLowerCase();

      // Valor vacío o genérico ("todos / todas") → no filtra
      if (!val || val === 'todos' || val === 'todas') return true;

      const dato = (tr.dataset[campo] || '').toLowerCase();

      switch (modo) {
        case 'exact':
          return dato === val;

        case 'contains':
          return dato.includes(val);

        case 'range': {
          const n = parseInt(dato, 10);
          if (Number.isNaN(n)) return false;
          if (val === '0')   return n === 0;
          if (val === '1')   return n === 1;
          if (val === '2')   return n === 2;
          if (val === '1-2') return n >= 1 && n <= 2;
          if (val === '3+')  return n >= 3;
          return true;
        }

        default:
          return true;
      }
    });
  }

  function filtrar() {
    let visibles = 0;
    filas.forEach(tr => {
      const ok = evaluar(tr);
      tr.style.display = ok ? '' : 'none';
      if (ok) visibles++;
    });
    if (ctr) {
      ctr.textContent = total > 0
        ? `Mostrando ${visibles} de ${total}`
        : '';
    }
  }

  // Reaccionar a cambios en cualquier control
  controles.forEach(ctrl => {
    ctrl.addEventListener('input',  filtrar);
    ctrl.addEventListener('change', filtrar);
  });

  // Botón "Limpiar filtros" — se busca dentro de la barra por clase
  const btnLimpiar = barra.querySelector('.btn-limpiar');
  if (btnLimpiar) {
    btnLimpiar.addEventListener('click', () => {
      controles.forEach(ctrl => { ctrl.value = ''; });
      filtrar();
    });
  }

  // Inicializar contador al cargar la página
  filtrar();
}
