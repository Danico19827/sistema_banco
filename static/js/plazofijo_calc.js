(function() {
  var montoInput = document.getElementById('monto');
  var plazoInput = document.getElementById('plazo_dias');
  var preview = document.getElementById('preview-plazofijo');

  if (!montoInput || !plazoInput || !preview) return;

  function parseMonto(val) {
    return parseFloat(val.replace(/[^0-9.,]/g, '').replace(',', '.')) || 0;
  }

  function fmt(v) {
    var parts = v.toFixed(2).split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return '$ ' + parts.join(',');
  }

  function calcular() {
    var capital = parseMonto(montoInput.value);
    var dias = parseInt(plazoInput.value) || 0;
    var tasa = 0.08;

    if (capital < 100 || dias < 30 || dias > 365) {
      preview.innerHTML = '<div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:8px;padding:0.75rem 1rem;"><div style="font-size:0.75rem;color:#a0aec0;text-align:center;">Completá los datos para ver la previsualización</div></div>';
      return;
    }

    var interes = capital * tasa * dias / 365;
    var total = capital + interes;

    preview.innerHTML =
      '<div style="display:flex;gap:1rem;flex-wrap:wrap;">' +
        '<div style="background:#ebf8ff;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:120px;">' +
          '<div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Capital</div>' +
          '<div style="font-size:1rem;font-weight:700;color:#2b6cb0;">' + fmt(capital) + '</div>' +
        '</div>' +
        '<div style="background:#fefcbf;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:120px;">' +
          '<div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Intereses (' + dias + ' días)</div>' +
          '<div style="font-size:1rem;font-weight:700;color:#975a16;">' + fmt(interes) + '</div>' +
        '</div>' +
        '<div style="background:#e6fffa;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:120px;">' +
          '<div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Total al vencimiento</div>' +
          '<div style="font-size:1rem;font-weight:700;color:#276749;">' + fmt(total) + '</div>' +
        '</div>' +
      '</div>';
  }

  montoInput.addEventListener('input', calcular);
  plazoInput.addEventListener('input', calcular);
})();
