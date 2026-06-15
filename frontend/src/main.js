import './index.css';
const API_URL = import.meta.env.VITE_API_URL ?? '';
const DEFAULT_PATIENT = import.meta.env.VITE_DEFAULT_PATIENT_ID ?? 'patient_001';

let patientId = new URLSearchParams(location.search).get('patient') || sessionStorage.getItem('patientId') || DEFAULT_PATIENT;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

async function api(path, opts = {}) {
    const res = await fetch(`${API_URL}${path}`, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s ?? '';
    return d.innerHTML;
}

function showView(name) {
    $$('.view-section').forEach((v) => v.classList.add('hidden'));
    const el = $(`#view-${name}`);
    if (el) el.classList.remove('hidden');
    $$('#sidebar-nav .sidebar-link').forEach((a) => {
        a.classList.toggle('active', a.dataset.view === name);
        a.classList.toggle('text-primary', a.dataset.view === name);
        a.classList.toggle('text-on-surface-variant/70', a.dataset.view !== name);
    });
    if (name === 'records') loadTimeline($('#records-timeline'));
}

function setLoading(on, text = 'Processing…') {
    const el = $('#loading-indicator');
    if (!el) return;
    el.classList.toggle('hidden', !on);
    const t = $('#loading-text');
    if (t) t.textContent = text;
}

function renderVitalsBadge(severity) {
    const badge = $('#badge-vitals');
    if (!badge) return;
    const critical = severity === 'CRITICAL' || severity === 'HIGH';
    badge.className = critical
        ? 'flex items-center gap-xs px-3 py-1 bg-error-container text-on-error-container rounded-full font-label-sm'
        : 'flex items-center gap-xs px-3 py-1 bg-secondary-container/30 text-on-secondary-container rounded-full font-label-sm';
    badge.innerHTML = critical
        ? '<span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span> Elevated Risk'
        : '<span class="w-1.5 h-1.5 rounded-full bg-secondary"></span> Stable Vitals';
}

function renderAlerts(alerts) {
    const box = $('#priority-alerts');
    if (!box) return;
    if (!alerts?.length) {
        box.innerHTML = '<p class="font-label-sm text-outline">No active alerts.</p>';
        return;
    }
    const dot = { critical: 'bg-primary', positive: 'bg-secondary', warning: 'bg-primary', info: 'bg-secondary' };
    box.innerHTML = alerts.map((a) => `
        <div class="flex gap-md items-start group">
            <div class="mt-1 w-2 h-2 rounded-full ${dot[a.type] || 'bg-outline'} shrink-0"></div>
            <div><p class="font-label-md text-on-surface">${esc(a.title)}</p>
            <p class="text-label-sm text-outline leading-tight">${esc(a.detail)}</p></div>
        </div>`).join('');
}

function renderOverview(summary) {
    const cards = $('#overview-cards');
    const activity = $('#overview-activity');
    if (!cards || !summary) return;
    const v = summary.vitals;
    const vitalsStr = v
        ? `HR ${v.heart_rate ?? '—'} · SpO₂ ${v.spo2 ?? '—'}% · BP ${v.systolic_bp ?? '—'}/${v.diastolic_bp ?? '—'}`
        : 'No vitals recorded';
    cards.innerHTML = [
        { label: 'Risk Score', val: `${summary.risk_score}/100`, sub: summary.severity },
        { label: 'Medications', val: summary.medications_count, sub: 'active records' },
        { label: 'Lab Results', val: summary.labs_count, sub: 'measurements' },
    ].map((c) => `
        <div class="minimal-card rounded-xl p-md">
            <p class="font-label-sm text-outline uppercase">${c.label}</p>
            <p class="font-headline-md text-on-surface mt-xs">${esc(String(c.val))}</p>
            <p class="font-label-sm text-outline/60">${esc(c.sub)}</p>
        </div>`).join('');
    const updated = summary.last_updated ? summary.last_updated.replace('T', ' ').slice(0, 16) : '—';
    activity.innerHTML = `<p><strong>Patient:</strong> ${esc(summary.patient_id)}</p>
        <p class="mt-sm"><strong>Latest vitals:</strong> ${esc(vitalsStr)}</p>
        <p class="mt-sm"><strong>Timeline events:</strong> ${summary.timeline_count}</p>
        <p class="mt-sm text-outline/60">Last updated: ${esc(updated)}</p>`;
}

function appendChat(role, text) {
    const stream = $('#chat-stream');
    if (!stream) return;
    if (role === 'user') {
        stream.insertAdjacentHTML('beforeend', `
            <div class="flex justify-end"><div class="max-w-[85%] bg-surface-container-high text-on-surface rounded-2xl rounded-tr-none px-md py-sm shadow-sm border border-outline-variant/20">
            <p class="font-body-md leading-relaxed">${esc(text)}</p></div></div>`);
    } else {
        stream.insertAdjacentHTML('beforeend', `
            <div class="minimal-card rounded-2xl p-lg shadow-sm">
            <div class="flex items-start gap-md">
            <div class="w-10 h-10 rounded-xl bg-tertiary/10 flex items-center justify-center text-tertiary shrink-0">
            <span class="material-symbols-outlined text-[22px]">auto_awesome</span></div>
            <div class="flex-1"><div class="flex items-center gap-sm mb-sm">
            <h3 class="font-label-sm text-outline/60 uppercase tracking-widest font-bold">Assistant</h3></div>
            <p class="font-headline-md text-on-surface leading-snug">${esc(text)}</p>
            <p class="text-label-sm text-outline/50 italic mt-md flex items-center gap-xs">
            <span class="material-symbols-outlined text-[14px]">info</span>Clinical verification required.</p></div></div></div>`);
    }
    stream.scrollTop = stream.scrollHeight;
}

async function loadSummary() {
    try {
        const s = await api(`/api/v1/patient/summary?patient_id=${encodeURIComponent(patientId)}`);
        renderVitalsBadge(s.severity);
        renderAlerts(s.priority_alerts);
        renderOverview(s);
        $('#patient-label').textContent = s.patient_id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        const inp = $('#patient-id-input');
        if (inp && document.activeElement !== inp) inp.value = patientId;
    } catch (e) {
        console.error(e);
        $('#patient-label').textContent = patientId;
    }
}

async function loadTimeline(container) {
    if (!container) return;
    try {
        const { timeline } = await api(`/api/v1/patient/timeline?patient_id=${encodeURIComponent(patientId)}`);
        if (!timeline?.length) {
            container.innerHTML = '<p class="text-outline">No events yet. Upload records or start a chat.</p>';
            return;
        }
        container.innerHTML = [...timeline].reverse().map((ev) => {
            const ts = ev.timestamp?.replace('T', ' ').slice(0, 16) ?? '';
            return `<div class="mb-md border-l-2 border-primary/30 pl-md relative">
                <p class="text-xs text-outline font-bold">${esc(ts)}</p>
                <p class="font-label-md">${esc(ev.description)}</p>
                <p class="text-label-sm text-primary">Score ${ev.risk_score} (${esc(ev.severity)})</p></div>`;
        }).join('');
    } catch {
        container.innerHTML = '<p class="text-error-container">Failed to load timeline.</p>';
    }
}

async function openVitalsModal() {
    const body = $('#modal-vitals-body');
    const modal = $('#modal-vitals');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    body.innerHTML = 'Loading…';
    try {
        const { vitals } = await api(`/api/v1/patient/vitals?patient_id=${encodeURIComponent(patientId)}`);
        body.innerHTML = vitals?.length
            ? vitals.map((v) => `<div class="mb-sm p-sm bg-surface-container-low rounded-lg font-label-sm">
                <strong>${esc(v.timestamp?.slice(0, 10))}</strong> — HR ${v.heart_rate ?? '—'}, SpO₂ ${v.spo2 ?? '—'}%, Temp ${v.temperature ?? '—'}°F</div>`).join('')
            : '<p class="text-outline">No vitals recorded.</p>';
    } catch {
        body.innerHTML = '<p class="text-error-container">Failed to load vitals.</p>';
    }
}

async function openLabsModal() {
    const body = $('#modal-labs-body');
    const modal = $('#modal-labs');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    body.innerHTML = 'Loading…';
    try {
        const { labs } = await api(`/api/v1/patient/labs?patient_id=${encodeURIComponent(patientId)}`);
        body.innerHTML = labs?.length
            ? labs.map((l) => `<div class="mb-sm p-sm bg-surface-container-low rounded-lg font-label-sm">
                <strong>${esc(l.test)}</strong>: ${l.value} ${esc(l.unit)} <span class="text-outline">(ref ${esc(l.reference_range || 'N/A')})</span></div>`).join('')
            : '<p class="text-outline">No lab results.</p>';
    } catch {
        body.innerHTML = '<p class="text-error-container">Failed to load labs.</p>';
    }
}

function closeModals() {
    $$('#modal-vitals, #modal-labs').forEach((m) => {
        m.classList.add('hidden');
        m.classList.remove('flex');
    });
}

async function sendChat() {
    const input = $('#chat-input');
    const text = input?.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';
    appendChat('user', text);
    setLoading(true, 'Cross-referencing datasets…');
    try {
        const data = await api('/api/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, patient_id: patientId }),
        });
        appendChat('assistant', data.response);
        const alerts = (data.alerts || []).map((d) => ({
            type: data.sos_detected ? 'critical' : 'warning',
            title: data.severity || 'Alert',
            detail: d,
        }));
        if (data.sos_detected) alerts.unshift({ type: 'critical', title: 'Emergency', detail: 'SOS symptoms detected — seek immediate care.' });
        renderAlerts(alerts.length ? alerts : null);
        renderVitalsBadge(data.severity);
        await loadSummary();
    } catch (e) {
        appendChat('assistant', `Unable to reach the reasoning engine: ${e.message}`);
    } finally {
        setLoading(false);
    }
}

