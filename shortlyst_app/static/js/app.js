// Shortlyst Client Application

let selectedJdFile = null;
let resumeFiles = [];

const ALLOWED_EXTS = ['.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'];

function isAllowedFile(name) {
    const lower = name.toLowerCase();
    return ALLOWED_EXTS.some(ext => lower.endsWith(ext));
}

function isImageFile(name) {
    const lower = name.toLowerCase();
    return ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'].some(ext => lower.endsWith(ext));
}

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initLlmHealthCheck();
    initJdInputs();
    initResumeDropzone();
    initScreeningFlow();
});

// ── 1. Dark & Light Theme Toggle ───────────────────────────────────────────────
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.contains('dark');
        if (isDark) {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
            localStorage.setItem('shortlyst_theme', 'light');
        } else {
            document.documentElement.classList.remove('light');
            document.documentElement.classList.add('dark');
            localStorage.setItem('shortlyst_theme', 'dark');
        }
    });
}

// ── 2. LLM Health Check & Model Population ─────────────────────────────────────
async function initLlmHealthCheck() {
    const indicator = document.getElementById('llm-indicator');
    const text = document.getElementById('llm-status-text');
    const chatSelect = document.getElementById('chat-model-select');
    const embedSelect = document.getElementById('embed-model-select');
    const countLabel = document.getElementById('model-count-label');
    const activeModelDisplay = document.getElementById('active-model-display');

    try {
        const res = await fetch('/api/health/llm');
        const data = await res.json();
        
        if (data.ollama === 'connected') {
            indicator.className = 'w-2 h-2 rounded-full bg-emerald-400';
            const models = data.availableModels || [];
            text.textContent = `Ollama: Online (${models.length} models)`;

            if (countLabel) {
                countLabel.textContent = `${models.length} local Ollama models ready for inference`;
            }

            // Populate Dropdowns if on workspace
            if (chatSelect && embedSelect && models.length > 0) {
                chatSelect.innerHTML = '';
                embedSelect.innerHTML = '';

                models.forEach(m => {
                    // Chat model option
                    const chatOpt = document.createElement('option');
                    chatOpt.value = m;
                    chatOpt.textContent = m;
                    if (m.toLowerCase().includes('llama3.2') || m.toLowerCase().includes('llama3') || m.toLowerCase().includes('mistral')) {
                        chatOpt.textContent += ' (Recommended)';
                    }
                    chatSelect.appendChild(chatOpt);

                    // Embed model option
                    const embedOpt = document.createElement('option');
                    embedOpt.value = m;
                    embedOpt.textContent = m;
                    if (m.toLowerCase().includes('embed') || m.toLowerCase().includes('nomic')) {
                        embedOpt.textContent += ' (Vector Embeddings)';
                    }
                    embedSelect.appendChild(embedOpt);
                });

                // Select sensible defaults
                const defaultChat = models.find(m => m.toLowerCase().includes('llama3.2')) || models.find(m => !m.toLowerCase().includes('embed')) || models[0];
                const defaultEmbed = models.find(m => m.toLowerCase().includes('embed')) || models[0];

                if (defaultChat) chatSelect.value = defaultChat;
                if (defaultEmbed) embedSelect.value = defaultEmbed;

                updateActiveModelDisplay();
                chatSelect.addEventListener('change', updateActiveModelDisplay);
                embedSelect.addEventListener('change', updateActiveModelDisplay);
            }
        } else {
            indicator.className = 'w-2 h-2 rounded-full bg-rose-500';
            text.textContent = 'Ollama: Offline (Start Ollama)';
            if (countLabel) {
                countLabel.textContent = 'Ollama unreachable — ensure Ollama is running at http://localhost:11434';
            }
        }
    } catch (err) {
        indicator.className = 'w-2 h-2 rounded-full bg-rose-500';
        text.textContent = 'Ollama: Unreachable';
    }

    function updateActiveModelDisplay() {
        if (!activeModelDisplay || !chatSelect || !embedSelect) return;
        activeModelDisplay.textContent = `Inference: ${embedSelect.value} (Vectors) + ${chatSelect.value} (LLM) + RapidOCR`;
    }
}

