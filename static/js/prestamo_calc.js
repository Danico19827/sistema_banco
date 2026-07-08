(function() {
  var montoInput = document.getElementById('monto');
  var plazoInput = document.getElementById('plazo');
  var sistemaSelect = document.getElementById('sistema');
  var preview = document.getElementById('preview-tabla');

  if (!montoInput || !plazoInput || !sistemaSelect || !preview) return;

  function parseMonto(val) {
    return parseFloat(val.replace(/[^0-9.,]/g, '').replace(',', '.')) || 0;
  }

  function calcular() {
    var P = parseMonto(montoInput.value);
    var n = parseInt(plazoInput.value) || 0;
    var sistema = sistemaSelect.value;
    var r = 0.05 / 12;

    if (P < 1000 || P > 1000000 || n < 3 || n > 60) {
      preview.innerHTML = '<p style="color:#a0aec0;text-align:center;padding:1rem;">Completá los datos para ver la previsualización</p>';
      return;
    }

    var cuotas = [];
    if (sistema === 'frances') {
      var cuotaFija = P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
      var saldo = P;
      for (var i = 1; i <= n; i++) {
        var interes = saldo * r;
        var amortizacion = cuotaFija - interes;
        saldo -= amortizacion;
        if (i === n) saldo = 0;
        cuotas.push({ n: i, monto: cuotaFija, interes: interes, amort: amortizacion, saldo: Math.max(saldo, 0) });
      }
    } else {
      var amortFija = P / n;
      var saldo = P;
      for (var i = 1; i <= n; i++) {
        var interes = saldo * r;
        saldo -= amortFija;
        if (i === n) saldo = 0;
        cuotas.push({ n: i, monto: amortFija + interes, interes: interes, amort: amortFija, saldo: Math.max(saldo, 0) });
      }
    }

    var totalIntereses = cuotas.reduce(function(s, c) { return s + c.interes; }, 0);
    var totalPagar = P + totalIntereses;

    var fmt = function(v) {
      var parts = v.toFixed(2).split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      return '$ ' + parts.join(',');
    };

    var html = '';
    html += '<div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">';
    html += '<div style="background:#ebf8ff;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:140px;"><div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Cuota mensual</div><div style="font-size:1.1rem;font-weight:700;color:#2b6cb0;">' + fmt(cuotas[0].monto) + '</div></div>';
    html += '<div style="background:#fefcbf;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:140px;"><div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Total intereses</div><div style="font-size:1.1rem;font-weight:700;color:#975a16;">' + fmt(totalIntereses) + '</div></div>';
    html += '<div style="background:#e6fffa;padding:0.75rem 1rem;border-radius:8px;flex:1;min-width:140px;"><div style="font-size:0.7rem;color:#718096;text-transform:uppercase;">Total a pagar</div><div style="font-size:1.1rem;font-weight:700;color:#276749;">' + fmt(totalPagar) + '</div></div>';
    html += '</div>';

    html += '<div class="table-container" style="max-height:300px;overflow-y:auto;">';
    html += '<table class="transactions-table"><thead><tr><th>Cuota</th><th style="text-align:right;">Monto</th><th style="text-align:right;">Interés</th><th style="text-align:right;">Amort.</th><th style="text-align:right;">Saldo</th></tr></thead><tbody>';
    for (var i = 0; i < cuotas.length; i++) {
      var c = cuotas[i];
      html += '<tr><td>' + c.n + '</td><td class="amount">' + fmt(c.monto) + '</td><td class="amount amount-negative">' + fmt(c.interes) + '</td><td class="amount amount-positive">' + fmt(c.amort) + '</td><td class="amount">' + fmt(c.saldo) + '</td></tr>';
    }
    html += '</tbody></table></div>';
    preview.innerHTML = html;
  }

  montoInput.addEventListener('input', calcular);
  plazoInput.addEventListener('input', calcular);
  sistemaSelect.addEventListener('change', calcular);
})();
