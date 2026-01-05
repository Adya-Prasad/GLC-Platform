import { apiCall } from './utils.js';

const DOC_PAGES = [
    { id: 'signup_page.md', label: 'Signup' },
    { id: 'loan_application.md', label: 'Application' },
    { id: 'report.md', label: 'Report' },
    { id: 'dashboard.md', label: 'Dashboard' }
];

let activeDoc = 'loan_application.md';

export async function renderDocs() {
    setTimeout(async () => {
        await loadDocContent(activeDoc);
    }, 100);

    return `
        <div class="flex bg-white rounded-2xl p-2 overflow-hidden h-[calc(100vh-120px)]">
            <!-- Internal Docs Sidebar -->
            <div class="w-48 border-r border-gray-300 flex flex-col bg-gray-50/30">
                <div class="p-4 bg-white">
                    <h3 class="font-bold text-gray-700 text-sm italictracking-wider">Navigation</h3>
                </div>
                <nav class="flex-1 overflow-y-auto p-3 space-y-1">
                    ${DOC_PAGES.map(page => `
                        <button 
                            onclick="window.switchDoc('${page.id}')" 
                            id="doc-link-${page.id.replace('.md', '')}"
                            class="w-full text-left px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeDoc === page.id ? 'bg-green-50 text-green-700 shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'}"
                        >
                            ${page.label}
                        </button>
                    `).join('')}
                </nav>
            </div>

            <!-- Docs Content area -->
            <div class="flex-1 overflow-y-auto p-8 lg:p-12 relative bg-white">
                <div id="doc-loading" class="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10 hidden">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700"></div>
                </div>
                <div id="doc-render-area" class="prose prose-green max-w-none">
                    <div class="animate-pulse space-y-4">
                        <div class="h-8 bg-gray-100 rounded w-1/4"></div>
                        <div class="h-4 bg-gray-100 rounded w-3/4"></div>
                        <div class="h-4 bg-gray-100 rounded w-1/2"></div>
                        <div class="h-4 bg-gray-100 rounded w-full"></div>
                        <div class="h-4 bg-gray-100 rounded w-2/3"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

window.switchDoc = async function (docId) {
    activeDoc = docId;

    // Update active class in sidebar
    DOC_PAGES.forEach(p => {
        const btn = document.getElementById(`doc-link-${p.id.replace('.md', '')}`);
        if (btn) {
            btn.classList.remove('bg-green-50', 'text-green-700', 'shadow-sm');
            btn.classList.add('text-gray-500', 'hover:bg-gray-100', 'hover:text-gray-900');
        }
    });

    const activeBtn = document.getElementById(`doc-link-${docId.replace('.md', '')}`);
    if (activeBtn) {
        activeBtn.classList.add('bg-green-50', 'text-green-700', 'shadow-sm');
        activeBtn.classList.remove('text-gray-500', 'hover:bg-gray-100', 'hover:text-gray-900');
    }

    await loadDocContent(docId);
};

async function loadDocContent(filename) {
    const renderArea = document.getElementById('doc-render-area');
    const loader = document.getElementById('doc-loading');
    if (!renderArea) return;

    if (loader) loader.classList.remove('hidden');

    try {
        const data = await apiCall(`/docs/content/${filename}`);
        if (window.marked) {
            // Using marked.js which we added to index.html
            renderArea.innerHTML = window.marked.parse(data.content || '');

            // Basic styling for the rendered HTML since tailwind-typography might not be active
            styleDocContent(renderArea);
        } else {
            renderArea.innerHTML = `<pre class="whitespace-pre-wrap">${data.content}</pre>`;
        }
    } catch (e) {
        console.error(e);
        renderArea.innerHTML = `<p class="text-red-500">Error loading document: ${e.message}</p>`;
    } finally {
        if (loader) loader.classList.add('hidden');
    }
}

function styleDocContent(container) {
    // Manually add some basics if prose class isn't doing enough
    const headers = container.querySelectorAll('h1, h2, h3, h4');
    headers.forEach(h => {
        h.classList.add('font-bold', 'text-gray-900', 'mb-4', 'mt-8');
        if (h.tagName === 'H1') h.classList.add('text-3xl', 'mt-0');
        if (h.tagName === 'H2') h.classList.add('text-2xl', 'border-b', 'pb-2');
        if (h.tagName === 'H3') h.classList.add('text-xl');
    });

    const paras = container.querySelectorAll('p');
    paras.forEach(p => p.classList.add('text-gray-600', 'mb-4', 'leading-relaxed'));

    const lists = container.querySelectorAll('ul, ol');
    lists.forEach(l => l.classList.add('ml-6', 'mb-4', 'space-y-2', 'list-disc', 'text-gray-600'));

    const code = container.querySelectorAll('code');
    code.forEach(c => c.classList.add('bg-gray-100', 'px-1', 'rounded', 'text-sm', 'font-mono', 'text-green-700'));

    const pre = container.querySelectorAll('pre');
    pre.forEach(p => p.classList.add('bg-gray-900', 'text-gray-100', 'p-4', 'rounded-xl', 'overflow-x-auto', 'mb-6', 'text-sm'));
}
