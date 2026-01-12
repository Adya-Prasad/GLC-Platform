/**
 * Document Viewer Modal Logic
 * Handles opening documents (PDF, DOCX, JSON) in a glassmorphism popup.
 */

export function setupDocumentViewer() {
    // Create Modal HTML if it doesn't exist
    if (!document.getElementById('doc-viewer-modal')) {
        const modalHtml = `
        <div id="doc-viewer-modal" class="fixed inset-0 z-[60] hidden flex items-center justify-center bg-black/40 backdrop-blur-sm transition-opacity duration-300">
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[95vh] flex flex-col relative overflow-hidden transform scale-95 transition-transform duration-300" id="doc-modal-content">
                
                <!-- Header -->
                <div class="flex justify-between items-center p-2 border-b border-gray-200">
                    <h3 id="doc-viewer-title" class="text-lg font-bold text-gray-800 truncate pr-4">Document Viewer</h3>
                    <button id="close-doc-viewer" class="text-gray-500 hover:text-red-500 transition-colors p-2 rounded-full hover:bg-red-50">
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <!-- Content Area -->
                <div id="doc-viewer-body" class="flex-1 bg-gray-50 relative overflow-auto flex items-center justify-center">
                    <div id="doc-loader" class="hidden absolute inset-0 flex items-center justify-center bg-white/80 z-10">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--green)]"></div>
                    </div>
                    <iframe id="doc-frame" class="w-full h-full border-0 hidden"></iframe>
                    <div id="doc-placeholder" class="text-center p-8 text-gray-500">
                        <p>Select a document to view</p>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Event Delegation for View Buttons
    document.body.addEventListener('click', async (e) => {
        const btn = e.target.closest('.view-doc-btn');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            const url = btn.dataset.url;
            const type = btn.dataset.type || 'pdf'; // pdf, docx, json
            const title = btn.dataset.title || 'Document';

            if (url) {
                openDocumentModal(url, type, title);
            } else {
                alert('Document URL not found.');
            }
        }
    });

    // Close handlers
    document.getElementById('close-doc-viewer')?.addEventListener('click', closeDocumentModal);
    document.getElementById('doc-viewer-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'doc-viewer-modal') closeDocumentModal();
    });
}

function openDocumentModal(url, type, title) {
    const modal = document.getElementById('doc-viewer-modal');
    const content = document.getElementById('doc-modal-content');
    const titleEl = document.getElementById('doc-viewer-title');
    const frame = document.getElementById('doc-frame');
    const placeholder = document.getElementById('doc-placeholder');
    const loader = document.getElementById('doc-loader');

    if (!modal) return;

    titleEl.textContent = title;
    modal.classList.remove('hidden');
    // Animation classes
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        content.classList.remove('scale-95');
        content.classList.add('scale-100');
    }, 10);

    loader.classList.remove('hidden');
    frame.classList.add('hidden');
    placeholder.classList.add('hidden');

    // Determine file type from URL, type parameter, or title (filename)
    const fileExt = url.split('.').pop()?.toLowerCase() || '';
    const titleExt = title.split('.').pop()?.toLowerCase() || '';
    const typeLower = (type || '').toLowerCase();
    
    // Check if it's a PDF - multiple ways to detect
    const isPdf = typeLower.includes('pdf') || 
                  typeLower === 'ai_report' || 
                  typeLower === 'application/pdf' ||
                  fileExt === 'pdf' || 
                  titleExt === 'pdf' ||
                  title.toLowerCase().endsWith('.pdf');
    
    const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(fileExt) || 
                    ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(titleExt) ||
                    typeLower.includes('image');
    
    const isText = ['json', 'txt', 'md'].includes(fileExt) || 
                   ['json', 'txt', 'md'].includes(titleExt) ||
                   typeLower.includes('json') || 
                   typeLower.includes('text') ||
                   typeLower === 'application/json';
    
    console.log('Document Viewer - URL:', url, 'Type:', type, 'Title:', title, 'isPdf:', isPdf, 'fileExt:', fileExt, 'titleExt:', titleExt);
    
    // For PDFs, images, and text files - load directly in iframe
    if (isPdf || isImage || isText) {
        console.log('Loading directly in iframe:', url);
        frame.src = url;
        frame.onload = () => {
            console.log('Document loaded successfully');
            loader.classList.add('hidden');
            frame.classList.remove('hidden');
        };
        frame.onerror = (err) => {
            console.error('Document load error:', err);
            loader.classList.add('hidden');
            placeholder.classList.remove('hidden');
            placeholder.innerHTML = `
                <div class="text-center p-8">
                    <p class="text-red-500 font-medium mb-2">Unable to preview this file</p>
                    <p class="text-gray-500 text-sm mb-4">The file may not exist or cannot be displayed in browser.</p>
                    <a href="${url}" download class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Download Instead</a>
                </div>
            `;
        };
    } else {
        console.log('Using Google Docs viewer for:', url);
        // For Office files (docx, xlsx, pptx) - use Google Docs Viewer
        const fullUrl = url.startsWith('http') ? url : window.location.origin + url;
        const gDocsUrl = `https://docs.google.com/gview?url=${encodeURIComponent(fullUrl)}&embedded=true`;
        frame.src = gDocsUrl;
        frame.onload = () => {
            loader.classList.add('hidden');
            frame.classList.remove('hidden');
        };
    }
}

function closeDocumentModal() {
    const modal = document.getElementById('doc-viewer-modal');
    const content = document.getElementById('doc-modal-content');
    const frame = document.getElementById('doc-frame');

    if (!modal) return;

    modal.classList.add('opacity-0');
    content.classList.remove('scale-100');
    content.classList.add('scale-95');

    setTimeout(() => {
        modal.classList.add('hidden');
        frame.src = ''; 
    }, 300);
}

// Auto-initialize
setupDocumentViewer();