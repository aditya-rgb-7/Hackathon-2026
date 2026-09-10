document.addEventListener('DOMContentLoaded', () => {
    // Add Mountain
    document.getElementById('addMountainForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('admId').value,
            name: document.getElementById('admName').value,
            state: document.getElementById('admState').value,
            location: document.getElementById('admLocation').value,
            latitude: document.getElementById('admLat').value,
            longitude: document.getElementById('admLon').value,
            elevation: document.getElementById('admElevation').value,
            nearby_river: document.getElementById('admRiver').value,
            description: document.getElementById('admDesc').value
        };

        const res = await fetch('/api/admin/mountain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const msg = document.getElementById('adminStatusMsg');
        if (res.ok) {
            msg.innerHTML = '<span class="text-success">Sector created successfully!</span>';
            document.getElementById('addMountainForm').reset();
        } else {
            msg.innerHTML = '<span class="text-danger">Failed to register sector.</span>';
        }
    });

    // Simulate ESP32 Packet
    document.getElementById('simulatePacketForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            sensor_id: document.getElementById('simSensorId').value,
            mountain_id: document.getElementById('simMountainId').value,
            moisture: parseFloat(document.getElementById('simMoisture').value),
            rainfall: parseFloat(document.getElementById('simRain').value)
        };

        const res = await fetch('/api/sensor-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        document.getElementById('packetResult').textContent = JSON.stringify(result, null, 2);
    });
});