async function handleUpload(file, endpoint, statusEl) {
    if (!file || !endpoint) return;
    if (statusEl) statusEl.innerHTML = `<span class="text-primary animate-pulse">Processing ${esc(file.name)}…</span>`;
    setLoading(true, `Processing ${file.name}…`);
    const form = new FormData();
    form.append('file', file);
    try {
        const data = await api(`/api/v1${endpoint}?patient_id=${encodeURIComponent(patientId)}`, { method: 'POST', body: form });
        if (statusEl) statusEl.innerHTML = `<span class="text-on-secondary-container">${esc(data.message)}</span>`;
        appendChat('assistant', data.message || `Uploaded ${file.name}`);
        await loadSummary();
        if (!$('#view-records').classList.contains('hidden')) loadTimeline($('#records-timeline'));
    } catch (e) {
        if (statusEl) statusEl.innerHTML = `<span class="text-on-error-container">${esc(e.message)}</span>`;
        appendChat('assistant', `Failed to upload ${file.name}: ${e.message}`);
    } finally {
        setLoading(false);
    }
}

function initUploads() {
    $$('.upload-zone').forEach((zone) => {
        const input = zone.querySelector('.file-input');
        if (!input) return;
        zone.addEventListener('click', (e) => { if (e.target !== input) input.click(); });
        zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-active'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('drag-active'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-active');
            if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0], zone.dataset.endpoint, $('#records-upload-status'));
        });
        input.addEventListener('change', () => {
            const file = input.files[0];
            if (!file) return;
            let endpoint = zone.dataset.endpoint;
            if (zone.id === 'chat-attach-btn') {
                const ext = file.name.split('.').pop().toLowerCase();
                const name = file.name.toLowerCase();
                if (['jpg', 'jpeg', 'png', 'tiff'].includes(ext)) endpoint = '/upload/image';
                else if (['mp3', 'wav', 'm4a', 'ogg'].includes(ext)) endpoint = '/upload/audio';
                else if (['mp4', 'mov', 'webm', 'avi'].includes(ext)) endpoint = '/upload/video';
                else if (['pdf', 'docx', 'txt'].includes(ext)) {
                    if (name.includes('prescription') || name.includes('rx') || name.includes('meds')) endpoint = '/upload/prescription';
                    else if (name.includes('lab') || name.includes('report') || name.includes('blood')) endpoint = '/upload/lab-report';
                    else endpoint = '/upload/document';
                }
            }
            handleUpload(file, endpoint, $('#records-upload-status'));
            input.value = '';
        });
    });
}

