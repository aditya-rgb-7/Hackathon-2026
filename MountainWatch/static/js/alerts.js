let allAlerts = [];

document.addEventListener('DOMContentLoaded', async () => {
    const res = await fetch('/api/alerts');
    const data = await res.json();
    allAlerts = data.alerts;
    renderFilteredAlerts();
});

function renderFilteredAlerts() {
    const filter = document.getElementById('riskFilter').value;
    const stream = document.getElementById('alertsStream');
    stream.innerHTML = '';

    const list = allAlerts.filter(a => filter === 'ALL' || a.risk_level === filter);

    if (list.length === 0) {
        stream.innerHTML = '<p class="text-center">No alerts match the selected criteria.</p>';
        return;
    }

    list.forEach(a => {
        const div = document.createElement('div');
        div.className = 'metric-card';
        div.style.marginBottom = '14px';
        div.style.borderLeft = `6px solid ${a.risk_level === 'CRITICAL' ? '#d90429' : '#f77f00'}`;
        div.innerHTML = `
            <div class="metric-head">
                <span>SECTOR: ${a.mountain_name} (${a.state})</span>
                <span class="risk-badge" style="background:${a.risk_level === 'CRITICAL' ? '#d90429' : '#f77f00'}">${a.risk_level}</span>
            </div>
            <div style="margin: 10px 0;">
                <h3 style="margin-bottom:4px;">${a.message}</h3>
                <p class="text-muted" style="font-size:0.85rem;">Recorded Saturation: <strong>${a.moisture}\%</strong> \vert{} Rainfall: <strong>${a.rainfall} mm</strong></p>
            </div>
            <div class="metric-foot">
                <span>Timestamp: ${a.timestamp}</span>
                <span>Status: <strong>${a.status}</strong></span>
            </div>
        `;
        stream.appendChild(div);
    });
}