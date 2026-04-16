// DOM 렌더링 함수들

function renderSupercentInfo(data) {
    const scCount = data.supercent_video_count;
    const totalVideos = data.videos.videos.length;
    const commentCount = data.total_comments_analyzed;
    const filterActive = data.supercent_filter_active;
    const usedFallback = data.used_fallback;

    document.getElementById('sc-video-count').textContent = scCount + '개';
    document.getElementById('sc-total-videos').textContent = totalVideos;
    document.getElementById('sc-comment-count').textContent = commentCount.toLocaleString();

    const infoSection = document.getElementById('supercent-info');
    const warning = document.getElementById('sc-warning');

    if (!filterActive) {
        // 필터 OFF: 전체 영상 대상
        infoSection.className = 'rounded-xl shadow-sm border-2 border-gray-200 bg-gray-50 p-4 fade-in';
        warning.classList.remove('hidden');
        warning.textContent = '슈퍼센트 필터가 꺼져 있습니다. 전체 영상 기준으로 분석되었습니다.';
        warning.className = 'mt-3 p-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600 text-sm';
    } else if (scCount > 0) {
        // 필터 ON + 관련 영상 있음
        infoSection.className = 'rounded-xl shadow-sm border-2 border-indigo-200 bg-indigo-50 p-4 fade-in';
        warning.classList.add('hidden');
    } else {
        // 필터 ON + 관련 영상 없음 → 전체로 폴백
        infoSection.className = 'rounded-xl shadow-sm border-2 border-amber-200 bg-amber-50 p-4 fade-in';
        warning.classList.remove('hidden');
        warning.textContent = '슈퍼센트 게임 관련 영상을 찾지 못했습니다. 전체 영상 기준으로 댓글을 수집하여 분석했습니다.';
        warning.className = 'mt-3 p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm';
    }
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.getFullYear() + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + String(d.getDate()).padStart(2, '0');
}

function renderChannelInfo(channel) {
    document.getElementById('ch-thumbnail').src = channel.thumbnail_url;
    document.getElementById('ch-title').textContent = channel.title;
    document.getElementById('ch-custom-url').textContent = channel.custom_url || '';
    document.getElementById('ch-subscribers').textContent = formatNumber(channel.subscriber_count);
    document.getElementById('ch-views').textContent = formatNumber(channel.total_view_count);
    document.getElementById('ch-videos').textContent = formatNumber(channel.video_count);
    document.getElementById('ch-joined').textContent = formatDate(channel.published_at);
}

function renderSentimentInfo(sentiment) {
    document.getElementById('sent-positive').textContent = (sentiment.positive_ratio * 100).toFixed(1) + '%';
    document.getElementById('sent-neutral').textContent = (sentiment.neutral_ratio * 100).toFixed(1) + '%';
    document.getElementById('sent-negative').textContent = (sentiment.negative_ratio * 100).toFixed(1) + '%';
    document.getElementById('sent-overall').textContent = sentiment.overall_sentiment;
    document.getElementById('sent-count').textContent = sentiment.analyzed_count;

    // 테마 태그
    const themesContainer = document.getElementById('themes-container');
    themesContainer.innerHTML = '';
    sentiment.key_themes.forEach(theme => {
        const tag = document.createElement('span');
        tag.className = 'theme-tag inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium';
        tag.textContent = theme;
        themesContainer.appendChild(tag);
    });

    // 주목할 댓글 (감정별 색상 구분)
    const quotesList = document.getElementById('quotes-list');
    quotesList.innerHTML = '';

    const sentimentStyles = {
        positive: { border: 'border-green-400', bg: 'bg-green-50', badge: 'bg-green-500', label: '긍정' },
        negative: { border: 'border-red-400', bg: 'bg-red-50', badge: 'bg-red-500', label: '부정' },
        neutral:  { border: 'border-gray-400', bg: 'bg-gray-100', badge: 'bg-gray-500', label: '중립' },
    };

    (sentiment.notable_comments || []).forEach(comment => {
        const style = sentimentStyles[comment.sentiment] || sentimentStyles.neutral;
        const li = document.createElement('li');
        li.className = `p-3 ${style.bg} rounded-lg text-sm text-gray-700 border-l-4 ${style.border} flex items-start gap-2`;
        li.innerHTML = `
            <span class="${style.badge} text-white text-xs font-bold px-2 py-0.5 rounded-full whitespace-nowrap">${style.label}</span>
            <span>"${comment.text}"</span>
        `;
        quotesList.appendChild(li);
    });
}

