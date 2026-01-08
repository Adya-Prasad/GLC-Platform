export const API_BASE = '/api/v1';

export async function apiCall(endpoint, options = {}) {
    const user = getCurrentUser();
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    if (user && user.token) {
        defaultHeaders['Authorization'] = `Bearer ${user.token}`;
    }

    // Add user_id to query params for authentication (hackathon approach)
    let url = `${API_BASE}${endpoint}`;
    if (user && user.id) {
        const separator = endpoint.includes('?') ? '&' : '?';
        url += `${separator}current_user_id=${user.id}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
    config.signal = controller.signal;

    try {
        const response = await fetch(url, config);
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please check your connection.');
        }
        console.error('API Call Error:', error);
        throw error;
    }
}

export function getCurrentUser() {
    const userStr = localStorage.getItem('glc_user');
    return userStr ? JSON.parse(userStr) : null;
}

export function formatCurrency(amount, currency = 'USD') {
    if (amount === undefined || amount === null) return '-';
    // Simple formatter for millions/thousands
    if (amount >= 1000000) {
        return `${currency} ${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
        return `${currency} ${(amount / 1000).toFixed(0)}k`;
    }
    return `${currency} ${amount}`;
}

export function getStatusClass(status) {
    const statusLower = (status || '').toLowerCase();
    switch (statusLower) {
        case 'approved': return 'bg-green-400 text-green-800';
        case 'rejected': return 'bg-red-300 text-red-700';
        case 'pending': return 'bg-gray-300 text-gray-700';
        case 'submitted': return 'bg-gray-300 text-gray-700';
        case 'under_review': return 'bg-yellow-400 text-purple-700';
        case 'verified': return 'bg-green-300 text-green-800';
        default: return 'bg-gray-100 text-gray-700';
    }
}

export function showModal(title, contentHtml) {
    const container = document.getElementById('modal-container');
    if (!container) return;

    container.innerHTML = `
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div class="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-200">
                <div class="p-6 border-b flex justify-between items-center">
                    <h3 class="text-xl font-bold text-gray-900">${title}</h3>
                    <button onclick="document.getElementById('modal-container').innerHTML=''" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                </div>
                <div class="flex-1 overflow-auto p-6">
                    ${contentHtml}
                </div>
            </div>
        </div>
    `;
}

export function downloadFile(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
