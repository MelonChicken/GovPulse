HTML = """<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GovPulse — 정부 서비스 모니터링</title>
    <style>
        :root {
            --color-success: #10b981;
            --color-warning: #f59e0b;
            --color-error: #ef4444;
            --color-muted: #6b7280;
            --color-bg-success: #ecfdf5;
            --color-bg-warning: #fef3c7;
            --color-bg-error: #fee2e2;
            --color-bg-muted: #f9fafb;
            --color-text: #111827;
            --color-text-muted: #6b7280;
            --border-radius: 8px;
            --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background-color: #f8fafc;
            padding: 24px;
        }

        .header {
            max-width: 1200px;
            margin: 0 auto 32px;
            text-align: center;
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--color-text);
        }

        .header p {
            color: var(--color-text-muted);
            margin-bottom: 24px;
        }

        .controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }

        .btn-primary {
            background-color: var(--color-success);
            color: white;
        }

        .btn-primary:hover {
            background-color: #059669;
        }

        .btn-secondary {
            background-color: white;
            color: var(--color-text);
            border: 1px solid #d1d5db;
        }

        .btn-secondary:hover {
            background-color: #f9fafb;
        }

        .status-summary {
            max-width: 1200px;
            margin: 0 auto 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }

        .summary-card {
            background: white;
            padding: 20px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            text-align: center;
        }

        .summary-number {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .summary-label {
            color: var(--color-text-muted);
            font-size: 0.875rem;
        }

        .error-banner {
            max-width: 1200px;
            margin: 0 auto 24px;
            padding: 16px;
            background-color: var(--color-bg-error);
            border: 1px solid var(--color-error);
            border-radius: var(--border-radius);
            color: var(--color-error);
            display: none;
        }

        .error-banner.show {
            display: block;
        }

        .error-banner strong {
            display: block;
            margin-bottom: 4px;
        }

        .last-update {
            max-width: 1200px;
            margin: 0 auto 24px;
            text-align: center;
            color: var(--color-text-muted);
            font-size: 0.875rem;
        }

        .grid {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }

        .card {
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .card-title {
            font-weight: 600;
            font-size: 1.125rem;
            margin-bottom: 4px;
        }

        .badge {
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-healthy {
            background-color: var(--color-bg-success);
            color: var(--color-success);
        }

        .badge-unhealthy {
            background-color: var(--color-bg-error);
            color: var(--color-error);
        }


        .badge-error {
            background-color: var(--color-bg-error);
            color: var(--color-error);
        }

        .badge-warning {
            background-color: var(--color-bg-warning);
            color: var(--color-warning);
        }

        .url {
            color: var(--color-text-muted);
            font-size: 0.875rem;
            word-break: break-all;
            margin-bottom: 12px;
        }

        .status-details {
            font-size: 0.875rem;
            margin-bottom: 8px;
        }

        .status-details strong {
            color: var(--color-text);
        }

        .keyword-info {
            background-color: var(--color-bg-warning);
            border: 1px solid var(--color-warning);
            border-radius: var(--border-radius);
            padding: 12px;
            margin-top: 12px;
            font-size: 0.875rem;
        }

        .keyword-info strong {
            color: var(--color-warning);
            display: block;
            margin-bottom: 4px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: var(--color-text-muted);
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--color-text-muted);
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            body {
                padding: 16px;
            }

            .grid {
                grid-template-columns: 1fr;
            }

            .controls {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>GovPulse</h1>
        <p>정부 서비스 실시간 모니터링 — 키워드 기반 장애 감지</p>

        <div class="controls">
            <button id="refreshBtn" class="btn btn-primary">
                <span class="spinner" style="display: none;"></span>
                지금 새로고침
            </button>
            <button id="clearCacheBtn" class="btn btn-secondary">
                캐시 지우기
            </button>
        </div>
    </div>

    <div id="errorBanner" class="error-banner">
        <strong>실시간 데이터 로드 실패</strong>
        <span id="errorMessage"></span>
    </div>

    <div class="status-summary">
        <div class="summary-card">
            <div class="summary-number" id="healthyCount" style="color: var(--color-success);">-</div>
            <div class="summary-label">정상</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" id="unhealthyCount" style="color: var(--color-error);">-</div>
            <div class="summary-label">장애</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" id="errorCount" style="color: var(--color-muted);">-</div>
            <div class="summary-label">오류</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" id="totalCount" style="color: var(--color-text);">-</div>
            <div class="summary-label">전체</div>
        </div>
    </div>

    <div id="lastUpdate" class="last-update">
        마지막 업데이트: 로딩 중...
    </div>

    <div id="grid" class="grid">
        <div class="loading">
            <div class="spinner"></div>
            데이터를 불러오는 중...
        </div>
    </div>

    <script>
        // TypeScript-style utility functions
        class MonitoringDashboard {
            constructor() {
                this.API_ENDPOINT = '/api/status';
                this.RETRY_COUNT = 3;
                this.TIMEOUT_MS = 8000;
                this.AUTO_REFRESH_INTERVAL = 60000; // 60 seconds
                this.autoRefreshTimer = null;

                this.init();
            }

            init() {
                this.setupEventListeners();
                this.loadData();
                this.startAutoRefresh();
            }

            setupEventListeners() {
                document.getElementById('refreshBtn').addEventListener('click', () => {
                    this.loadData(true);
                });

                document.getElementById('clearCacheBtn').addEventListener('click', () => {
                    this.clearCache();
                });
            }

            async fetchWithTimeout(url, options = {}) {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.TIMEOUT_MS);

                try {
                    const response = await fetch(url, {
                        ...options,
                        signal: controller.signal,
                        cache: 'no-store'
                    });

                    clearTimeout(timeoutId);
                    return response;
                } catch (error) {
                    clearTimeout(timeoutId);
                    throw error;
                }
            }

            async retryFetch(url, maxRetries = this.RETRY_COUNT) {
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                    try {
                        const response = await this.fetchWithTimeout(url);

                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }

                        return await response.json();
                    } catch (error) {
                        console.warn(`Attempt ${attempt} failed:`, error.message);

                        if (attempt === maxRetries) {
                            throw error;
                        }

                        // Exponential backoff with jitter
                        const baseDelay = Math.pow(2, attempt) * 1000;
                        const jitter = Math.random() * 1000;
                        await this.sleep(baseDelay + jitter);
                    }
                }
            }

            sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }

            saveSnapshot(data) {
                try {
                    const snapshot = {
                        data: data,
                        timestamp: new Date().toISOString(),
                        version: '1.0'
                    };

                    localStorage.setItem('govpulse_snapshot', JSON.stringify(snapshot));
                    console.log('Snapshot saved to localStorage');
                } catch (error) {
                    console.warn('Failed to save snapshot:', error);
                }
            }

            loadSnapshot() {
                try {
                    const snapshot = localStorage.getItem('govpulse_snapshot');
                    if (snapshot) {
                        const parsed = JSON.parse(snapshot);
                        console.log('Loaded snapshot from:', parsed.timestamp);
                        return parsed;
                    }
                } catch (error) {
                    console.warn('Failed to load snapshot:', error);
                }
                return null;
            }

            clearCache() {
                try {
                    localStorage.removeItem('govpulse_snapshot');
                    this.hideErrorBanner();
                    this.loadData(true);
                } catch (error) {
                    console.warn('Failed to clear cache:', error);
                }
            }

            async loadData(forceRefresh = false) {
                this.showLoading();
                this.hideErrorBanner();

                try {
                    const data = await this.retryFetch(this.API_ENDPOINT);
                    this.saveSnapshot(data);
                    this.renderData(data);
                    console.log('Data loaded successfully');
                } catch (error) {
                    console.error('Failed to load live data:', error);
                    this.handleLoadError(error);
                }
            }

            handleLoadError(error) {
                const snapshot = this.loadSnapshot();

                if (snapshot) {
                    this.renderData(snapshot.data);
                    this.showErrorBanner(error, new Date(snapshot.timestamp));
                } else {
                    this.showErrorOnly(error);
                }
            }

            showErrorBanner(error, snapshotTime) {
                const banner = document.getElementById('errorBanner');
                const message = document.getElementById('errorMessage');

                const kstTime = new Date(snapshotTime).toLocaleString('ko-KR', {
                    timeZone: 'Asia/Seoul',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                message.textContent = `${error.message}. 마지막 스냅샷: ${kstTime} KST`;
                banner.classList.add('show');
            }

            hideErrorBanner() {
                document.getElementById('errorBanner').classList.remove('show');
            }

            showErrorOnly(error) {
                const grid = document.getElementById('grid');
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--color-error);">
                        <h3>데이터 로드 실패</h3>
                        <p style="margin-top: 8px; color: var(--color-text-muted);">${error.message}</p>
                        <button onclick="window.location.reload()" class="btn btn-primary" style="margin-top: 16px;">
                            페이지 새로고침
                        </button>
                    </div>
                `;
            }

            showLoading() {
                const refreshBtn = document.getElementById('refreshBtn');
                const spinner = refreshBtn.querySelector('.spinner');

                refreshBtn.disabled = true;
                spinner.style.display = 'inline-block';
            }

            hideLoading() {
                const refreshBtn = document.getElementById('refreshBtn');
                const spinner = refreshBtn.querySelector('.spinner');

                refreshBtn.disabled = false;
                spinner.style.display = 'none';
            }

            renderData(apiResponse) {
                this.hideLoading();

                const data = apiResponse.data || apiResponse; // Handle both new and legacy format
                const timestamp = apiResponse.timestamp || new Date().toISOString();

                this.updateSummary(apiResponse);
                this.updateTimestamp(timestamp);
                this.renderCards(data);
            }

            updateSummary(apiResponse) {
                // Handle both new and legacy API response formats
                if (apiResponse.healthy !== undefined) {
                    document.getElementById('healthyCount').textContent = apiResponse.healthy;
                    document.getElementById('unhealthyCount').textContent = apiResponse.unhealthy;
                    document.getElementById('errorCount').textContent = apiResponse.errors;
                    document.getElementById('totalCount').textContent = apiResponse.total_endpoints;
                } else {
                    // Legacy format - count manually
                    const data = apiResponse.data || apiResponse;
                    const healthy = data.filter(item => item.outcome === 'Healthy').length;
                    const unhealthy = data.filter(item => item.outcome === 'Unhealthy').length;
                    const errors = data.filter(item => item.outcome === 'Error').length;

                    document.getElementById('healthyCount').textContent = healthy;
                    document.getElementById('unhealthyCount').textContent = unhealthy;
                    document.getElementById('errorCount').textContent = errors;
                    document.getElementById('totalCount').textContent = data.length;
                }
            }

            updateTimestamp(timestamp) {
                const kstTime = new Date(timestamp).toLocaleString('ko-KR', {
                    timeZone: 'Asia/Seoul',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                document.getElementById('lastUpdate').textContent = `마지막 업데이트: ${kstTime} KST`;
            }

            renderCards(data) {
                const grid = document.getElementById('grid');
                grid.innerHTML = '';

                data.forEach(item => {
                    const card = this.createCard(item);
                    grid.appendChild(card);
                });
            }

            createCard(item) {
                const card = document.createElement('div');
                card.className = 'card';

                const { statusText, badgeClass } = this.getStatusInfo(item);
                const checkedTime = this.formatTimestamp(item.checked_at || item.ts);

                card.innerHTML = `
                    <div class="card-header">
                        <div>
                            <div class="card-title">${item.name || '-'}</div>
                            <div class="url">${item.url}</div>
                        </div>
                        <div class="badge ${badgeClass}">${statusText}</div>
                    </div>

                    <div class="status-details">
                        <div><strong>Status:</strong> ${this.getDetailedStatus(item)}</div>
                        <div><strong>Last checked:</strong> ${checkedTime}</div>
                        <div><strong>Last result:</strong> ${this.getLastResult(item)}</div>
                    </div>

                    ${this.getKeywordInfo(item)}
                    ${this.getErrorInfo(item)}
                `;

                return card;
            }

            getStatusInfo(item) {
                const outcome = (item.outcome || '').toLowerCase();

                switch (outcome) {
                    case 'healthy':
                        return { statusText: 'Healthy', badgeClass: 'badge-healthy' };
                    case 'unhealthy':
                        return { statusText: 'Unhealthy', badgeClass: 'badge-unhealthy' };
                    case 'disallowed':
                        return { statusText: '로봇 차단', badgeClass: 'badge-error' };
                    default:
                        return { statusText: 'Error', badgeClass: 'badge-error' };
                }
            }

            getDetailedStatus(item) {
                const outcome = (item.outcome || '').toLowerCase();

                if (outcome === 'unhealthy') {
                    const keywords = item.matched_keywords || '';
                    if (keywords.includes('CONTENT:') || keywords.includes('TITLE:')) {
                        const keywordMatch = keywords.split(';')[0];
                        const keywordText = keywordMatch.includes(':') ? keywordMatch.split(':')[1] : '';
                        return `Unhealthy (HTTP ${item.http}, keyword="${keywordText}")`;
                    }
                    return `Unhealthy (HTTP ${item.http})`;
                } else if (outcome === 'disallowed') {
                    return '로봇 차단 (robots.txt 정책)';
                } else if (outcome === 'error') {
                    return '오류 (네트워크 또는 서버 문제)';
                }

                return item.outcome || 'Unknown';
            }

            getLastResult(item) {
                const parts = [];

                parts.push(item.outcome || 'Unknown');

                if (item.http) {
                    parts.push(`HTTP ${item.http}`);
                }

                if (item.ttfb_ms >= 0) {
                    parts.push(`${item.ttfb_ms}ms`);
                }

                if (item.matched_keywords && item.matched_keywords !== '') {
                    const firstKeyword = item.matched_keywords.split(';')[0];
                    const keywordText = firstKeyword.includes(':') ? firstKeyword.split(':')[1] : firstKeyword;
                    parts.push(`matched="${keywordText}"`);
                }

                return parts.join(', ');
            }

            getKeywordInfo(item) {
                if (item.matched_keywords && item.matched_keywords !== '') {
                    const keywords = item.matched_keywords.split(';')
                        .map(k => k.includes(':') ? k.split(':')[1] : k)
                        .join(', ');

                    return `
                        <div class="keyword-info">
                            <strong>키워드 매칭:</strong>
                            ${keywords}
                        </div>
                    `;
                }
                return '';
            }

            getErrorInfo(item) {
                if (item.error) {
                    return `
                        <div style="margin-top: 12px; padding: 8px; background-color: var(--color-bg-error); border-radius: var(--border-radius); font-size: 0.875rem; color: var(--color-error);">
                            <strong>Error:</strong> ${item.error}
                        </div>
                    `;
                }
                return '';
            }

            formatTimestamp(timestamp) {
                if (!timestamp) return '-';

                try {
                    const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
                    return date.toLocaleString('ko-KR', {
                        timeZone: 'Asia/Seoul',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                } catch (error) {
                    return '-';
                }
            }

            startAutoRefresh() {
                if (this.autoRefreshTimer) {
                    clearInterval(this.autoRefreshTimer);
                }

                this.autoRefreshTimer = setInterval(() => {
                    this.loadData();
                }, this.AUTO_REFRESH_INTERVAL);
            }

            stopAutoRefresh() {
                if (this.autoRefreshTimer) {
                    clearInterval(this.autoRefreshTimer);
                    this.autoRefreshTimer = null;
                }
            }
        }

        // Initialize dashboard when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            window.dashboard = new MonitoringDashboard();
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (window.dashboard) {
                if (document.hidden) {
                    window.dashboard.stopAutoRefresh();
                } else {
                    window.dashboard.startAutoRefresh();
                    window.dashboard.loadData();
                }
            }
        });
    </script>
</body>
</html>
"""