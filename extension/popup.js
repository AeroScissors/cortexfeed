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
let checkedFiles         = new Set();
let _currentFilesList    = [];

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
  if (saved.cf_intent) {
    document.getElementById('intent').value = saved.cf_intent;
    const card = document.getElementById('intent-card');
    if (card) card.style.display = 'flex';
  }
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

  // Check for right-click selected text + load prompt history
  await checkSelectedText();
  const histStored = await chrome.storage.local.get(['cf_history']);
  if (histStored.cf_history?.length) renderHistory(histStored.cf_history);

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

  // BUILD + PASTE: full pipeline in one click
  document.getElementById('btn-build').addEventListener('click', async () => {
    setLog('Reading conversation...', 'info');
    const ok = await readConversation();
    if (ok && conversationText.length > 100) {
      setLog('Analyzing...', 'info');
      await analyzeConversation();
    }
    // If no project path is set, ask before building so files get attached
    const currentPath = document.getElementById('project-path').value.trim();
    if (!currentPath) {
      const chosenPath = await promptForProjectPath();
      if (chosenPath) {
        document.getElementById('project-path').value = chosenPath;
        projectPath = chosenPath;
        setLog('Attaching files...', 'info');
        await analyzeConversation();
        await saveState();
      }
    }
    await buildAndPaste(window._convSummary || '');
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
      const intentCard  = document.getElementById('intent-card');
      // Always overwrite with fresh analysis UNLESS the user manually typed
      // something in this session.
      if (!intentUserEdited) {
        let fresh = data.suggested_intent || data.next_step || data.last_ai_action || '';
        if (fresh) {
          fresh = fresh.replace(/^[\w_]+\s*:\s*/i, '').trim();
          // Guard: if the AI returned raw JSON instead of a string, extract from it
          if (fresh.startsWith('{')) {
            try {
              const parsed = JSON.parse(fresh);
              fresh = parsed.suggested_intent || parsed.next_step || parsed.last_ai_action || '';
            } catch (_) {
              // Truncated JSON — try to pull suggested_intent value out by regex
              const m = fresh.match(/"suggested_intent"\s*:\s*"([^"]{10,})"/);
              fresh = m ? m[1] : '';
            }
          }
          if (fresh) {
            intentField.value = fresh;
            if (window.autoResizeIntent) window.autoResizeIntent();
          }
        }
      }
      // Show intent card whenever there's something to display/edit
      if (intentField.value && intentCard) {
        intentCard.style.display = 'flex';
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

        // Show warning if files detected but no project path set
        const noPathWarn = document.getElementById('no-path-warning');
        const filesCount = document.getElementById('files-count');
        if (noPathWarn) {
          const hasFiles = detectedFiles.length > 0;
          const hasPath  = !!projectPath;
          noPathWarn.style.display = (hasFiles && !hasPath) ? 'block' : 'none';
          if (filesCount) {
            filesCount.textContent = hasFiles
              ? (hasPath ? `${detectedFiles.length} file${detectedFiles.length > 1 ? 's' : ''} — contents included` : `${detectedFiles.length} detected — set path to include`)
              : 'auto-detected';
            filesCount.style.color = hasFiles && hasPath ? 'rgba(0,212,120,0.6)' : 'rgba(255,255,255,0.18)';
          }
        }
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
      recommendedAI    = data.recommended_ai;
      window._taskType = data.task_type;

      // Show task type badge on intent card
      const badge = document.getElementById('intent-task-badge');
      if (badge) badge.textContent = data.task_type.toUpperCase();

      // Route card (hidden but kept for JS compat)
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

    if (buildData.status !== 'ok' || !buildData.prompt) {
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
        window._pendingExtraContext = null;
        showPreviewModal(data.prompt);
        setLog('Review and paste when ready', 'info');
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

// ── GitHub Context (Feature 3) ────────────────────────────
async function getGitHubContext() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url || '';
    const match = url.match(/github\.com\/([^/]+)\/([^/?\s#]+)/);
    if (!match) return null;

    const [, owner, repo] = match;
    const repoRes = await fetch(`https://api.github.com/repos/${owner}/${repo}`);
    if (!repoRes.ok) return null;
    const repoData = await repoRes.json();
    const branch = repoData.default_branch || 'main';

    let readme = '';
    try {
      const r = await fetch(`https://raw.githubusercontent.com/${owner}/${repo}/${branch}/README.md`);
      if (r.ok) readme = (await r.text()).slice(0, 2000);
    } catch (_) {}

    let fileTree = '';
    try {
      const t = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`);
      if (t.ok) {
        const td = await t.json();
        if (td.tree) {
          fileTree = td.tree
            .filter(f => f.type === 'blob' && !f.path.includes('node_modules'))
            .map(f => f.path)
            .slice(0, 60)
            .join('\n');
        }
      }
    } catch (_) {}

    const card = document.getElementById('github-card');
    const nameEl = document.getElementById('github-repo-name');
    if (card && nameEl) { nameEl.textContent = `${owner}/${repo}`; card.style.display = 'flex'; }

    return { owner, repo, branch, readme, fileTree };
  } catch (_) { return null; }
}

// ── Prompt History (Feature 4) ────────────────────────────
async function savePromptHistory(prompt) {
  const s = await chrome.storage.local.get(['cf_history']);
  const history = s.cf_history || [];
  history.unshift({ prompt, ts: Date.now() });
  if (history.length > 5) history.length = 5;
  await chrome.storage.local.set({ cf_history: history });
  renderHistory(history);
}

function renderHistory(history) {
  const section = document.getElementById('history-section');
  const list    = document.getElementById('history-list');
  if (!section || !list || !history.length) return;
  section.style.display = 'block';
  list.innerHTML = history.map((item, i) => {
    const preview = item.prompt.slice(0, 80).replace(/</g, '&lt;');
    const ago = timeAgo(item.ts);
    return `<div class="history-item">
      <div class="history-body">
        <div class="history-text">${preview}…</div>
        <div class="history-meta">${ago}</div>
      </div>
      <button class="history-copy" data-history-index="${i}" title="Copy"><i class="ti ti-copy"></i></button>
    </div>`;
  }).join('');
}

window.copyHistory = async function(i) {
  const s = await chrome.storage.local.get(['cf_history']);
  const h = (s.cf_history || [])[i];
  if (h) { await navigator.clipboard.writeText(h.prompt); setLog('Copied!', 'success'); }
};

function timeAgo(ts) {
  const m = Math.floor((Date.now() - ts) / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ── Selected text from right-click (Feature 5) ───────────
async function checkSelectedText() {
  const s = await chrome.storage.local.get(['cf_selected_text']);
  if (s.cf_selected_text) {
    const card = document.getElementById('selected-text-card');
    const prev = document.getElementById('selected-text-preview');
    if (card && prev) {
      const t = s.cf_selected_text;
      prev.textContent = t.slice(0, 60) + (t.length > 60 ? '...' : '');
      card.style.display = 'flex';
    }
  }
}

window.clearSelectedText = async function() {
  await chrome.storage.local.remove('cf_selected_text');
  const card = document.getElementById('selected-text-card');
  if (card) card.style.display = 'none';
};

// ── Build prompt + paste into chat ────────────────────────
async function buildAndPaste(convSummary = '') {
  const intent   = document.getElementById('intent').value.trim();
  const expected = document.getElementById('expected').value.trim();
  const actual   = document.getElementById('actual').value.trim();
  const filesRaw = document.getElementById('files').value.trim();
  const target   = document.getElementById('target').value;
  projectPath    = document.getElementById('project-path').value.trim();

  // Feature 5: selected text from right-click
  const stored = await chrome.storage.local.get(['cf_selected_text']);
  const extraContext = stored.cf_selected_text || '';

  // Feature 3: GitHub context
  const githubCtx = await getGitHubContext();

  if (!intent && !conversationText && !githubCtx && !extraContext) {
    setLog('Add a description or read the conversation first', 'error');
    return;
  }

  // Use the user-controlled checklist; fall back to raw field if no checklist state
  const files = checkedFiles.size > 0
    ? [...checkedFiles]
    : (filesRaw ? filesRaw.split(' ').filter(Boolean) : []);
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
        task_type:            window._taskType || 'general',  // Feature 2
        github_context:       githubCtx,                       // Feature 3
        extra_context:        extraContext,                     // Feature 5
      }),
    });
    const data = await res.json();

    if (data.status === 'ok' && data.prompt) {
      // Stash extra-context state so confirmPaste can clean it up after pasting
      window._pendingExtraContext = extraContext || null;
      showPreviewModal(data.prompt, data.files_loaded || 0);
    } else {
      setLog('Server error', 'error');
    }
  } catch (e) {
    setLog('Could not reach server', 'error');
    console.error(e);
  }
}

// ── Prompt preview modal ──────────────────────────────────
function showPreviewModal(prompt, filesLoaded) {
  const modal    = document.getElementById('preview-modal');
  const textarea = document.getElementById('preview-text');
  const chars    = document.getElementById('preview-chars');
  if (!modal || !textarea) return;
  textarea.value = prompt;
  let charLabel = prompt.length.toLocaleString() + ' chars';
  if (filesLoaded > 0) {
    charLabel += ` · ${filesLoaded} file${filesLoaded > 1 ? 's' : ''} attached`;
  } else if (typeof filesLoaded === 'number' && checkedFiles.size > 0) {
    charLabel += ' · ⚠ files not found — check project path';
  }
  chars.textContent = charLabel;
  modal.style.display = 'flex';
  textarea.focus();
}

function closePreviewModal() {
  const modal = document.getElementById('preview-modal');
  if (modal) modal.style.display = 'none';
}

// ── Project path prompt ───────────────────────────────────
function promptForProjectPath() {
  return new Promise((resolve) => {
    const modal = document.getElementById('path-modal');
    const input = document.getElementById('path-modal-input');
    if (!modal) { resolve(null); return; }

    // Pre-fill with any previously saved path
    const saved = document.getElementById('project-path').value.trim();
    if (saved) input.value = saved;

    modal.style.display = 'flex';
    setTimeout(() => input.focus(), 80);

    function confirm() {
      modal.style.display = 'none';
      cleanup();
      resolve(input.value.trim() || null);
    }
    function skip() {
      modal.style.display = 'none';
      cleanup();
      resolve(null);
    }
    function onKey(e) { if (e.key === 'Enter') confirm(); if (e.key === 'Escape') skip(); }

    function cleanup() {
      document.getElementById('btn-path-confirm').onclick = null;
      document.getElementById('btn-path-skip').onclick    = null;
      input.removeEventListener('keydown', onKey);
    }

    document.getElementById('btn-path-confirm').onclick = confirm;
    document.getElementById('btn-path-skip').onclick    = skip;
    input.addEventListener('keydown', onKey);
  });
}

async function confirmPaste() {
  const prompt = document.getElementById('preview-text').value;
  closePreviewModal();
  await chrome.runtime.sendMessage({ action: 'paste_to_active_tab', prompt });
  setLog('Prompt pasted into chat!', 'success');
  await savePromptHistory(prompt);
  if (window._pendingExtraContext) {
    await chrome.storage.local.remove('cf_selected_text');
    const card = document.getElementById('selected-text-card');
    if (card) card.style.display = 'none';
    window._pendingExtraContext = null;
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
      const offlineCard = document.getElementById('offline-card');
      if (offlineCard) offlineCard.classList.remove('visible');
    }
  } catch (e) {
    isOnline = false;
    statusEl.textContent = 'OFFLINE';
    statusWrap.classList.remove('online');
    statusDot.style.background = '#ff4444';
    setLog('Server offline — see setup steps below', 'error');
    const offlineCard = document.getElementById('offline-card');
    if (offlineCard) offlineCard.classList.add('visible');
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
  if (!log) return;
  if (type === 'success' && msg.toLowerCase().includes('analyzed')) {
    log.innerHTML =
      'Analyzed — review and hit ' +
      '<span style="color:#00d47a">ROUTE</span>, ' +
      '<span style="color:#00d47a">BUILD</span>, or ' +
      '<span style="color:#00d47a">INVESTIGATE</span>';
    log.className = 'success';
    return;
  }
  if (type === 'success' && msg.toLowerCase().includes('pasted')) {
    log.innerHTML = '<span style="color:#00d47a">✓</span> ' + msg;
    log.className = 'success';
    return;
  }
  log.textContent = msg;
  log.className = type || '';
}

function copyField(id) {
  const el = document.getElementById(id);
  if (el && el.value) {
    navigator.clipboard.writeText(el.value);
    setLog('Copied!', 'success');
  }
}

// ── File cards ────────────────────────────────────────────
const EXT_ICONS = {
  dart: 'ti-brand-flutter', py: 'ti-brand-python',
  js: 'ti-brand-javascript', ts: 'ti-brand-typescript',
  json: 'ti-braces', md: 'ti-markdown',
  txt: 'ti-file-text', html: 'ti-html',
  css: 'ti-file-code', yaml: 'ti-file-code', yml: 'ti-file-code',
};

function renderFileCards(filesStr) {
  const container = document.getElementById('files-cards');
  if (!container) return;
  const files = filesStr ? filesStr.split(/\s+/).filter(Boolean) : [];
  if (!files.length) {
    container.innerHTML = '<div class="no-files">Set project path + hit BUILD to auto-detect relevant files</div>';
    checkedFiles = new Set();
    _currentFilesList = [];
    return;
  }
  // Sync checkedFiles: add any new files (checked by default), drop removed ones
  const incoming = new Set(files);
  for (const f of checkedFiles) { if (!incoming.has(f)) checkedFiles.delete(f); }
  files.forEach(f => { if (!checkedFiles.has(f)) checkedFiles.add(f); });
  _currentFilesList = files;
  _renderFileCardsUI(files);
}

function _renderFileCardsUI(files) {
  const container = document.getElementById('files-cards');
  if (!container) return;
  const activeCount = files.filter(f => checkedFiles.has(f)).length;
  const filesCount  = document.getElementById('files-count');
  if (filesCount) {
    const hasPath = !!document.getElementById('project-path').value.trim();
    filesCount.textContent = `${activeCount}/${files.length} included${hasPath ? ' — contents loaded' : ''}`;
    filesCount.style.color = activeCount > 0 ? 'rgba(0,212,120,0.6)' : 'rgba(255,255,255,0.18)';
  }
  container.innerHTML = files.map(f => {
    const included = checkedFiles.has(f);
    const parts = f.split(/[/\\]/);
    const name  = parts.pop();
    const dir   = parts.slice(-2).join('/');
    const ext   = (name.split('.').pop() || '').toLowerCase();
    const icon  = EXT_ICONS[ext] || 'ti-file-code';
    const safe  = f.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    return `<div class="file-card${included ? '' : ' excluded'}">
      <i class="ti ${icon} file-card-icon"></i>
      <div class="file-card-body">
        <div class="file-card-name" title="${safe}">${name}</div>
        <div class="file-card-meta" style="color:rgba(255,255,255,0.2)">${dir}</div>
      </div>
      <button class="file-toggle${included ? '' : ' excluded'}" data-toggle-path="${safe}" title="${included ? 'Exclude from prompt' : 'Include in prompt'}">
        <i class="ti ${included ? 'ti-check' : 'ti-minus'}"></i>
      </button>
      <button class="file-card-copy" data-copy-path="${safe}" title="Copy path">
        <i class="ti ti-copy"></i>
      </button>
    </div>`;
  }).join('');
}

function _toggleFile(path) {
  if (checkedFiles.has(path)) { checkedFiles.delete(path); }
  else { checkedFiles.add(path); }
  _renderFileCardsUI(_currentFilesList);
}

window.renderFileCards = renderFileCards;

// ── Intent auto-resize ────────────────────────────────────
function autoResizeIntent() {
  const el = document.getElementById('intent');
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 96) + 'px';
}
window.autoResizeIntent = autoResizeIntent;

// ── Advanced toggle ───────────────────────────────────────
function toggleAdvanced() {
  const panel = document.getElementById('advanced-panel');
  const label = document.getElementById('adv-label');
  const open  = panel.style.display === 'none';
  panel.style.display = open ? 'flex' : 'none';
  label.textContent   = open ? '···  Hide Advanced  ···' : '···  Advanced  ···';
  if (open) {
    chrome.storage.local.get(['cf_history']).then(s => {
      if (s.cf_history?.length) renderHistory(s.cf_history);
    });
  }
}

// ── UI wiring (runs after DOM is ready) ──────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Intent resize
  const intentEl = document.getElementById('intent');
  if (intentEl) {
    intentEl.addEventListener('input', autoResizeIntent);
    setTimeout(autoResizeIntent, 150);
  }

  // Buttons that were using inline onclick
  document.getElementById('adv-toggle')?.addEventListener('click', toggleAdvanced);
  document.getElementById('btn-clear-selection')?.addEventListener('click', clearSelectedText);
  document.getElementById('btn-copy-project-path')?.addEventListener('click', () => copyField('project-path'));
  document.getElementById('repo-header')?.addEventListener('click', toggleRepoIntel);
  document.getElementById('btn-repo-ask')?.addEventListener('click', askRepoIntel);
  document.getElementById('btn-refresh')?.addEventListener('click', async () => {
    document.getElementById('error-card')?.classList.remove('visible');
    await checkServer();
    const ok = await readConversation();
    if (ok && conversationText && conversationText.length > 100) {
      await analyzeConversation();
    }
  });

  // Preview modal buttons
  document.getElementById('btn-preview-paste')?.addEventListener('click', confirmPaste);
  document.getElementById('btn-preview-cancel')?.addEventListener('click', closePreviewModal);
  document.getElementById('preview-text')?.addEventListener('input', () => {
    const chars = document.getElementById('preview-chars');
    if (chars) chars.textContent = document.getElementById('preview-text').value.length.toLocaleString() + ' chars';
  });

  // Offline card copy command
  document.getElementById('btn-copy-cmd')?.addEventListener('click', () => {
    navigator.clipboard.writeText('python server.py');
    setLog('Copied!', 'success');
  });

  // Event delegation for dynamically generated copy/toggle buttons
  document.addEventListener('click', e => {
    const toggleBtn = e.target.closest('.file-toggle');
    if (toggleBtn?.dataset.togglePath !== undefined) {
      _toggleFile(toggleBtn.dataset.togglePath);
      return;
    }
    const fileBtn = e.target.closest('.file-card-copy');
    if (fileBtn?.dataset.copyPath) {
      navigator.clipboard.writeText(fileBtn.dataset.copyPath);
      setLog('Copied!', 'success');
      return;
    }
    const histBtn = e.target.closest('.history-copy');
    if (histBtn?.dataset.historyIndex !== undefined) {
      copyHistory(parseInt(histBtn.dataset.historyIndex, 10));
    }
  });

  // Error card: show when log says "Could not read" etc.
  const logEl    = document.getElementById('log');
  const errorCard = document.getElementById('error-card');
  if (logEl && errorCard) {
    new MutationObserver(() => {
      const txt = logEl.textContent;
      if (
        txt.includes('Could not read') ||
        txt.includes('Error reading') ||
        txt.includes('Refresh this tab') ||
        txt.includes('No conversation found')
      ) {
        errorCard.classList.add('visible');
      } else if (logEl.classList.contains('success') || logEl.classList.contains('info')) {
        errorCard.classList.remove('visible');
      }
    }).observe(logEl, { childList: true, characterData: true, subtree: true });
  }
});
