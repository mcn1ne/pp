// Chart.js 인스턴스 관리
let chartInstances = {};

function destroyCharts() {
    Object.values(chartInstances).forEach(chart => chart.destroy());
    chartInstances = {};
}

function renderViewsChart(videos) {
    const ctx = document.getElementById('chart-views').getContext('2d');
    const labels = videos.map(v => v.title.substring(0, 15) + '...');
    const data = videos.map(v => v.view_count);

    chartInstances.views = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.reverse(),
            datasets: [{
                label: '조회수',
                data: data.reverse(),
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ctx.raw.toLocaleString() + '회'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: v => v >= 1000 ? (v/1000).toFixed(0) + 'K' : v }
                },
                x: {
                    ticks: { font: { size: 10 } }
                }
            }
        }
    });
}

function renderSentimentChart(sentiment) {
    const ctx = document.getElementById('chart-sentiment').getContext('2d');

    const pos = parseFloat((sentiment.positive_ratio * 100).toFixed(1));
    const neu = parseFloat((sentiment.neutral_ratio * 100).toFixed(1));
    const neg = parseFloat((sentiment.negative_ratio * 100).toFixed(1));

    // 데이터가 모두 0이면 "데이터 없음" 표시
    if (pos === 0 && neu === 0 && neg === 0) {
        chartInstances.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['데이터 없음'],
                datasets: [{ data: [1], backgroundColor: ['#e5e7eb'], borderWidth: 0 }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: { enabled: false }
                }
            }
        });
        return;
    }

    chartInstances.sentiment = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['긍정', '중립', '부정'],
            datasets: [{
                data: [pos, neu, neg],
                backgroundColor: ['#22c55e', '#9ca3af', '#ef4444'],
                borderWidth: 2,
                borderColor: '#fff',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 12 } } },
                tooltip: {
                    callbacks: { label: (ctx) => ctx.label + ': ' + ctx.raw + '%' }
                }
            }
        }
    });
}

function renderEngagementChart(videos) {
    const ctx = document.getElementById('chart-engagement').getContext('2d');
    const labels = videos.map(v => v.title.substring(0, 15) + '...');
    const data = videos.map(v => v.engagement_rate);

    chartInstances.engagement = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.reverse(),
            datasets: [{
                label: '참여율 (%)',
                data: data.reverse(),
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointBackgroundColor: '#8b5cf6',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => ctx.raw.toFixed(2) + '%' } }
            },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => v + '%' } },
                x: { ticks: { font: { size: 10 } } }
            }
        }
    });
}

function renderScoresChart(breakdown) {
    const ctx = document.getElementById('chart-scores').getContext('2d');
    chartInstances.scores = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['구독자', '참여도', '성장률', '감성', '일관성'],
            datasets: [{
                label: '점수',
                data: [
                    breakdown.subscriber_score,
                    breakdown.engagement_score,
                    breakdown.growth_score,
                    breakdown.sentiment_score,
                    breakdown.consistency_score,
                ],
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(59, 130, 246, 1)',
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { stepSize: 20, font: { size: 10 } },
                    pointLabels: { font: { size: 12 } }
                }
            }
        }
    });
}
