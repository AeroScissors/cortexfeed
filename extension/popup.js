const SERVER = 'http://127.0.0.1:5050';

let conversationText     = '';
let detectedFiles        = [];
let projectPath          = '';
let isOnline             = false;
let currentSite          = 'unknown';
let recommendedAI        = 'claude'; // updated by classifyAndRoute()
// Track whether the user manually edited intent/files THIS session.
// Fresh analysis always overwrites storage-restored values —
// only skip the overwrite if the user typed something new themselves.
let intentUserEdited     = false;
let filesUserEdited      = false;

// ── State persistence (chrome.storage.local) ──────────────
async function saveState() {
  await chrome.storage.local.set({
    cf_project_path: document.getElementById('project-path').value.trim(),
    cf_intent:       document.getElementById('intent').value.trim(),
    cf_expected:     document.getElementById('expected').value.trim(),
    cf_actual:       document.getElementById('actual').value.trim(),
    cf_files:        document.getElementById('files').value.trim(),
  });
}

async function restoreState() {
  const saved = await chrome.storage.local.get([
    'cf_project_path', 'cf_intent', 'cf_expected', 'cf_actual', 'cf_files',
  ]);
  if (saved.cf_project_path) document.getElementById('project-path').value = saved.cf_project_path;
  if (saved.cf_intent)       document.getElementById('intent').value       = saved.cf_intent;
  if (saved.cf_expected)     document.getElementById('expected').value     = saved.cf_expected;
  if (saved.cf_actual)       document.getElementById('actual').value       = saved.cf_actual;
  if (saved.cf_files) {
    document.getElementById('files').value = saved.cf_files;
    if (window.renderFileCards) window.renderFileCards(saved.cf_files);
  }
}

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Restore saved fields first so UI is populated immediately
  await restoreState();

  // Check server + detect site in parallel
  await Promise.all([checkServer(), detectSite()]);

  // Mark intent/files as user-edited only after the user actually types —
  // NOT when restoreState() programmatically fills them.
  document.getElementById('intent').addEventListener('input', () => { intentUserEdited = true; });
  document.getElementById('files').addEventListener('input',  () => { filesUserEdited  = true; });

  // Auto-read + analyze when popup opens on an AI site
  if (isOnline && currentSite !== 'unknown') {
    const success = await readConversation();
    if (success && conversationText.length > 100) {
      await analyzeConversation();
    } else {
      // Reading failed — clear stale context from previous sessions so the
      // user doesn't see old data that belongs to a different conversation.
      if (!intentUserEdited) document.getElementById('intent').value = '';
      if (!filesUserEdited) {
        document.getElementById('files').value = '';
        if (window.renderFileCards) window.renderFileCards('');
      }
      // setLog already set by readConversation() failure branch
    }
  } else if (isOnline) {
    setLog('Open Claude, ChatGPT, or Gemini to get started', '');
  }

  // Event listeners
  document.getElementById('btn-read').addEventListener('click', async () => {
    await readConversation();
  });

  document.getElementById('btn-analyze').addEventListener('click', async () => {
    if (!conversationText) { setLog('Read conversation first', 'error'); return; }
    await analyzeConversation();
    await saveState();
  });

  document.getElementById('btn-route').addEventListener('click', async () => {
    await routeAndPaste();
    await saveState();
  });

  document.getElementById('btn-build').addEventListener('click', async () => {
    await buildAndPaste();
    await saveState();
  });

  document.getElementById('btn-investigate').addEventListener('click', async () => {
    await investigateAndPaste();
    await saveState();
  });

  document.getElementById('btn-oneclick').addEventListener('click', async () => {
    setLog('Reading chat...', 'info');
    await readConversation();
    if (!conversationText) return;
    setLog('Analyzing intent...', 'info');
    await analyzeConversation();
    setLog('Building + pasting prompt...', 'info');
    await buildAndPaste(window._convSummary || '');
    await saveState();
  });

  // Auto-save project path as user types
  document.getElementById('project-path').addEventListener('change', saveState);
});

