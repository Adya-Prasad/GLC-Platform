 	Format
import { apiCall, formatCurrency, showModal, downloadFile, API_BASE } from './utils.js';

export async function renderDocuments() {
    let docs = [];
    try {
        docs = await apiCall('/borrower/all_documents');
    } catch (e) {
        console.error("Failed to fetch documents", e);
    }

    // Attach view/download handlers to window
    window.viewDoc = async (id, filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        const viewUrl = `${API_BASE}/borrower/document/${id}/view`;

        let content = '';
        if (ext === 'pdf') {
            content = `<iframe src="${viewUrl}" class="w-full h-[75vh] rounded-xl border-0 shadow-inner"></iframe>`;
        } else if (ext === 'json') {
            try {
                const res = await fetch(viewUrl);
                const data = await res.json();
                content = `<pre class="bg-gray-900 text-gray-100 p-6 rounded-xl overflow-auto max-h-[70vh] text-sm font-mono custom-scrollbar">${JSON.stringify(data, null, 2)}</pre>`;
            } catch (e) {
                content = `<p class="text-red-500">Error loading JSON: ${e.message}</p>`;
            }
        } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
            content = `<div class="flex justify-center bg-gray-50 rounded-xl p-4"><img src="${viewUrl}" class="max-w-full h-auto max-h-[75vh] rounded-lg shadow-md"></div>`;
        } else {
            content = `
                <div class="text-center py-16 bg-gray-50 rounded-2xl border border-gray-100">
                    <div class="w-20 h-20 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm">
                        <svg class="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 mb-2">Preview Not Available</h3>
                    <p class="text-gray-500 mb-8 max-w-sm mx-auto">This file specific format (.${ext}) cannot be previewed directly in the browser.</p>
                    <button onclick="window.downloadDoc(${id}, '${filename}')" class="px-8 py-3 bg-[var(--green)] text-white rounded-xl font-bold hover:shadow-lg hover:-translate-y-0.5 transition-all">
                        Download File
                    </button>
                </div>
            `;
        }
        showModal(filename, content);
    };

    window.downloadDoc = (id, filename) => {
        downloadFile(`${API_BASE}/borrower/document/${id}/download`, filename);
    };

    window.shareDoc = (id) => {
        // Mock share functionality
        const btn = document.getElementById(`share-btn-${id}`);
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
        btn.classList.add('bg-green-50');

        // Show toast or alert
        // alert("Link copied to clipboard!"); 

        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('bg-green-50');
        }, 2000);
    };

    return `
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-6 border-b border-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 class="text-xl font-bold text-gray-900">My Documents</h2>
                    <p class="text-sm text-gray-500 mt-1">Manage proof documents and reports</p>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                        Total: ${docs.length}
                    </span>
                </div>
            </div>

            ${docs.length === 0 ? `
                <div class="text-center py-20 bg-gray-50/30">
                    <div class="w-20 h-20 bg-white rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-gray-100">
                        <svg class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    </div>
                    <h3 class="text-lg font-bold text-gray-900">No documents yet</h3>
                    <p class="text-gray-500 mt-2 text-sm max-w-xs mx-auto">Documents uploaded during application submission will appear here.</p>
                </div>
            ` : `
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-gray-50/50">
                            <tr>
                                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Document Name</th>
                                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Format</th>
                                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Size</th>
                                <th class="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-50">
                            ${docs.map(doc => {
        const sizeKB = (doc.file_size / 1024).toFixed(0) + ' KB';
        const ext = doc.filename.split('.').pop().toUpperCase();

        // Determine icon color based on extension
        let iconColor = "text-gray-500 bg-gray-50";
        if (ext === 'PDF') iconColor = "text-red-500 bg-red-50";
        if (['DOC', 'DOCX'].includes(ext)) iconColor = "text-blue-500 bg-blue-50";
        if (['XLS', 'XLSX', 'CSV'].includes(ext)) iconColor = "text-green-500 bg-green-50";

        return `
                                    <tr class="group hover:bg-gray-50/50 transition-colors">
                                        <td class="px-6 py-4">
                                            <div class="flex items-center space-x-4">
                                                <div class="w-10 h-10 rounded-xl flex items-center justify-center ${iconColor} transition-transform group-hover:scale-110">
                                                    <span class="text-[10px] font-bold">${ext}</span>
                                                </div>
                                                <div>
                                                    <p class="font-bold text-gray-900 text-sm group-hover:text-[var(--green)] transition-colors">${doc.filename}</p>
                                                    <p class="text-xs text-gray-500 mt-0.5">${doc.doc_category || 'General'}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="px-6 py-4">
                                            <span class="text-xs font-mono font-large text-gray-500 bg-gray-100 px-2 py-1 rounded uppercase">${ext}</span>
                                        </td>
                                        <td class="px-6 py-4">
                                            <span class="text-sm font-medium text-gray-600">${sizeKB}</span>
                                        </td>
                                        <td class="px-6 py-4">
                                            <div class="flex items-center justify-center gap-2">
                                                <button onclick="window.viewDoc(${doc.id}, '${doc.filename}')" class="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all" title="Read / View">
                                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                                                </button>
                                                <button onclick="window.downloadDoc(${doc.id}, '${doc.filename}')" class="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all" title="Download">
                                                    <svg class="w-5 h-5" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"><path d="m3.25 13.25h9m-8.5-6.5 4 3.5 4-3.5m-4-5v8.5"/></svg>
                                                </button>
                                                <button id="share-btn-${doc.id}" onclick="window.shareDoc(${doc.id})" class="p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-all" title="Share (Copy Link)">
                                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                `;
    }).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;
}
