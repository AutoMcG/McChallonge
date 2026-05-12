(function () {
    const REFRESH_MS = 5000;
    const bannersContainer = document.getElementById('underway-banners');
    const generatedAt = document.getElementById('underway-generated-at');

    if (!bannersContainer || !generatedAt) {
        return;
    }

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value ?? '';
        return div.innerHTML;
    }

    function renderBanners(payload) {
        const banners = Array.isArray(payload?.banners) ? payload.banners : [];
        if (payload?.generated_at) {
            generatedAt.style.display = '';
            generatedAt.textContent = `Last generated: ${payload.generated_at}`;
        } else {
            generatedAt.style.display = 'none';
        }

        if (!banners.length) {
            bannersContainer.innerHTML = '<div class="alert alert-info">No underway matches right now.</div>';
            return;
        }

        bannersContainer.innerHTML = banners.map((banner) => {
            const title = escapeHtml(banner.title || 'Match');
            const tournament = escapeHtml(banner.tournament_name || 'Tournament');
            const url = escapeHtml(banner.url || '');
            return `
                <div class="banner-card">
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
                        <strong>${title}</strong>
                        <span class="meta">${tournament}</span>
                    </div>
                    <img src="${url}" alt="${title}">
                </div>
            `;
        }).join('');
    }

    async function refreshUnderway() {
        try {
            const response = await fetch('/api/underway', { cache: 'no-store' });
            if (!response.ok) return;
            const payload = await response.json();
            renderBanners(payload);
        } catch (error) {
            console.warn('Failed to refresh underway view:', error);
        }
    }

    window.setInterval(refreshUnderway, REFRESH_MS);
})();