// ── Read conversation from page ───────────────────────────
async function readConversation() {
  const preview = document.getElementById('conv-preview');
  setLog('Reading conversation...', '');
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'read_conversation' });
    if (response && response.conversation) {
      conversationText = response.conversation;
      preview.textContent = conversationText.slice(0, 200) + (conversationText.length > 200 ? '...' : '');
      preview.className = 'has-data';
      setLog('Read ' + conversationText.length + ' chars — analyzing...', 'info');
      return true;
    } else {
      preview.textContent = '';
      setLog('No conversation found on this page', 'error');
      return false;
    }
  } catch (e) {
    preview.textContent = '';
    setLog('Refresh this tab to activate cortexfeed', 'error');
    console.error(e);
    return false;
  }
}

// ── Analyze conversation with local AI ────────────────────
async function analyzeConversation() {
  projectPath = document.getElementById('project-path').value.trim();
  setLog('Analyzing conversation...', 'info');

  // Clear stale values immediately so old context doesn't sit on screen
  // while the fetch is in flight. Only skip if the user typed something
  // themselves this session.
  if (!intentUserEdited) {
    document.getElementById('intent').value = '';
    if (window.autoResizeIntent) window.autoResizeIntent();
  }
  if (!filesUserEdited) {
    document.getElementById('files').value = '';
    if (window.renderFileCards) window.renderFileCards('');
  }

  try {
    const res = await fetch(SERVER + '/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation: conversationText, project_path: projectPath }),
    });
    const data = await res.json();

    if (data.conversation_summary) window._convSummary = data.conversation_summary;

    if (data.status === 'ok') {
      const intentField = document.getElementById('intent');
      // Always overwrite with fresh analysis UNLESS the user manually typed
      // something in this session. This ensures switching conversations updates
      // the "WORKING ON" field instead of showing stale stored intent.
      if (!intentUserEdited) {
        let fresh = data.suggested_intent || data.next_step || data.last_ai_action || '';
        if (fresh) {
          // Strip any "fieldname : " prefix the server might include
          fresh = fresh.replace(/^[\w_]+\s*:\s*/i, '').trim();
          // Keep it to one short phrase (≤70 chars, break at word boundary)
          if (fresh.length > 70) {
            fresh = fresh.slice(0, 70).replace(/\s+\S*$/, '').trim();
          }
          intentField.value = fresh;
          if (window.autoResizeIntent) window.autoResizeIntent();
        }
      }

      const filesField = document.getElementById('files');
      if (!filesUserEdited) {
        if (data.detected_files?.length > 0) {
          detectedFiles = data.detected_files;
          filesField.value = data.detected_files.join(' ');
        } else if (data.likely_files?.length > 0) {
          detectedFiles = data.likely_files;
          filesField.value = data.likely_files.join(' ');
        }
        if (window.renderFileCards) window.renderFileCards(filesField.value);
      }

      setLog('Analyzed — review and hit ROUTE, BUILD, or INVESTIGATE', 'success');
      // Classify task and show routing recommendation
      await classifyAndRoute();
    } else {
      setLog('Analyze failed', 'error');
    }
  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  }
}

// ── Classify task + show route recommendation ─────────────
async function classifyAndRoute() {
  const intent = document.getElementById('intent').value.trim();
  if (!intent && !conversationText) return;

  try {
    const res = await fetch(SERVER + '/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        intent,
        conversation: conversationText.slice(0, 2000),
      }),
    });
    const data = await res.json();

    if (data.status === 'ok') {
      recommendedAI = data.recommended_ai;

      // Show route card
      document.getElementById('route-card').style.display = 'block';
      document.getElementById('route-badge').textContent    = data.task_type.toUpperCase();
      document.getElementById('route-ai-label').textContent = data.ai_display;
      document.getElementById('route-reason').textContent   = data.reason;
      document.getElementById('btn-route').disabled         = false;
    }
  } catch (_) {
    // classify is optional — fail silently
  }
}

