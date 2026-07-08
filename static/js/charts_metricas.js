document.addEventListener('DOMContentLoaded', function() {
    // ==========================================
    // GRAFICO 2: TORTA (GÉNEROS QUE PAGAN A TIEMPO)
    // ==========================================
    const ctxTorta = document.getElementById('chartTortaGeneros').getContext('2d');
    const datosGenero = JSON.parse(document.getElementById('data-genero').textContent);

    new Chart(ctxTorta, {
      type: 'pie',
      plugins: [ChartDataLabels],
      data: {
        labels: ['Femenino', 'Masculino', 'No especifica'],
        datasets: [{
          data: datosGenero, // Ahora toma los datos del DOM de forma segura
          backgroundColor: ['#319795', '#2b6cb0', '#a0aec0'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            position: 'bottom', 
            labels: { font: { family: 'sans-serif', size: 12 }, boxWidth: 15 } 
          },
          datalabels: {
            color: '#ffffff',
            font: { weight: 'bold', size: 14 },
            formatter: (value, context) => {
              const dataset = context.chart.data.datasets[0];
              const total = dataset.data.reduce((acc, current) => acc + current, 0);
              return ((value / total) * 100).toFixed(1) + '%';
            }
          }
        }
      }
    });

    // ==========================================
    // GRAFICO 3: ÁREAS APILADAS (NIVEL EDUCATIVO)
    // ==========================================
    const dataPrimario = JSON.parse(document.getElementById('data-primario').textContent);
    const dataSecundario = JSON.parse(document.getElementById('data-secundario').textContent);
    const dataSuperior = JSON.parse(document.getElementById('data-superior').textContent);

    const ctxAreas = document.getElementById('chartAreasEducacion').getContext('2d');

    const greenGradient = ctxAreas.createLinearGradient(0, 0, 0, 300);
    greenGradient.addColorStop(0, 'rgba(56, 178, 172, 0.4)'); 
    greenGradient.addColorStop(1, 'rgba(56, 178, 172, 0.0)'); 

    const blueGradient = ctxAreas.createLinearGradient(0, 0, 0, 300);
    blueGradient.addColorStop(0, 'rgba(66, 153, 225, 0.4)'); 
    blueGradient.addColorStop(1, 'rgba(66, 153, 225, 0.0)'); 

    const purpleGradient = ctxAreas.createLinearGradient(0, 0, 0, 300);
    purpleGradient.addColorStop(0, 'rgba(128, 90, 213, 0.4)'); 
    purpleGradient.addColorStop(1, 'rgba(128, 90, 213, 0.0)'); 

    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    new Chart(ctxAreas, {
      type: 'line',
      data: {
        labels: meses.slice(0, dataPrimario.length),
        datasets: [
          {
            label: 'Terciario/Universitario',
            data: dataSuperior,
            fill: true,
            backgroundColor: purpleGradient, 
            borderColor: '#805ad5', 
            borderWidth: 4,               
            tension: 0.35,                
            pointBackgroundColor: '#fff', 
            pointBorderColor: '#805ad5',
            pointBorderWidth: 2,
            pointRadius: 6,               
            pointHoverRadius: 8,
            pointHitRadius: 10,
          },
          {
            label: 'Secundario',
            data: dataSecundario,
            fill: true,
            backgroundColor: blueGradient,
            borderColor: '#3182ce',
            borderWidth: 4,
            tension: 0.35,
            pointBackgroundColor: '#fff',
            pointBorderColor: '#3182ce',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointHitRadius: 10,
          },
          {
            label: 'Primario',
            data: dataPrimario,
            fill: true,
            backgroundColor: greenGradient,
            borderColor: '#38b2ac',
            borderWidth: 4,
            tension: 0.35,
            pointBackgroundColor: '#fff',
            pointBorderColor: '#38b2ac',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointHitRadius: 10,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 10, bottom: 10, left: 5, right: 5 } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#718096', font: { size: 12 } } },
          y: { 
            stacked: false,     
            beginAtZero: true,  
            ticks: { precision: 0, color: '#718096', font: { size: 12, weight: '600' }, stepSize: 1 },
            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false } 
          }
        },
        plugins: {
          legend: { position: 'bottom', labels: { color: '#4a5568', font: { family: "'Inter', sans-serif", size: 13, weight: '500' }, boxWidth: 15, padding: 20 } },
          tooltip: { backgroundColor: 'rgba(26, 32, 44, 0.9)', titleColor: '#fff', bodyColor: '#fff', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, cornerRadius: 6, padding: 12, multiKeyBackground: 'rgba(0,0,0,0)', usePointStyle: true, titleFont: { size: 14, weight: '700' }, bodyFont: { size: 13 } }
        }
      }
    });

    // ==========================================
    // GRAFICO 4: SCORE CREDITICIO (MEDIDOR)
    // ==========================================
    const ctxScore = document.getElementById('chartScoreCrediticio').getContext('2d');
    const rawScore = JSON.parse(document.getElementById('data-promedio-score').textContent);
    
    let scoreActual = 0;
    const scoreMaximo = 500; 
    let scoreRestante = scoreMaximo; 
    let colorGrafico = '#e2e8f0'; 

    if (rawScore && rawScore !== null && rawScore !== '') {
      scoreActual = parseFloat(rawScore);
      if (scoreActual > scoreMaximo) scoreActual = scoreMaximo;
      scoreRestante = scoreMaximo - scoreActual;
      colorGrafico = '#48bb78'; 
    }

    new Chart(ctxScore, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [scoreActual, scoreRestante],
          backgroundColor: [colorGrafico, '#e2e8f0'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        circumference: 180, 
        rotation: -90,      
        cutout: '80%',      
        plugins: { legend: { display: false } }
      }
    });

    // ==========================================
    // GRAFICO 1: BURBUJAS EFECTO 3D ESFERA Y EJE Y DINÁMICO
    // ==========================================
    const datosCrudos = JSON.parse(document.getElementById('data-riesgo-burbujas').textContent);

    const datosPagoATiempo = datosCrudos.filter(d => d.riesgo === 'Pagó a Tiempo');
    const datosEnMora = datosCrudos.filter(d => d.riesgo === 'En Mora');

    const maxMonto = Math.max(...datosCrudos.map(d => d.r), 1000);
    const maxPrestamos = Math.max(...datosCrudos.map(d => d.y), 0);
    const topeEjeY = Math.max(10, maxPrestamos + 1); 

    const normalizarR = (monto) => (monto / maxMonto) * 25 + 8;

    const datasetRealPagoATiempo = datosPagoATiempo.map(d => ({ x: d.x, y: d.y, r: normalizarR(d.r), original_r: d.r }));
    const datasetRealEnMora = datosEnMora.map(d => ({ x: d.x, y: d.y, r: normalizarR(d.r), original_r: d.r }));

    const get3DBubbleColor = (context, colorBrillo, colorSombra) => {
        const chart = context.chart;
        const { ctx, chartArea } = chart;
        if (!chartArea) return colorSombra; 

        const element = context.element;
        if (!element || element.x === undefined || element.y === undefined) return colorSombra;

        const r = Math.max(1, element.options?.radius || context.raw?.r || 5);
        const offset = r * 0.35; 
        
        try {
            const gradient = ctx.createRadialGradient(element.x - offset, element.y - offset, 0, element.x, element.y, r);
            gradient.addColorStop(0, colorBrillo);
            gradient.addColorStop(1, colorSombra);
            return gradient;
        } catch (error) {
            return colorSombra;
        }
    };

    const ctxBurbuja = document.getElementById('chartBurbujaEdad').getContext('2d');
    new Chart(ctxBurbuja, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Pagó a Tiempo',
            data: datasetRealPagoATiempo,
            backgroundColor: (context) => get3DBubbleColor(context, '#6ee7b7', '#065f46'),
            borderColor: 'rgba(255, 255, 255, 0.4)',
            borderWidth: 1,
            hoverBorderWidth: 3,
            hoverBorderColor: '#ffffff'
          },
          {
            label: 'En Mora / Atrasado',
            data: datasetRealEnMora,
            backgroundColor: (context) => get3DBubbleColor(context, '#fca5a5', '#9f1239'),
            borderColor: 'rgba(255, 255, 255, 0.4)',
            borderWidth: 1,
            hoverBorderWidth: 3,
            hoverBorderColor: '#ffffff'
          }
        ]
      },
      options: {
          responsive: true,
          maintainAspectRatio: false,
          onResize: function(chart) {
              setTimeout(() => { chart.update('none'); }, 50);
          },
          layout: { padding: 15 },
          animation: { duration: 1500, easing: 'easeOutQuart' },
          scales: {
            x: { title: { display: true, text: 'Edad (Años)', font: { size: 12, weight: 'bold' } }, grid: { borderDash: [4, 4], drawBorder: false }, ticks: { precision: 0 }, min: 18, max: 85 },
            y: { title: { display: true, text: 'Cant. Créditos Solicitados', font: { size: 12, weight: 'bold' } }, grid: { borderDash: [4, 4], drawBorder: false }, ticks: { precision: 0, stepSize: 1 }, beginAtZero: true, max: topeEjeY }
          },
          plugins: {
            legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 10, padding: 20 } },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#ffffff', bodyColor: '#e2e8f0', padding: 15, cornerRadius: 8,
                callbacks: {
                  label: function(context) {
                    const item = context.raw;
                    const estado = context.dataset.label;
                    const montoFormateado = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(item.original_r);
                    return [ ` Edad: ${item.x} años`, ` Estado: ${estado}`, ` Cantidad: ${item.y} ${item.y === 1 ? 'préstamo' : 'préstamos'}`, ` Total pedido: ${montoFormateado}` ];
                  }
                }
            }
          }
      }
    });
});