function renderRecommendation(data) {
    const card = document.getElementById('recommendation-card');
    const badge = document.getElementById('rec-badge');
    const score = document.getElementById('rec-score');
    const summary = document.getElementById('rec-summary');
    const dateEl = document.getElementById('rec-date');

    score.textContent = data.composite_score.toFixed(1);
    summary.textContent = data.ai_summary;
    dateEl.textContent = '평가일: ' + formatDate(data.evaluated_at);

    // 추천 결과에 따른 스타일링
    badge.textContent = data.recommendation;
    if (data.recommendation === 'PASS') {
        card.className = 'rounded-xl shadow-sm border-2 border-green-300 bg-green-50 p-6 fade-in';
        badge.className = 'px-5 py-2 rounded-full text-lg font-bold bg-green-500 text-white';
    } else if (data.recommendation === 'REVIEW') {
        card.className = 'rounded-xl shadow-sm border-2 border-yellow-300 bg-yellow-50 p-6 fade-in';
        badge.className = 'px-5 py-2 rounded-full text-lg font-bold bg-yellow-500 text-white';
    } else {
        card.className = 'rounded-xl shadow-sm border-2 border-red-300 bg-red-50 p-6 fade-in';
        badge.className = 'px-5 py-2 rounded-full text-lg font-bold bg-red-500 text-white';
    }
}

function renderScoreBars(breakdown, composite) {
    const container = document.getElementById('score-bars');
    container.innerHTML = '';

    const items = [
        { label: '구독자 (20%)', score: breakdown.subscriber_score, color: 'bg-blue-500' },
        { label: '참여도 (25%)', score: breakdown.engagement_score, color: 'bg-purple-500' },
        { label: '성장률 (20%)', score: breakdown.growth_score, color: 'bg-green-500' },
        { label: '감성 (20%)', score: breakdown.sentiment_score, color: 'bg-yellow-500' },
        { label: '일관성 (15%)', score: breakdown.consistency_score, color: 'bg-orange-500' },
    ];

    items.forEach(item => {
        const row = document.createElement('div');
        row.innerHTML = `
            <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-600">${item.label}</span>
                <span class="font-semibold text-gray-800">${item.score.toFixed(1)}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="score-bar ${item.color} h-2.5 rounded-full" style="width: 0%"></div>
            </div>
        `;
        container.appendChild(row);

        // 애니메이션
        setTimeout(() => {
            row.querySelector('.score-bar').style.width = item.score + '%';
        }, 100);
    });

    // 종합 점수 원
    const circle = document.getElementById('composite-score-circle');
    const text = document.getElementById('composite-score-text');
    text.textContent = composite.toFixed(1);

    if (composite >= 60) {
        circle.className = 'w-28 h-28 rounded-full border-8 border-green-500 flex items-center justify-center mx-auto';
        text.className = 'text-3xl font-bold text-green-600';
    } else if (composite >= 45) {
        circle.className = 'w-28 h-28 rounded-full border-8 border-yellow-500 flex items-center justify-center mx-auto';
        text.className = 'text-3xl font-bold text-yellow-600';
    } else {
        circle.className = 'w-28 h-28 rounded-full border-8 border-red-500 flex items-center justify-center mx-auto';
        text.className = 'text-3xl font-bold text-red-600';
    }
}
