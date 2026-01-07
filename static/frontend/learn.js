import { apiCall, showModal } from './utils.js';

export async function renderLearn() {
    let files = [];
    try {
        files = await apiCall('/learn/list');
    } catch (e) {
        console.error("Failed to fetch learn files", e);
        return `<p class="text-red-500">Error loading learning materials.</p>`;
    }

    if (!files || files.length === 0) {
        return `
            <div class="bg-white rounded-2xl p-12 text-center border border-gray-100">
                <p class="text-gray-500 font-medium">No learning materials available yet.</p>
            </div>
        `;
    }

    const gridItems = files.map(file => {
        const isPdf = file.type === 'pdf';

        // Icon logic
        const icon = isPdf
            ? `<div class="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                 <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
               </div>`
            : `<div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                 <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
               </div>`;

        return `
            <div class="bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 group flex flex-col h-full">
                <!-- Top Part: Content Info -->
                <div class="p-6 flex-1 flex flex-col items-center text-center bg-gradient-to-b from-white to-gray-50/50">
                    ${icon}
                    <h3 class="font-bold text-gray-900 text-lg mb-2 leading-tight line-clamp-2" title="${file.name}">${file.name.replace('.md', '').replace('.pdf', '')}</h3>
                    <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">${file.type.toUpperCase()} • ${(file.size / 1024).toFixed(0)} KB</p>
                </div>
                
                <!-- Bottom Part: Actions (Darker Background) -->
                <div class="bg-gray-50 p-4 border-t border-gray-100 grid grid-cols-2 gap-3">
                    <button 
                         onclick="window.openLearnFile('${file.name}', '${file.type}')"
                         class="col-span-2 flex items-center justify-center gap-2 w-full py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:text-green-600 hover:border-green-200 transition-colors shadow-sm"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                        Read Now
                    </button>
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
            ${gridItems}
        </div>
    `;
}

window.openLearnFile = async function (filename, type) {
    if (type === 'pdf') {
        const url = `/api/v1/learn/content/${filename}`;
        showModal(filename.replace('.pdf', ''), `
            <div class="h-[80vh] bg-gray-900 rounded-xl overflow-hidden">
                <iframe src="${url}" class="w-full h-full" frameborder="0"></iframe>
            </div>
        `);
    } else if (type === 'md') {
        try {
            const data = await apiCall(`/learn/content/${filename}`);
            let content = '';

            if (window.marked) {
                // Configure marked for better rendering if needed
                content = window.marked.parse(data.content);
            } else {
                content = `<pre class="whitespace-pre-wrap font-mono text-sm">${data.content}</pre>`;
            }

            showModal(filename.replace('.md', ''), `
                <div class="bg-white p-8 md:p-12 rounded-xl max-w-4xl mx-auto h-[80vh] overflow-y-auto custom-scrollbar">
                    <div class="prose prose-lg prose-green max-w-none">
                        ${content}
                    </div>
                </div>
            `);

            // Add custom styling after rendering
            setTimeout(styleMarkdownContent, 100);

        } catch (e) {
            alert("Error loading content: " + e.message);
        }
    } else {
        window.open(`/api/v1/learn/content/${filename}`, '_blank');
    }
};

// Helper to enhance markdown styling dynamically
function styleMarkdownContent() {
    const containers = document.querySelectorAll('.prose');
    containers.forEach(container => {
        // Enhance headings
        container.querySelectorAll('h1').forEach(h => h.className = "text-3xl font-extrabold text-gray-900 mb-6 pb-4 border-b border-gray-200");
        container.querySelectorAll('h2').forEach(h => h.className = "text-2xl font-bold text-gray-800 mt-10 mb-4 flex items-center gap-2");
        container.querySelectorAll('h3').forEach(h => h.className = "text-xl font-semibold text-gray-800 mt-8 mb-3");

        // Enhance paragraphs
        container.querySelectorAll('p').forEach(p => p.className = "text-gray-600 leading-relaxed mb-5 text-[16px]");

        // Enhance lists
        container.querySelectorAll('ul').forEach(ul => ul.className = "list-disc pl-6 space-y-2 mb-6 text-gray-600");
        container.querySelectorAll('ol').forEach(ol => ol.className = "list-decimal pl-6 space-y-2 mb-6 text-gray-600");

        // Enhance blockquotes
        container.querySelectorAll('blockquote').forEach(bq => bq.className = "border-l-4 border-green-500 bg-green-50 p-4 rounded-r-lg italic text-gray-700 mb-6");

        // Enhance code blocks
        container.querySelectorAll('pre').forEach(pre => pre.className = "bg-gray-900 text-gray-100 p-4 rounded-xl overflow-x-auto mb-6 text-sm");
        container.querySelectorAll('code').forEach(code => {
            if (!code.closest('pre')) {
                code.className = "bg-gray-100 text-green-700 px-1.5 py-0.5 rounded text-sm font-mono font-medium";
            }
        });

        // Enhance tables
        container.querySelectorAll('table').forEach(table => {
            table.className = "w-full border-collapse mb-6 bg-white rounded-lg overflow-hidden shadow-sm border border-gray-200";
            table.querySelectorAll('th').forEach(th => th.className = "bg-gray-50 text-left p-3 font-semibold text-gray-700 border-b border-gray-200");
            table.querySelectorAll('td').forEach(td => td.className = "p-3 border-b border-gray-100 text-gray-600");
            table.querySelectorAll('tr:last-child td').forEach(td => td.classList.remove('border-b'));
        });

        // Enhance links
        container.querySelectorAll('a').forEach(a => a.className = "text-green-600 hover:text-green-700 font-medium underline decoration-green-300 hover:decoration-green-600 transition-all");
    });
}