function initNav() {
    $$('#sidebar-nav .sidebar-link').forEach((a) => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            showView(a.dataset.view);
        });
    });
    $('#link-vitals')?.addEventListener('click', openVitalsModal);
    $('#link-labs')?.addEventListener('click', openLabsModal);
    $$('.modal-close').forEach((b) => b.addEventListener('click', closeModals));
    $$('#modal-vitals, #modal-labs').forEach((m) => m.addEventListener('click', (e) => { if (e.target === m) closeModals(); }));
    $('#btn-notifications')?.addEventListener('click', () => {
        showView('chat');
        $('#priority-alerts')?.scrollIntoView({ behavior: 'smooth' });
    });
    $('#patient-id-save')?.addEventListener('click', () => {
        const v = $('#patient-id-input')?.value.trim();
        if (!v) return;
        patientId = v;
        sessionStorage.setItem('patientId', v);
        const url = new URL(location.href);
        url.searchParams.set('patient', v);
        history.replaceState(null, '', url);
        loadSummary();
        $('#chat-stream').innerHTML = '';
        appendChat('assistant', `Switched to patient ${v}. Upload records or ask a clinical question.`);
    });
}

function initChat() {
    $('#chat-submit')?.addEventListener('click', sendChat);
    const input = $('#chat-input');
    input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
    });
    input?.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
    });
}

async function checkHealth() {
    const el = $('#api-status');
    try {
        const h = await api('/health');
        if (el) el.textContent = `API: ${h.status} · AI: Groq Ready`;
    } catch {
        if (el) el.textContent = 'API unreachable — start backend with uvicorn backend.main:app';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initChat();
    initUploads();
    loadSummary();
    checkHealth();
    appendChat('assistant', 'Hello. I am your clinical intelligence assistant. Ask about patient data or upload records via Records or the attach button.');
});
