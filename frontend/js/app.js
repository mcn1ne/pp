// 메인 앱 로직

async function startAnalysis() {
    const urlInput = document.getElementById('channel-url');
    const url = urlInput.value.trim();

    if (!url) {
        showError('YouTube 채널 URL을 입력해주세요.');
        return;
    }

    // UI 상태 변경
    setLoading(true);
    hideError();
    hideResults();

    try {
        const filterOn = document.getElementById('supercent-filter').checked;
        const response = await fetch('/api/v1/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                days: 30,
                supercent_filter: filterOn,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '분석에 실패했습니다.');
        }

        const data = await response.json();
        renderDashboard(data);

    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

function renderDashboard(data) {
    // 기존 차트 제거
    destroyCharts();

    // 각 섹션 렌더링
    renderRecommendation(data);
    renderChannelInfo(data.channel);
    renderSupercentInfo(data);
    renderSentimentInfo(data.sentiment);
    renderScoreBars(data.score_breakdown, data.composite_score);

    // 차트 렌더링
    renderViewsChart(data.videos.videos);
    renderSentimentChart(data.sentiment);
    renderEngagementChart(data.videos.videos);
    renderScoresChart(data.score_breakdown);

    // 결과 표시
    showResults();
}

function setLoading(isLoading) {
    const btn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    const spinner = document.getElementById('btn-spinner');
    const loadingSection = document.getElementById('loading-section');

    btn.disabled = isLoading;
    if (isLoading) {
        btnText.textContent = '분석 중...';
        spinner.classList.remove('hidden');
        btn.classList.add('opacity-75', 'cursor-not-allowed');
        loadingSection.classList.remove('hidden');
    } else {
        btnText.textContent = '분석 시작';
        spinner.classList.add('hidden');
        btn.classList.remove('opacity-75', 'cursor-not-allowed');
        loadingSection.classList.add('hidden');
    }
}

function showError(message) {
    const el = document.getElementById('error-msg');
    el.textContent = message;
    el.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error-msg').classList.add('hidden');
}

function showResults() {
    document.getElementById('result-dashboard').classList.remove('hidden');
    document.getElementById('result-dashboard').classList.add('fade-in');
}

function hideResults() {
    document.getElementById('result-dashboard').classList.add('hidden');
}

// Enter 키로도 분석 시작
document.getElementById('channel-url').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') startAnalysis();
});