// ── Route + paste into the recommended AI tab ─────────────
async function routeAndPaste() {
  const intent   = document.getElementById('intent').value.trim();
  const expected = document.getElementById('expected').value.trim();
  const actual   = document.getElementById('actual').value.trim();
  const filesRaw = document.getElementById('files').value.trim();
  projectPath    = document.getElementById('project-path').value.trim();

  const TARGET_LABELS = {
    claude:  'Claude by Anthropic',
    chatgpt: 'OpenAI ChatGPT',
    gemini:  'Google Gemini',
  };
  const target = TARGET_LABELS[recommendedAI] || 'Claude by Anthropic';
  const files  = filesRaw ? filesRaw.split(' ').filter(Boolean) : [];

  setLog('Building prompt for ' + target + '...', 'info');

  try {
    const buildRes = await fetch(SERVER + '/build-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation:         conversationText,
        intent, expected, actual, files, target,
        project_path:         projectPath,
        conversation_summary: window._convSummary || '',
      }),
    });
    const buildData = await buildRes.json();

    if (!buildData.status === 'ok' || !buildData.prompt) {
      setLog('Build failed', 'error');
      return;
    }

    // Delegate tab routing to background (handles find/open + paste)
    setLog('Routing to ' + target + '...', 'info');
    chrome.runtime.sendMessage({
      action: 'route_and_paste',
      ai:     recommendedAI,
      prompt: buildData.prompt,
    }, () => {
      setLog('Routed to ' + target + ' and pasted!', 'success');
    });

  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  }
}

// ── Investigate + paste structured prompt ─────────────────
async function investigateAndPaste() {
  projectPath = document.getElementById('project-path').value.trim();
  const intent = document.getElementById('intent').value.trim();

  if (!conversationText && !intent) {
    setLog('Read conversation first', 'error');
    return;
  }

  const projectName = projectPath
    ? projectPath.replace(/\\/g, '/').split('/').filter(Boolean).pop() || 'project'
    : 'project';

  const request_text = intent || conversationText.slice(0, 300);

  const btn = document.getElementById('btn-investigate');
  btn.disabled = true;
  btn.querySelector('i').className = 'ti ti-loader spinning';
  setLog('Running investigation...', 'info');

  try {
    const res = await fetch(SERVER + '/investigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        request:      request_text,
        project_name: projectName,
        project_root: projectPath || undefined,
      }),
    });

    const data = await res.json();

    if (data.status === 'ok') {
      const panel = document.getElementById('invest-result');
      panel.classList.add('visible');

      const facts   = data.facts      || [];
      const hyps    = data.hypotheses || [];
      const summary = data.summary    || {};
      const evidence = typeof summary === 'string'
        ? summary.split('\n').filter(Boolean)
        : Object.entries(summary).map(([k, v]) => `${k}: ${v}`).filter(Boolean);

      document.getElementById('inv-facts').textContent    = facts.length;
      document.getElementById('inv-hyps').textContent     = hyps.length;
      document.getElementById('inv-evidence').textContent = facts.length || evidence.length;

      const hypList = document.getElementById('inv-hyp-list');
      hypList.innerHTML = hyps.length > 0
        ? hyps.slice(0, 3).map(h => `<div class="invest-hyp-item">→ ${h.statement}</div>`).join('')
        : '<div style="color:#2a5a3a;font-size:10px;">No hypotheses — run with mistral model</div>';

      if (data.prompt) {
        await chrome.runtime.sendMessage({ action: 'paste_to_active_tab', prompt: data.prompt });
        setLog('Investigation prompt pasted!', 'success');
      } else {
        setLog('Investigation done — no prompt returned', 'error');
      }
    } else {
      setLog('Investigation failed: ' + (data.error || 'unknown'), 'error');
    }
  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.querySelector('i').className = 'ti ti-microscope';
  }
}

// ── Build prompt + paste into chat ────────────────────────
async function buildAndPaste(convSummary = '') {
  const intent   = document.getElementById('intent').value.trim();
  const expected = document.getElementById('expected').value.trim();
  const actual   = document.getElementById('actual').value.trim();
  const filesRaw = document.getElementById('files').value.trim();
  const target   = document.getElementById('target').value;
  projectPath    = document.getElementById('project-path').value.trim();

  if (!intent && !conversationText) {
    setLog('Add a description or read the conversation first', 'error');
    return;
  }

  const files = filesRaw ? filesRaw.split(' ').filter(Boolean) : [];
  setLog('Building prompt...', '');

  try {
    const res = await fetch(SERVER + '/build-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation:         conversationText,
        intent,
        expected,
        actual,
        files,
        target,
        project_path:         projectPath,
        conversation_summary: convSummary || window._convSummary || '',
      }),
    });
    const data = await res.json();

    if (data.status === 'ok' && data.prompt) {
      await chrome.runtime.sendMessage({ action: 'paste_to_active_tab', prompt: data.prompt });
      setLog('Prompt pasted into chat!', 'success');
    } else {
      setLog('Server error', 'error');
    }
  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  }
}

