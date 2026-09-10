document.addEventListener('DOMContentLoaded', async () => {
    // Populate mountains dropdown
    try {
        const res = await fetch('/api/mountains');
        const data = await res.json();
        const sel = document.getElementById('empMountain');
        data.mountains.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = `${m.name} (${m.state})`;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error(e);
    }

    // Submit handler
    document.getElementById('emergencyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btnSubmitEmergency');
        const statusMsg = document.getElementById('emergencyStatusMsg');
        btn.disabled = true;
        btn.textContent = "Transmitting to Control Center...";

        const payload = {
            mountain_id: document.getElementById('empMountain').value,
            emergency_type: document.getElementById('empType').value,
            location: document.getElementById('empLocation').value,
            people_affected: parseInt(document.getElementById('empAffected').value, 10),
            contact_phone: document.getElementById('empPhone').value,
            description: document.getElementById('empDesc').value
        };

        try {
            const res = await fetch('/api/emergency', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();
            if (res.ok) {
                statusMsg.style.display = 'block';
                statusMsg.className = 'alert alert-danger';
                statusMsg.innerHTML = `<strong>DISPATCH SENT!</strong> Report #${result.report_id} received by Emergency Control. Response units notified.`;
                document.getElementById('emergencyForm').reset();
            } else {
                alert("Error submitting emergency report: " + result.error);
            }
        } catch (err) {
            alert("Network error transmitting emergency dispatch.");
        } finally {
            btn.disabled = false;
            btn.textContent = "SEND EMERGENCY DISPATCH";
        }
    });
});