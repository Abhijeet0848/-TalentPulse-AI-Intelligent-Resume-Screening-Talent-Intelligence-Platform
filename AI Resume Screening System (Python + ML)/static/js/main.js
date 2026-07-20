// TalentPulse AI - Main Client JavaScript Logic

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initDragAndDrop();
    initLeaderboardSearch();
    initStatusToggles();
    initAnimatedCounters();
    initInteractiveFaq();
    initDemoModals();
    initHeroResumeSim();
    initDashboardTabs();
    initKanbanDragAndDrop();
});

// Kanban Board Drag & Drop Status Update
function initKanbanDragAndDrop() {
    const cards = document.querySelectorAll('.kanban-card');
    const cols = document.querySelectorAll('.kanban-col');

    if (cards.length === 0 || cols.length === 0) return;

    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', card.getAttribute('data-result-id'));
            card.classList.add('dragging');
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
    });

    cols.forEach(col => {
        col.addEventListener('dragover', (e) => {
            e.preventDefault();
            col.style.background = 'rgba(2, 132, 199, 0.08)';
        });

        col.addEventListener('dragleave', () => {
            col.style.background = '';
        });

        col.addEventListener('drop', async (e) => {
            e.preventDefault();
            col.style.background = '';
            
            const resultId = e.dataTransfer.getData('text/plain');
            const newStatus = col.getAttribute('data-status');
            const card = document.querySelector(`.kanban-card[data-result-id="${resultId}"]`);

            if (card && newStatus) {
                col.appendChild(card);
                
                try {
                    const response = await fetch(`/api/screening/${resultId}/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: newStatus })
                    });
                    const data = await response.json();
                    if (data.success) {
                        showToast('Candidate status moved to ' + newStatus, 'success');
                    }
                } catch (err) {
                    console.error(err);
                }
            }
        });
    });
}

function initThemeToggle() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
        });
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    toggleBtns.forEach(btn => {
        if (theme === 'dark') {
            btn.innerHTML = '<i class="fa-solid fa-sun" style="color: #F59E0B;"></i>';
            btn.setAttribute('title', 'Switch to Light Mode');
        } else {
            btn.innerHTML = '<i class="fa-solid fa-moon" style="color: #6366F1;"></i>';
            btn.setAttribute('title', 'Switch to Dark Mode');
        }
    });
}

function initAnimatedCounters() {
    const statNumbers = document.querySelectorAll('.counter-val');
    if (statNumbers.length === 0) return;

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const targetNum = parseInt(target.getAttribute('data-target'), 10);
                const suffix = target.getAttribute('data-suffix') || '';
                let currentNum = 0;
                const increment = Math.ceil(targetNum / 40);

                const timer = setInterval(() => {
                    currentNum += increment;
                    if (currentNum >= targetNum) {
                        currentNum = targetNum;
                        clearInterval(timer);
                    }
                    target.textContent = currentNum.toLocaleString() + suffix;
                }, 30);

                observer.unobserve(target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(el => observer.observe(el));
}

function initHeroResumeSim() {
    const heroDropzone = document.getElementById('heroDropzone');
    const heroFileInput = document.getElementById('heroFileInput');
    const simResult = document.getElementById('heroSimResult');

    if (!heroDropzone || !heroFileInput || !simResult) return;

    heroDropzone.addEventListener('click', () => heroFileInput.click());

    ['dragenter', 'dragover'].forEach(name => {
        heroDropzone.addEventListener(name, (e) => {
            e.preventDefault();
            heroDropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        heroDropzone.addEventListener(name, (e) => {
            e.preventDefault();
            heroDropzone.classList.remove('dragover');
        });
    });

    heroDropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) runSimAnimation(files[0].name);
    });

    heroFileInput.addEventListener('change', () => {
        if (heroFileInput.files.length > 0) runSimAnimation(heroFileInput.files[0].name);
    });
}

function runSimAnimation(fileName) {
    const simResult = document.getElementById('heroSimResult');
    if (!simResult) return;

    simResult.style.display = 'block';
    
    const steps = [
        { label: '📄 Reading Resume File (' + fileName + ')...', progress: 20 },
        { label: '🔍 Extracting Contact Info & Technical Skills...', progress: 45 },
        { label: '🎯 Comparing Vector Similarity to Job Profile...', progress: 70 },
        { label: '⚡ Calculating Weighted Fit Score Matrix...', progress: 90 },
        { label: '✅ Screening Analysis Complete!', progress: 100 }
    ];

    let stepIdx = 0;
    const progressFill = document.getElementById('simProgressFill');
    const stepLabel = document.getElementById('simStepLabel');
    const outputCard = document.getElementById('simOutputCard');

    outputCard.style.display = 'none';

    const interval = setInterval(() => {
        if (stepIdx < steps.length) {
            stepLabel.textContent = steps[stepIdx].label;
            progressFill.style.width = steps[stepIdx].progress + '%';
            stepIdx++;
        } else {
            clearInterval(interval);
            outputCard.style.display = 'block';
        }
    }, 600);
}

function initInteractiveFaq() {
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                const isActive = item.classList.contains('active');
                faqItems.forEach(i => i.classList.remove('active'));
                if (!isActive) item.classList.add('active');
            });
        }
    });
}

function initDemoModals() {
    const watchDemoBtn = document.getElementById('watchDemoBtn');
    const bookDemoBtn = document.getElementById('bookDemoBtn');
    const videoModal = document.getElementById('videoModal');
    const bookModal = document.getElementById('bookModal');
    const closeBtns = document.querySelectorAll('.modal-close');

    if (watchDemoBtn && videoModal) {
        watchDemoBtn.addEventListener('click', () => videoModal.classList.add('active'));
    }

    if (bookDemoBtn && bookModal) {
        bookDemoBtn.addEventListener('click', () => bookModal.classList.add('active'));
    }

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (videoModal) videoModal.classList.remove('active');
            if (bookModal) bookModal.classList.remove('active');
        });
    });

    [videoModal, bookModal].forEach(m => {
        if (m) {
            m.addEventListener('click', (e) => {
                if (e.target === m) m.classList.remove('active');
            });
        }
    });
}

function initDashboardTabs() {
    const tabBtns = document.querySelectorAll('.dash-tab-btn');
    const tabViews = document.querySelectorAll('.dash-tab-view');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('btn-primary'));
            tabBtns.forEach(b => b.classList.add('btn-secondary'));
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary');

            tabViews.forEach(v => {
                if (v.id === target) v.style.display = 'block';
                else v.style.display = 'none';
            });
        });
    });
}

function initDragAndDrop() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileList(files);
        }
    });

    fileInput.addEventListener('change', () => {
        updateFileList(fileInput.files);
    });
}

function updateFileList(files) {
    const fileListPreview = document.getElementById('fileListPreview');
    if (!fileListPreview) return;
    
    fileListPreview.innerHTML = '';
    if (files.length === 0) return;

    let html = '<div style="margin-top: 16px; text-align: left;"><h5 style="margin-bottom: 8px; font-size: 13px; color: var(--text-secondary);">Selected Files (' + files.length + '):</h5><ul style="list-style: none; padding: 0;">';
    for (let i = 0; i < files.length; i++) {
        html += `<li style="padding: 6px 12px; background: var(--bg-card-hover); border-radius: 6px; margin-bottom: 4px; font-size: 13px; display: flex; justify-content: space-between;">
            <span>📄 ${files[i].name}</span>
            <span style="color: var(--text-muted);">${(files[i].size / 1024).toFixed(1)} KB</span>
        </li>`;
    }
    html += '</ul></div>';
    fileListPreview.innerHTML = html;
}

function initLeaderboardSearch() {
    const searchInput = document.getElementById('tableSearchInput');
    const categorySelect = document.getElementById('categoryFilterSelect');
    const statusSelect = document.getElementById('statusFilterSelect');
    const tableBody = document.getElementById('leaderboardTableBody');

    if (!tableBody) return;

    function filterTable() {
        const searchVal = searchInput ? searchInput.value.toLowerCase() : '';
        const catVal = categorySelect ? categorySelect.value : 'ALL';
        const statusVal = statusSelect ? statusSelect.value : 'ALL';

        const rows = tableBody.querySelectorAll('tr');

        rows.forEach(row => {
            const name = row.getAttribute('data-name') || '';
            const skills = row.getAttribute('data-skills') || '';
            const category = row.getAttribute('data-category') || '';
            const status = row.getAttribute('data-status') || '';

            const matchesSearch = name.toLowerCase().includes(searchVal) || skills.toLowerCase().includes(searchVal);
            const matchesCat = catVal === 'ALL' || category === catVal;
            const matchesStatus = statusVal === 'ALL' || status === statusVal;

            if (matchesSearch && matchesCat && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (categorySelect) categorySelect.addEventListener('change', filterTable);
    if (statusSelect) statusSelect.addEventListener('change', filterTable);
}

function initStatusToggles() {
    document.querySelectorAll('.status-select-btn').forEach(select => {
        select.addEventListener('change', async function() {
            const resultId = this.getAttribute('data-result-id');
            const newStatus = this.value;
            
            try {
                const response = await fetch(`/api/screening/${resultId}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                
                const data = await response.json();
                if (data.success) {
                    const row = this.closest('tr');
                    if (row) row.setAttribute('data-status', newStatus);
                    showToast('Status updated successfully!', 'success');
                }
            } catch (err) {
                console.error(err);
            }
        });
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        padding: 12px 24px;
        background: ${type === 'success' ? 'var(--emerald)' : (type === 'error' ? 'var(--rose)' : 'var(--primary)')};
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        z-index: 9999;
        transition: opacity 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}
