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
        const icon = isPdf
            ? '<svg class="w-10 h-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>'
            : '<svg class="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>';

        return `
            <div 
                onclick="window.openLearnFile('${file.name}', '${file.type}')"
                class="aspect-[4/5] bg-gradient-to-tl from-white via-fuchsia-100 to-white p-2 rounded border border-[color:var(--border-color)] hover:-translate-y-2 transition-all cursor-pointer group flex flex-col items-center justify-center text-center space-y-6"
            >
                <div class="w-25 h-25 bg-white rounded-3xl shadow-sm flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                    ${icon}
                </div>
                <div class="flex-1 flex flex-col justify-center">
                    <h3 class="font-bold text-gray-900 text-lg mb-2 group-hover:text-[var(--green)] transition-all leading-tight">${file.name.replace('.md', '').replace('.pdf', '')}</h3>
                    <p class="text-[15px] text-green-500 font-semibold uppercase tracking-widest bg-green-50 px-3 py-1 rounded-full w-fit mx-auto">${file.type} • ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            ${gridItems}
        </div>
    `;
}

window.openLearnFile = async function (filename, type) {
    if (type === 'pdf') {
        const url = `/api/v1/learn/content/${filename}`;
        showModal(filename, `
            <div class="h-[75vh]">
                <iframe src="${url}" class="w-full h-full rounded-xl border border-gray-100" frameborder="0"></iframe>
            </div>
        `);
    } else if (type === 'md') {
        try {
            const data = await apiCall(`/learn/content/${filename}`);
            const content = window.marked ? window.marked.parse(data.content) : `<pre>${data.content}</pre>`;
            showModal(filename, `
                <div class="prose prose-green max-w-none">
                    ${content}
                </div>
            `);
        } catch (e) {
            alert("Error loading content: " + e.message);
        }
    } else {
        window.open(`/api/v1/learn/content/${filename}`, '_blank');
    }
};
