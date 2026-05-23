document.addEventListener("DOMContentLoaded", function() {
  // Configuración del Gráfico de Flujo de Caja
  const canvasFlujo = document.getElementById('chartFlujo');
  if (canvasFlujo) {
    const ctxFlujo = canvasFlujo.getContext('2d');
    new Chart(ctxFlujo, {
      type: 'line',
      data: {
        labels: ['Jan', 'Mar', 'Mar', 'Abr', 'May', 'Jun'],
        datasets: [{
          data: [1000, 1500, 1200, 2100, 1800, 2400],
          borderColor: '#38bdf8',
          tension: 0.4,
          borderWidth: 3,
          pointRadius: 0
        }]
      },
      options: { 
        responsive: true, 
        plugins: { legend: { display: false } } 
      }
    });
  }

  // Configuración del Gráfico de Patrones de Gasto
  const canvasGastos = document.getElementById('chartGastos');
  if (canvasGastos) {
    const ctxGastos = canvasGastos.getContext('2d');
    new Chart(ctxGastos, {
      type: 'bar',
      data: {
        labels: ['Abo', 'Gas', 'Bas', 'Otr', 'Nov', 'Dec'],
        datasets: [
          { data: [1200, 900, 1600, 1100, 1900, 1400], backgroundColor: '#0f172a' },
          { data: [600, 400, 800, 500, 1000, 700], backgroundColor: '#38bdf8' }
        ]
      },
      options: { 
        responsive: true, 
        plugins: { legend: { display: false } }, 
        scales: { y: { stacked: true }, x: { stacked: true } } 
      }
    });
  }
});