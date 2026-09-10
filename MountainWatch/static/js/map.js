document.addEventListener('DOMContentLoaded', async () => {
    // Center map over the Indian Himalayan Corridor
    const map = L.map('map').setView([30.5, 80.0], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    try {
        const res = await fetch('/api/mountains');
        const data = await res.json();

        data.mountains.forEach(m => {
            const riskLevel = m.risk ? m.risk.level : 'OFFLINE';
            let markerColor = '#6c757d';
            if (riskLevel === 'SAFE') markerColor = '#2ec4b6';
            else if (riskLevel === 'WATCH') markerColor = '#fcbf49';
            else if (riskLevel === 'WARNING') markerColor = '#f77f00';
            else if (riskLevel === 'CRITICAL') markerColor = '#d90429';

            const circle = L.circleMarker([m.latitude, m.longitude], {
                radius: 10,
                fillColor: markerColor,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }).addTo(map);

            const popupContent = `
                <div style="font-family:sans-serif; min-width: 190px; color:#111;">
                    <h4 style="margin:0 0 4px 0; font-size:1rem;">${m.name}</h4>
                    <p style="margin:0 0 6px 0; font-size:0.8rem; color:#555;">${m.state}</p>
                    <div style="font-size:0.85rem; line-height:1.4;">
                        <strong>Status:</strong> <span style="color:${markerColor}; font-weight:bold;">${riskLevel}</span><br>
                        <strong>Moisture:</strong> ${m.current_moisture !== null ? m.current_moisture + '%' : '--'}<br>
                        <strong>Sensor:</strong> ${m.sensor_status}<br>
                        <strong>Updated:</strong> ${m.last_seen_label}
                    </div>
                    <div style="margin-top:10px;">
                        <a href="/mountain/${m.id}" style="display:block; text-align:center; background:#3a86ff; color:#fff; padding:4px 8px; border-radius:4px; text-decoration:none; font-size:0.8rem; font-weight:bold;">View Mountain Profile</a>
                    </div>
                </div>
            `;
            circle.bindPopup(popupContent);
        });
    } catch (err) {
        console.error("Map rendering error:", err);
    }
});