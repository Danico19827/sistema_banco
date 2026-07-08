(function() {
  var inputs = document.querySelectorAll('[data-currency]');
  if (!inputs.length) return;

  inputs.forEach(function(input) {
    var wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    var sign = document.createElement('span');
    sign.textContent = '$';
    sign.style.cssText = 'position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);font-weight:600;color:#4a5568;pointer-events:none;';
    wrapper.appendChild(sign);

    input.style.paddingLeft = '2rem';

    function formatValue(val) {
      var raw = val.replace(/[^\d,]/g, '').replace(',', '.');
      var parts = raw.split('.');
      if (parts.length > 2) parts = [parts[0], parts.slice(1).join('')];
      var integer = parts[0] ? parts[0].replace(/^0+/, '') || '0' : '0';
      var decimal = parts.length > 1 ? parts[1].slice(0, 2) : '';
      var formatted = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      if (decimal) formatted += ',' + decimal.padEnd(2, '0');
      return { formatted: formatted, raw: decimal ? integer + '.' + decimal : integer };
    }

    function updateInput() {
      var val = input.value;
      var clean = val.replace(/[^\d,]/g, '').replace(',', '.');
      var result = formatValue(clean);
      input.value = result.formatted ? result.formatted : '';
      input.dataset.raw = result.raw;
    }

    input.setAttribute('inputmode', 'decimal');
    input.setAttribute('placeholder', '0,00');
    input.removeAttribute('step');
    input.removeAttribute('min');

    input.addEventListener('input', updateInput);

    input.form.addEventListener('submit', function() {
      input.value = input.dataset.raw || input.value.replace(/[^0-9.,]/g, '').replace(',', '.');
    });
  });
})();