// ── 3. Job Description Inputs ─────────────────────────────────────────────────
function initJdInputs() {
    const modeTextBtn = document.getElementById('jd-mode-text');
    const modePdfBtn = document.getElementById('jd-mode-pdf');
    const textContainer = document.getElementById('jd-text-container');
    const pdfContainer = document.getElementById('jd-pdf-container');
    const textInput = document.getElementById('jd-text-input');
    const charCount = document.getElementById('jd-char-count');
    const fileInput = document.getElementById('jd-file-input');
    const fileNameDisplay = document.getElementById('jd-file-name');

    if (!modeTextBtn) return;

    modeTextBtn.addEventListener('click', () => {
        modeTextBtn.className = 'px-2.5 py-1 rounded-md bg-surface-800 text-white font-medium shadow-sm transition';
        modePdfBtn.className = 'px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition';
        textContainer.classList.remove('hidden');
        pdfContainer.classList.add('hidden');
        selectedJdFile = null;
        fileNameDisplay.textContent = '';
        validateForm();
    });

    modePdfBtn.addEventListener('click', () => {
        modePdfBtn.className = 'px-2.5 py-1 rounded-md bg-surface-800 text-white font-medium shadow-sm transition';
        modeTextBtn.className = 'px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition';
        pdfContainer.classList.remove('hidden');
        textContainer.classList.add('hidden');
        textInput.value = '';
        charCount.textContent = '0 characters';
        validateForm();
    });

    textInput.addEventListener('input', () => {
        charCount.textContent = `${textInput.value.length} characters`;
        validateForm();
    });

    pdfContainer.addEventListener('click', () => fileInput.click());
    pdfContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        pdfContainer.classList.add('border-brand-500');
    });
    pdfContainer.addEventListener('dragleave', () => pdfContainer.classList.remove('border-brand-500'));
    pdfContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        pdfContainer.classList.remove('border-brand-500');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleJdFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files[0]) {
            handleJdFile(fileInput.files[0]);
        }
    });

    function handleJdFile(file) {
        if (!isAllowedFile(file.name)) {
            alert('Please select a valid PDF or Image file (.png, .jpg, .webp).');
            return;
        }
        selectedJdFile = file;
        const icon = isImageFile(file.name) ? '🖼️ Image (OCR)' : '📄 PDF';
        fileNameDisplay.textContent = `Attached: ${file.name} [${icon}] (${formatBytes(file.size)})`;
        validateForm();
    }
}

// ── 4. Resumes Dropzone ───────────────────────────────────────────────────────
function initResumeDropzone() {
    const dropzone = document.getElementById('resumes-dropzone');
    const fileInput = document.getElementById('resumes-file-input');
    const list = document.getElementById('resumes-list');
    const badge = document.getElementById('resume-count-badge');
    const clearBtn = document.getElementById('clear-resumes-btn');
    const emptyHint = document.getElementById('empty-resumes-hint');

    if (!dropzone) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-indigo-500', 'bg-indigo-950/20');
    });
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-indigo-500', 'bg-indigo-950/20');
    });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-indigo-500', 'bg-indigo-950/20');
        if (e.dataTransfer.files) {
            addResumeFiles(Array.from(e.dataTransfer.files));
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files) {
            addResumeFiles(Array.from(fileInput.files));
            fileInput.value = '';
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            resumeFiles = [];
            renderResumeList();
            validateForm();
        });
    }

    function addResumeFiles(files) {
        const allowed = files.filter(f => isAllowedFile(f.name));
        if (allowed.length < files.length) {
            alert('Ignored unsupported files. Please upload PDF, PNG, JPG, or WEBP documents.');
        }

        for (const file of allowed) {
            if (!resumeFiles.some(f => f.name === file.name && f.size === file.size)) {
                resumeFiles.push(file);
            }
        }
        renderResumeList();
        validateForm();
    }

    function renderResumeList() {
        badge.textContent = `${resumeFiles.length} Loaded`;
        if (resumeFiles.length === 0) {
            list.innerHTML = '';
            list.appendChild(emptyHint);
            emptyHint.classList.remove('hidden');
            clearBtn.classList.add('hidden');
            return;
        }

        emptyHint.classList.add('hidden');
        clearBtn.classList.remove('hidden');
        list.innerHTML = '';

        resumeFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs font-mono';
            const icon = isImageFile(file.name) ? '🖼️' : '📄';
            item.innerHTML = `
                <div class="flex items-center space-x-2 truncate">
                    <span class="text-indigo-400">${icon}</span>
                    <span class="text-slate-200 truncate">${escapeHtml(file.name)}</span>
                    <span class="text-slate-500 text-[10px]">(${formatBytes(file.size)})</span>
                </div>
                <button type="button" data-index="${index}" class="text-slate-500 hover:text-rose-400 px-2 py-0.5 rounded transition">✕</button>
            `;
            item.querySelector('button').addEventListener('click', (e) => {
                e.stopPropagation();
                resumeFiles.splice(index, 1);
                renderResumeList();
                validateForm();
            });
            list.appendChild(item);
        });
    }
}

