document.addEventListener('DOMContentLoaded', () => {
    loadSensors();
    setInterval(loadSensors, 6000);
});

async function loadSensors() {
    try {
        const res = await fetch('/api/sensors');
        const data = await res.json();
        const tbody = document.getElementById('sensorsTableBody');
        tbody.innerHTML = '';

        data.sensors.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${s.id}</strong></td>
                <td>${s.mountain_name}</td>
                <td>${s.current_moisture !== null ? s.current_moisture + '%' : '--'}</td>
                <td>${s.current_rainfall !== null ? s.current_rainfall + ' mm' : '--'}</td>
                <td><span class="status-pill ${s.status === 'ONLINE' ? 'online' : 'offline'}">${s.status}</span></td>
                <td>${s.last_seen_label}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Sensor refresh error:", err);
    }
}