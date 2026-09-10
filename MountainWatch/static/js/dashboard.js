let moistureChartInstance = null;
let currentMountainId = null;
let pollTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initMountainSelector();
    document.getElementById('mountainSelect').addEventListener('change', (e) => {
        currentMountainId = e.target.value;
        loadMountainDashboard(currentMountainId);
    });
    document.getElementById('refreshBtn').addEventListener('click', () => {
        if (currentMountainId) loadMountainDashboard(currentMountainId);
    });

    // Real-time polling every 5000ms
    pollTimer = setInterval(() => {
        if (currentMountainId) {
            loadMountainDashboard(currentMountainId, true);
        }
    }, 5000);
});

async function initMountainSelector() {
    try {
        const res = await fetch('/api/mountains');
        const data = await res.json();
        const sel = document.getElementById('mountainSelect');
        sel.innerHTML = '';

        if (!data.mountains || data.mountains.length === 0) {
            sel.innerHTML = '<option value="">No monitored mountains available</option>';
            return;
        }

        data.mountains.forEach((m, idx) => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = `${m.name} (${m.state})`;
            sel.appendChild(opt);
        });

        // Set default to first mountain
        currentMountainId = data.mountains[0].id;
        loadMountainDashboard(currentMountainId);
    } catch (err) {
        console.error("Failed to populate mountains:", err);
    }
}

async function loadMountainDashboard(mId, isBackground = false) {
    try {
        const res = await fetch(`/api/mountains/${mId}`);
        if (!res.ok) throw new Error("Mountain not found");
        const data = await res.json();

        // 1. Update Core Metric Cards
        const isOnline = data.mountain.sensor.status === 'ONLINE';
        const sensorBadge = document.getElementById('sensorStatusBadge');
        sensorBadge.textContent = data.mountain.sensor.status;
        sensorBadge.className = 'sensor-badge ' + (isOnline ? 'text-success' : 'text-danger');

        document.getElementById('sensorIdLabel').textContent = data.mountain.sensor.id || 'None';
        document.getElementById('lastUpdateLabel').textContent = data.mountain.sensor.last_seen_label || 'Offline';

        // Moisture
        document.getElementById('valMoisture').textContent = isOnline ? data.current.moisture.toFixed(1) : '--';

        // Moisture Rate
        const rateVal = isOnline ? (data.current.rate_per_hour > 0 ? `+${data.current.rate_per_hour}` : data.current.rate_per_hour) : '--';
        document.getElementById('valRate').textContent = rateVal;
        document.getElementById('trendLabel').textContent = isOnline ? data.current.trend : 'Sensor Inactive';

        const trendIcon = document.getElementById('trendIcon');
        if (!isOnline) trendIcon.textContent = '❌';
        else if (data.current.trend === 'Rapidly Increasing') trendIcon.textContent = '⇈';
        else if (data.current.trend === 'Increasing') trendIcon.textContent = '↑';
        else if (data.current.trend === 'Decreasing') trendIcon.textContent = '↓';
        else trendIcon.textContent = '↔';

        // Rainfall
        document.getElementById('valRainfall').textContent = isOnline ? data.current.rainfall.toFixed(1) : '--';
        const rainStatus = document.getElementById('rainStatus');
        if (data.current.rainfall > 25) {
            rainStatus.textContent = 'HEAVY';
            rainStatus.className = 'rain-status text-danger';
        } else if (data.current.rainfall > 10) {
            rainStatus.textContent = 'MODERATE';
            rainStatus.className = 'rain-status text-warning';
        } else {
            rainStatus.textContent = 'LOW / NONE';
            rainStatus.className = 'rain-status text-success';
        }

        // Hazard State Card
        const riskCard = document.getElementById('riskCard');
        const riskLevelEl = document.getElementById('valRiskLevel');
        const riskMsgEl = document.getElementById('riskMessage');
        const offlineBanner = document.getElementById('offlineAlertBanner');

        riskLevelEl.textContent = data.current.risk.level;
        riskLevelEl.style.color = data.current.risk.color;
        riskCard.style.borderLeftColor = data.current.risk.color;
        riskMsgEl.textContent = data.current.risk.message;

        if (!isOnline) {
            offlineBanner.style.display = 'block';
        } else {
            offlineBanner.style.display = 'none';
        }

        // 2. Update Stats Table
        document.getElementById('statMax').textContent = data.stats_15_days.max + '%';
        document.getElementById('statMaxTime').textContent = data.stats_15_days.max_timestamp;
        document.getElementById('statMin').textContent = data.stats_15_days.min + '%';
        document.getElementById('statMinTime').textContent = data.stats_15_days.min_timestamp;
        document.getElementById('statAvg').textContent = data.stats_15_days.average + '%';
        document.getElementById('statHistoricalMax').textContent = data.stats_15_days.historical_max + '%';

        // Link
        document.getElementById('lnkDetail').href = `/mountain/${data.mountain.id}`;

        // 3. Update Chart
        renderChart(data.history_graph);

    } catch (err) {
        console.error("Dashboard refresh error:", err);
    }
}

function renderChart(series) {
    const ctx = document.getElementById('moistureChart').getContext('2d');

    const labels = series.map(pt => {
        const d = new Date(pt.timestamp);
        return `${d.getMonth() + 1}/${d.getDate()}${d.getHours()}:00`;
    });
    const values = series.map(pt => pt.moisture);

    if (moistureChartInstance) {
        moistureChartInstance.data.labels = labels;
        moistureChartInstance.data.datasets[0].data = values;
        moistureChartInstance.update();
        return;
    }

    moistureChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Moisture Saturation (%)',
                data: values,
                borderColor: '#3a86ff',
                backgroundColor: 'rgba(58, 134, 255, 0.1)',
                fill: true,
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: '#2c3968' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', maxTicksLimit: 8 }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8f9fa' } }
            }
        }
    });
}