// ── Server check ──────────────────────────────────────────
async function checkServer() {
  const statusEl = document.getElementById('status');
  const statusDot = document.getElementById('status-dot');
  const statusWrap = statusEl.parentElement;

  try {
    const res  = await fetch(SERVER + '/ping');
    const data = await res.json();
    if (data.status === 'ok') {
      isOnline = true;
      statusEl.textContent = 'ONLINE';
      statusWrap.classList.add('online');
      statusDot.style.background = '#00d47a';
      document.getElementById('btn-build').disabled       = false;
      document.getElementById('btn-investigate').disabled = false;
      document.getElementById('btn-oneclick').disabled    = false;
      document.getElementById('btn-analyze').disabled     = false;
      document.getElementById('model-label').textContent  =
        'MODEL: ' + (data.model || '—').toUpperCase();
      setLog('Click BUILD + PASTE to get started', '');
    }
  } catch (e) {
    isOnline = false;
    statusEl.textContent = 'OFFLINE';
    statusWrap.classList.remove('online');
    statusDot.style.background = '#ff4444';
    setLog('run: python server.py', 'error');
  }
}

// ── Detect current AI site ────────────────────────────────
async function detectSite() {
  const target = document.getElementById('target');
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url || '';
    if (url.includes('claude.ai')) {
      target.value = 'Claude by Anthropic';
      currentSite = 'claude';
    } else if (url.includes('chatgpt.com')) {
      target.value = 'OpenAI ChatGPT';
      currentSite = 'chatgpt';
    } else if (url.includes('gemini.google.com')) {
      target.value = 'Google Gemini';
      currentSite = 'gemini';
    } else {
      currentSite = 'unknown';
    }
  } catch (e) {
    currentSite = 'unknown';
  }
  return currentSite;
}

// ── Repo Intel ────────────────────────────────────────────
function toggleRepoIntel() {
  const body   = document.getElementById('repo-intel-body');
  const toggle = document.getElementById('repo-intel-toggle');
  const open   = body.style.display === 'none';
  body.style.display  = open ? 'block' : 'none';
  toggle.textContent  = open ? '▲ CLOSE' : '▼ OPEN';
}

async function askRepoIntel() {
  const question = document.getElementById('repo-question').value.trim();
  projectPath    = document.getElementById('project-path').value.trim();

  if (!question)   { setLog('Enter a question first', 'error'); return; }
  if (!projectPath){ setLog('Set project path first', 'error'); return; }

  const btn = document.getElementById('btn-repo-ask');
  btn.disabled = true;
  btn.innerHTML = '<i class="ti ti-loader spinning"></i> Asking...';
  setLog('Querying repo intelligence...', 'info');

  try {
    const res = await fetch(SERVER + '/repo-intel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, project_path: projectPath }),
    });
    const data = await res.json();

    if (data.status === 'ok') {
      const answerBox = document.getElementById('repo-answer');
      answerBox.style.display = 'block';
      document.getElementById('repo-capability').textContent =
        data.capability.toUpperCase().replace(/_/g, ' ');
      document.getElementById('repo-answer-text').textContent = data.answer;
      document.getElementById('repo-confidence').textContent  =
        'confidence: ' + (data.confidence * 100).toFixed(0) + '%';
      setLog('Repo intel answered', 'success');
    } else {
      setLog('Error: ' + (data.error || 'unknown'), 'error');
    }
  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  } finally {
    btn.disabled  = false;
    btn.innerHTML = '<i class="ti ti-send"></i> Ask';
  }
}

// ── Helpers ───────────────────────────────────────────────
function setLog(msg, type) {
  const log = document.getElementById('log');
  if (log) { log.textContent = msg; log.className = type; }
}

function copyField(id) {
  const el = document.getElementById(id);
  if (el && el.value) {
    navigator.clipboard.writeText(el.value);
    setLog('Copied!', 'success');
  }
}
