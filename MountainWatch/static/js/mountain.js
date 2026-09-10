document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch(`/api/mountains/${mountainId}`);
        if (!res.ok) throw new Error("Mountain not found");
        const data = await res.json();

        document.getElementById('mName').textContent = data.mountain.name;
        document.getElementById('mState').textContent = data.mountain.state;
        document.getElementById('mLocation').textContent = `${data.mountain.location} • Elevation: ${data.mountain.elevation}m`;
        document.getElementById('mElevation').textContent = `${data.mountain.elevation} meters ASL`;
        document.getElementById('mCoords').textContent = `${data.mountain.latitude.toFixed(4)}° N,${data.mountain.longitude.toFixed(4)}° E`;
        document.getElementById('mRiver').textContent = data.mountain.nearby_river || 'None identified';
        document.getElementById('mDesc').textContent = data.mountain.description;

        document.getElementById('mSensorId').textContent = data.mountain.sensor.id;
        document.getElementById('mSensorStatus').textContent = data.mountain.sensor.status;

        // Current
        document.getElementById('mMoisture').textContent = data.current.moisture + '%';
        document.getElementById('mRainfall').textContent = data.current.rainfall + ' mm';
        document.getElementById('m15Max').textContent = data.stats_15_days.max + '%';
        document.getElementById('mHistMax').textContent = data.stats_15_days.historical_max + '%';

        // Risk
        const riskBox = document.getElementById('mRiskBox');
        const riskLvl = document.getElementById('mRiskLevel');
        riskLvl.textContent = data.current.risk.level;
        riskLvl.style.color = data.current.risk.color;

        // Villages
        const vList = document.getElementById('villagesList');
        if (data.nearby_villages && data.nearby_villages.length > 0) {
            vList.innerHTML = '';
            data.nearby_villages.forEach(v => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><strong>${v.name}</strong></td><td>${v.distance_km} km</td><td>~${v.population || 'Unspecified'}</td>`;
                vList.appendChild(tr);
            });
        }

        // Safe Locations
        const sList = document.getElementById('safeLocsList');
        if (data.safe_locations && data.safe_locations.length > 0) {
            sList.innerHTML = '';
            data.safe_locations.forEach(s => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><strong>${s.name}</strong></td><td>${s.type}</td><td><a href="tel:${s.contact}">${s.contact || 'N/A'}</a></td>`;
                sList.appendChild(tr);
            });
        }

        // Safety Advisory Message
        const advText = document.getElementById('advisoryText');
        if (data.current.risk.level === 'CRITICAL') {
            advText.textContent = "CRITICAL HAZARD: Immediate slope destabilization hazard detected. Local SDRF outposts and designated shelters should initiate precautionary protocols.";
        } else if (data.current.risk.level === 'WARNING') {
            advText.textContent = "WARNING: Saturated subsurface soil. Precautionary monitoring in progress. Restrict pedestrian access along vulnerable drainage valleys.";
        }
    } catch (err) {
        console.error("Error loading mountain profile:", err);
    }
});