// ── 5. Form Validation ────────────────────────────────────────────────────────
function validateForm() {
    const textInput = document.getElementById('jd-text-input');
    const runBtn = document.getElementById('run-screening-btn');
    if (!runBtn) return;

    const hasJd = (textInput && textInput.value.trim().length > 10) || selectedJdFile !== null;
    const hasResumes = resumeFiles.length > 0;

    runBtn.disabled = !(hasJd && hasResumes);
}

// ── 6. Screening Flow with Dynamic Model Selection & Redirect ─────────────────
function initScreeningFlow() {
    const runBtn = document.getElementById('run-screening-btn');
    const processing = document.getElementById('processing-state');
    const resetBtn = document.getElementById('reset-all-btn');
    const statusSubtitle = document.getElementById('pipeline-status-subtitle');
    const progressBar = document.getElementById('pipeline-progress-bar');
    const chatSelect = document.getElementById('chat-model-select');
    const embedSelect = document.getElementById('embed-model-select');

    if (!runBtn) return;

    runBtn.addEventListener('click', async () => {
        runBtn.disabled = true;
        processing.classList.remove('hidden');
        processing.scrollIntoView({ behavior: 'smooth' });

        const form = new FormData();
        const textInput = document.getElementById('jd-text-input');

        if (selectedJdFile) {
            form.append('jdFile', selectedJdFile);
        } else {
            form.append('jdText', textInput.value.trim());
        }

        resumeFiles.forEach(f => form.append('resumes', f));

        // Append chosen models if selected
        const chosenChat = chatSelect ? chatSelect.value : 'llama3.2';
        const chosenEmbed = embedSelect ? embedSelect.value : 'nomic-embed-text';
        form.append('chatModel', chosenChat);
        form.append('embedModel', chosenEmbed);

        // Phased progress meter while Ollama/OCR processes
        let progress = 12;
        progressBar.style.width = `${progress}%`;
        statusSubtitle.textContent = `Extracting text and generating embeddings via ${chosenEmbed}...`;

        const timer = setInterval(() => {
            if (progress < 85) {
                progress += Math.floor(Math.random() * 7) + 3;
                progressBar.style.width = `${progress}%`;
                if (progress > 35 && progress < 65) {
                    statusSubtitle.textContent = `Computing vector cosine similarity alignment...`;
                } else if (progress >= 65) {
                    statusSubtitle.textContent = `Evaluating candidate fit with ${chosenChat}...`;
                }
            }
        }, 1200);

        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                body: form
            });

            clearInterval(timer);
            progressBar.style.width = '100%';

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || `Server responded with ${res.status}`);
            }

            const data = await res.json();
            statusSubtitle.textContent = 'Screening complete! Redirecting to results dashboard...';

            setTimeout(() => {
                if (data.redirectUrl) {
                    window.location.href = data.redirectUrl;
                } else if (data.screeningId) {
                    window.location.href = `/results/${data.screeningId}`;
                } else {
                    window.location.href = '/results';
                }
            }, 600);

        } catch (err) {
            clearInterval(timer);
            processing.classList.add('hidden');
            runBtn.disabled = false;
            alert(`Screening Failed: ${err.message}\n\nPlease check Ollama status at http://localhost:11434 and ensure ${chosenChat} and ${chosenEmbed} are pulled.`);
        }
    });

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            const textInput = document.getElementById('jd-text-input');
            if (textInput) textInput.value = '';
            document.getElementById('jd-char-count').textContent = '0 characters';
            selectedJdFile = null;
            document.getElementById('jd-file-name').textContent = '';
            resumeFiles = [];
            document.getElementById('resume-count-badge').textContent = '0 Loaded';
            document.getElementById('resumes-list').innerHTML = '<p id="empty-resumes-hint" class="text-xs text-slate-600 italic py-4 text-center">No resumes added yet. Drop files above.</p>';
            document.getElementById('clear-resumes-btn').classList.add('hidden');
            validateForm();
        });
    }
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
