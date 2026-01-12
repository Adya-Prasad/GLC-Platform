import { apiCall } from './utils.js';

const DOC_PAGES = [
    { id: 'signup_page.md', label: 'Signup & Login' },
    { id: 'dashboard.md', label: 'Dashboard Guide' },
    { id: 'loan_application.md', label: 'Loan Applications' },
    { id: 'audit.md', label: 'ESG Reports' },
    { id: 'faq.md', label:'FAQs'}
];

let activeDoc = 'signup_page.md';

export async function renderDocs() {
    setTimeout(async () => {
        await loadDocContent(activeDoc);
    }, 100);

    return `
        <div class="flex bg-white rounded-2xl overflow-hidden h-[calc(100vh-120px)] border border-gray-200 shadow-sm">
            <!-- Internal Docs Sidebar -->
            <div class="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
                <div class="p-6 border-b border-gray-200 bg-white">
                    <h3 class="font-bold text-gray-800 text-sm tracking-wider uppercase flex items-center gap-2">
                        <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                        User Guide
                    </h3>
                </div>
                <nav class="flex-1 overflow-y-auto p-4 space-y-1">
                    ${DOC_PAGES.map(page => `
                        <button 
                            onclick="window.switchDoc('${page.id}')" 
                            id="doc-link-${page.id.replace('.md', '')}"
                            class="w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all flex items-center gap-3 ${activeDoc === page.id ? 'bg-white text-green-700 shadow-sm border border-gray-100 ring-1 ring-black/5' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900 icon-grayscale'}"
                        >
                            <span class="w-1.5 h-1.5 rounded-full ${activeDoc === page.id ? 'bg-green-500' : 'bg-gray-300'}"></span>
                            ${page.label}
                        </button>
                    `).join('')}
                </nav>
            </div>

            <!-- Docs Content area -->
            <div class="flex-1 overflow-y-auto relative bg-white custom-scrollbar">
                <div id="doc-loading" class="absolute inset-0 bg-white/90 backdrop-blur-sm flex items-center justify-center z-10 hidden">
                    <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-green-600"></div>
                </div>
                
                <div class="max-w-4xl mx-auto p-8 lg:p-12">
                    <div id="doc-render-area" class="prose prose-lg prose-green max-w-none">
                        <div class="animate-pulse space-y-6">
                            <div class="h-10 bg-gray-100 rounded w-1/3 mb-8"></div>
                            <div class="space-y-3">
                                <div class="h-4 bg-gray-100 rounded w-full"></div>
                                <div class="h-4 bg-gray-100 rounded w-5/6"></div>
                                <div class="h-4 bg-gray-100 rounded w-4/6"></div>
                            </div>
                        </div>
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
        const dot = btn?.querySelector('span');

        if (btn) {
            btn.className = `w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all flex items-center gap-3 text-gray-500 hover:bg-gray-100 hover:text-gray-900 icon-grayscale`;
            if (dot) dot.className = "w-1.5 h-1.5 rounded-full bg-gray-300";
        }
    });

    const activeBtn = document.getElementById(`doc-link-${docId.replace('.md', '')}`);
    if (activeBtn) {
        activeBtn.className = `w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all flex items-center gap-3 bg-white text-green-700 shadow-sm border border-gray-100 ring-1 ring-black/5`;
        const dot = activeBtn.querySelector('span');
        if (dot) dot.className = "w-1.5 h-1.5 rounded-full bg-green-500";
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
            renderArea.innerHTML = window.marked.parse(data.content || '');
            styleDocContent(renderArea);
        } else {
            renderArea.innerHTML = `<pre class="whitespace-pre-wrap font-mono">${data.content}</pre>`;
        }
    } catch (e) {
        console.error(e);
        renderArea.innerHTML = `
            <div class="bg-red-50 border border-red-100 rounded-xl p-6 text-center">
                <p class="text-red-600 font-medium">Error loading document</p>
                <p class="text-red-400 text-sm mt-2">${e.message}</p>
            </div>
        `;
    } finally {
        if (loader) loader.classList.add('hidden');
    }
}

function styleDocContent(container) {
    // Shared styling logic - kept consistent with learn.js

    // Headings
    container.querySelectorAll('h1').forEach(h => h.className = "text-4xl font-extrabold text-gray-900 mb-8 pb-4 border-b border-gray-100 tracking-tight");
    container.querySelectorAll('h2').forEach(h => h.className = "text-2xl font-bold text-gray-800 mt-12 mb-6 flex items-center gap-3");
    container.querySelectorAll('h3').forEach(h => h.className = "text-xl font-bold text-gray-800 mt-8 mb-4");

    // Text
    container.querySelectorAll('p').forEach(p => p.className = "text-gray-600 leading-8 mb-6 text-[17px]");

    // Lists
    container.querySelectorAll('ul').forEach(ul => ul.className = "list-disc pl-6 space-y-3 mb-8 text-gray-600 leading-7");
    container.querySelectorAll('ol').forEach(ol => ol.className = "list-decimal pl-6 space-y-3 mb-8 text-gray-600 leading-7");

    // Links
    container.querySelectorAll('a').forEach(a => a.className = "text-green-600 hover:text-green-700 font-medium underline decoration-green-200 hover:decoration-green-600 transition-all");

    // Code
    container.querySelectorAll('code').forEach(c => {
        if (!c.closest('pre')) {
            c.className = "bg-gray-100 text-green-700 px-1.5 py-0.5 rounded text-sm font-mono font-bold border border-gray-200";
        }
    });

    container.querySelectorAll('pre').forEach(p => p.className = "bg-gray-900 text-gray-100 p-5 rounded-xl overflow-x-auto mb-8 text-sm shadow-lg leading-relaxed");

    // Blockquotes
    container.querySelectorAll('blockquote').forEach(bq => bq.className = "border-l-4 border-green-500 bg-green-50 p-6 rounded-r-xl italic text-gray-700 mb-8 quote-icon");

    // Tables
    container.querySelectorAll('table').forEach(table => {
        table.className = "w-full border-collapse mb-8 bg-white rounded-xl overflow-hidden shadow-sm border border-gray-200 text-sm";
        table.querySelectorAll('thead').forEach(th => th.className = "bg-gray-50");
        table.querySelectorAll('th').forEach(th => th.className = "text-left p-4 font-bold text-gray-700 border-b border-gray-200 uppercase tracking-wider text-xs");
        table.querySelectorAll('td').forEach(td => td.className = "p-4 border-b border-gray-100 text-gray-600 align-top leading-6");
        table.querySelectorAll('tr:hover td').forEach(td => td.classList.add('bg-gray-50/50'));
    });

    // Images
    container.querySelectorAll('img').forEach(img => {
        img.className = "rounded-xl shadow-lg border border-gray-100 my-8 w-full";
        // Wrap in figure if caption needed
    });
}
