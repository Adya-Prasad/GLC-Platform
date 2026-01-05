import { apiCall, formatCurrency, showModal, downloadFile, API_BASE } from './utils.js';

export async function renderDocuments() {
    let docs = [];
    try {
        docs = await apiCall('/borrower/all_documents');
    } catch (e) {
        console.error("Failed to fetch documents", e);
    }

    // Attach global helpers to window if not already there
    window.viewDoc = async (id, filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        const viewUrl = `${API_BASE}/borrower/document/${id}/view`;

        let content = '';
        if (ext === 'pdf') {
            content = `<iframe src="${viewUrl}" class="w-full h-[70vh] rounded-lg border-0"></iframe>`;
        } else if (ext === 'json') {
            try {
                const res = await fetch(viewUrl);
                const data = await res.json();
                content = `<pre class="bg-gray-50 p-4 rounded-lg overflow-auto max-h-[70vh] text-sm text-gray-700 font-mono">${JSON.stringify(data, null, 2)}</pre>`;
            } catch (e) {
                content = `<p class="text-red-500">Error loading JSON: ${e.message}</p>`;
            }
        } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
            content = `<img src="${viewUrl}" class="max-w-full h-auto rounded-lg mx-auto shadow-sm">`;
        } else {
            content = `
                <div class="text-center py-12">
                    <div class="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    </div>
                    <p class="text-gray-600 mb-6">Preview for .${ext} files is not supported yet.</p>
                    <button onclick="window.downloadDoc(${id}, '${filename}')" class="px-6 py-2 bg-[var(--green)] text-white rounded-xl font-bold hover:opacity-90 transition-opacity">
                        Download to View
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
        alert("Sharing link copied to clipboard (Mock)");
    };

    return `
        <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h2 class="text-xl font-bold text-gray-900">Document Center</h2>
                </div>
                <div class="flex items-center space-x-2">
                     <button class="bg-gray-50 text-gray-600 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-gray-100 transition-colors border border-gray-100">
                        Sorted by Date
                     </button>
                </div>
            </div>

            ${docs.length === 0 ? `
                <div class="text-center py-16 bg-gray-50/50 rounded-2xl border-2 border-dashed border-gray-100">
                    <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                        <svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    </div>
                    <h3 class="text-gray-900 font-bold">No documents found</h3>
                    <p class="text-gray-500 text-sm mt-1">Uploaded documents from your applications will appear here.</p>
                </div>
            ` : `
                <div class="space-y-3">
                    ${docs.map(doc => {
        const date = new Date(doc.uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const sizeKB = (doc.file_size / 1024).toFixed(0);
        return `
                            <div class="flex items-center justify-between p-4 border border-gray-50 rounded-2xl hover:bg-gray-50 hover:border-green-100 transition-all group">
                                <div class="flex items-center space-x-4">
                                    <div class="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center text-green-600 group-hover:bg-green-100 transition-colors">
                                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                                        </svg>
                                    </div>
                                    <div>
                                        <p class="font-bold text-gray-900 group-hover:text-[var(--green)] transition-colors">${doc.filename}</p>
                                        <p class="text-xs text-gray-500 font-medium uppercase tracking-wider">${doc.file_type || 'Unknown'} • ${sizeKB} KB • ${date}</p>
                                    </div>
                                </div>
                                <div class="flex space-x-1 opacity-60 group-hover:opacity-100 transition-opacity">
                                    <button onclick="window.viewDoc(${doc.id}, '${doc.filename}')" class="p-2.5 text-gray-400 hover:text-blue-600 rounded-xl hover:bg-blue-50 transition-all title="View">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                                    </button>
                                    <button onclick="window.shareDoc(${doc.id})" class="p-2.5 text-gray-400 hover:text-purple-600 rounded-xl hover:bg-purple-50 transition-all" title="Share">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>
                                    </button>
                                    <button onclick="window.downloadDoc(${doc.id}, '${doc.filename}')" class="p-2.5 text-gray-400 hover:text-green-600 rounded-xl hover:bg-green-50 transition-all" title="Download">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                                    </button>
                                </div>
                            </div>
                        `;
    }).join('')}
                </div>
            `}
        </div>
    `;
}
