let chartInstance = null;

async function fetchData(agent_id, user_id) {
    const summary = await fetch(`http://127.0.0.1:8000/summary/${agent_id}/${user_id}`).then(r=>r.json());
    const logs = await fetch(`http://127.0.0.1:8000/logs/${agent_id}/${user_id}`).then(r=>r.json());
    return { summary, logs };
}

function renderChart(summary) {
    const ctx = document.getElementById('chart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const colors = {
        stressed: 'rgba(255, 75, 92, 0.6)',
        positive: 'rgba(76, 175, 80, 0.6)',
        uncertain: 'rgba(255, 152, 0, 0.6)',
        neutral: 'rgba(96, 125, 139, 0.6)'
    };

    const labels = Object.keys(summary);
    const data = Object.values(summary);
    const backgroundColors = labels.map(l => colors[l] || 'rgba(200,200,200,0.6)');

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Signal Frequency',
                data,
                backgroundColor: backgroundColors,
                borderRadius: 12
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
            animation: { duration: 1500, easing: 'easeOutElastic' }
        }
    });
}

function renderLogs(logs) {
    const tbody = document.querySelector("#logs-table tbody");
    tbody.innerHTML = "";

    if (logs.length === 0) {
        document.getElementById('status-message').innerText = "No logs yet for this user.";
        return;
    } else {
        document.getElementById('status-message').innerText = "";
    }

    logs.forEach((log, index) => {
        const tr = document.createElement("tr");
        const signalClass = `signal-${log.detected_signal}`;
        const signalEmoji = {
            stressed: "⚠️",
            positive: "😊",
            uncertain: "🤔",
            neutral: "💬"
        }[log.detected_signal] || "💬";

        tr.innerHTML = `
            <td>${log.timestamp}</td>
            <td>${log.user_input}</td>
            <td class="${signalClass}">${signalEmoji} ${log.detected_signal.toUpperCase()}</td>
        `;
        tr.style.animation = `fadeIn 0.5s ease ${index * 0.1}s forwards`;
        tbody.appendChild(tr);
    });
}

async function refreshDashboard() {
    const agentId = document.getElementById("agentId").value;
    const userId = document.getElementById("userId").value;
    const { summary, logs } = await fetchData(agentId, userId);
    renderChart(summary);
    renderLogs(logs);
}

refreshDashboard();
