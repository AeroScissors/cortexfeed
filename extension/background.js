/**
 * background.js — cortexfeed service worker
 *
 * Alt+C         → build + paste into the CURRENT AI tab (no popup)
 * Alt+Shift+C   → classify task, find/open the BEST AI tab, paste there
 *
 * All paste operations use chrome.scripting.executeScript so they work
 * even if the content script hasn't been injected yet (e.g. after a
 * fresh page load or after the extension was reloaded).
 */

const SERVER = 'http://127.0.0.1:5050';

const AI_URLS = {
  claude:  'https://claude.ai',
  chatgpt: 'https://chatgpt.com',
  gemini:  'https://gemini.google.com',
};

const AI_PATTERNS = {
  claude:  '*://claude.ai/*',
  chatgpt: '*://chatgpt.com/*',
  gemini:  '*://gemini.google.com/*',
};

const TARGET_LABELS = {
  claude:  'Claude by Anthropic',
  chatgpt: 'OpenAI ChatGPT',
  gemini:  'Google Gemini',
};


// ── Self-contained paste function (injected into page) ────
// IMPORTANT: this function must NOT reference any outer scope.
// chrome.scripting serialises it as a string and re-evaluates it
// inside the target page. All logic must be inlined.

function injectAndPaste(text) {
  /* ---- toast ---- */
  function showToast(msg) {
    const old = document.getElementById('cortexfeed-toast');
    if (old) old.remove();
    const t = document.createElement('div');
    t.id = 'cortexfeed-toast';
    t.innerText = msg;
    t.style.cssText = [
      'position:fixed','bottom:24px','right:24px',
      'background:#1a1a2e','color:#00d4ff',
      'border:1px solid #00d4ff',
      'padding:12px 20px','border-radius:8px',
      'font-family:monospace','font-size:13px',
      'z-index:999999',
      'box-shadow:0 4px 20px rgba(0,212,255,0.3)',
    ].join(';');
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3500);
  }

  /* ---- find the chat input ---- */
  function findInput() {
    const host = location.hostname;

    if (host.includes('claude.ai')) {
      return (
        document.querySelector('[contenteditable="true"][data-lexical-editor]') ||
        document.querySelector('[contenteditable="true"]')
      );
    }

    if (host.includes('chatgpt.com')) {
      return (
        document.querySelector('#prompt-textarea') ||
        document.querySelector('textarea[placeholder]') ||
        document.querySelector('[contenteditable="true"]')
      );
    }

    if (host.includes('gemini.google.com')) {
      // Gemini puts the Quill editor inside <rich-textarea>'s shadow root
      const rt = document.querySelector('rich-textarea');
      if (rt) {
        const shadow = rt.shadowRoot;
        if (shadow) {
          const inner =
            shadow.querySelector('.ql-editor[contenteditable="true"]') ||
            shadow.querySelector('[contenteditable="true"]');
          if (inner) return inner;
        }
        // No shadow root exposed — try light DOM children
        const inner =
          rt.querySelector('.ql-editor') ||
          rt.querySelector('[contenteditable="true"]');
        if (inner) return inner;
      }
      // Flat DOM fallbacks
      return (
        document.querySelector('.ql-editor[contenteditable="true"]') ||
        document.querySelector('[data-placeholder][contenteditable="true"]') ||
        document.querySelector('div[contenteditable="true"][role="textbox"]') ||
        [...document.querySelectorAll('[contenteditable="true"]')].at(-1) ||
        null
      );
    }

    return null;
  }

  /* ---- paste strategies ---- */
  function tryTextarea(el, txt) {
    try {
      const setter = Object.getOwnPropertyDescriptor(
        HTMLTextAreaElement.prototype, 'value'
      ).set;
      setter.call(el, txt);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    } catch (_) { return false; }
  }

  function tryExecCommand(el, txt) {
    try {
      el.focus();
      const range = document.createRange();
      range.selectNodeContents(el);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      const ok = document.execCommand('insertText', false, txt);
      el.dispatchEvent(new InputEvent('input', {
        bubbles: true, data: txt, inputType: 'insertText',
      }));
      return ok;
    } catch (_) { return false; }
  }

  function tryClipboardEvent(el, txt) {
    try {
      el.focus();
      const dt = new DataTransfer();
      dt.setData('text/plain', txt);
      dt.setData('text/html', txt.replace(/\n/g, '<br>'));
      el.dispatchEvent(new ClipboardEvent('paste', {
        clipboardData: dt, bubbles: true, cancelable: true,
      }));
      return true;
    } catch (_) { return false; }
  }

  function tryDirectDOM(el, txt) {
    try {
      el.focus();
      el.innerText = txt;
      el.dispatchEvent(new InputEvent('input', { bubbles: true, data: txt }));
      return true;
    } catch (_) { return false; }
  }

  /* ---- orchestrate ---- */
  const input = findInput();

  if (!input) {
    showToast('cortexfeed: no input found — copied! Ctrl+V to paste');
    navigator.clipboard.writeText(text).catch(() => {});
    return;
  }

  if (input.tagName === 'TEXTAREA') {
    if (tryTextarea(input, text)) {
      showToast('cortexfeed — prompt pasted!');
      return;
    }
  }

  if (tryExecCommand(input, text)) {
    showToast('cortexfeed — prompt pasted!');
    return;
  }

  if (tryClipboardEvent(input, text)) {
    showToast('cortexfeed — prompt pasted!');
    return;
  }

  if (tryDirectDOM(input, text)) {
    showToast('cortexfeed — prompt pasted!');
    return;
  }

  showToast('cortexfeed: all strategies failed — copied! Ctrl+V');
  navigator.clipboard.writeText(text).catch(() => {});
}


// ── Paste via scripting API (bypasses content-script timing) ─

async function pasteIntoTab(tabId, prompt) {
  await chrome.scripting.executeScript({
    target: { tabId },
    func: injectAndPaste,
    args: [prompt],
  });
}


// ── Context menu (Feature 5: right-click "Send to cortexfeed") ──

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'cortexfeed-add-context',
    title: 'Send to cortexfeed',
    contexts: ['selection'],
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === 'cortexfeed-add-context' && info.selectionText) {
    chrome.storage.local.set({ cf_selected_text: info.selectionText.trim() });
  }
});


// ── Keyboard shortcuts ────────────────────────────────────

chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'build-and-paste') {
    await buildAndPasteCurrentTab();
  } else if (command === 'route-and-paste') {
    await routeAndPaste();
  }
});


// ── Popup → background messages ───────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'route_and_paste') {
    handleRouteAndPaste(message.ai, message.prompt)
      .then(() => sendResponse({ status: 'ok' }))
      .catch((e) => sendResponse({ status: 'error', error: String(e) }));
    return true;
  }

  // popup.js BUILD+PASTE and INVESTIGATE+PASTE use this
  if (message.action === 'paste_to_active_tab') {
    chrome.tabs.query({ active: true, currentWindow: true })
      .then(([tab]) => {
        if (!tab) { sendResponse({ status: 'error', error: 'no tab' }); return; }
        return pasteIntoTab(tab.id, message.prompt);
      })
      .then(() => sendResponse({ status: 'ok' }))
      .catch((e) => sendResponse({ status: 'error', error: String(e) }));
    return true;
  }
});


// ── Alt+C — build + paste in the current AI tab ──────────

async function buildAndPasteCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const url = tab.url || '';
  if (!isAISite(url)) return;

  const target = targetFromUrl(url);

  try {
    // Read conversation via content script (still needed for text extraction)
    const readResp = await chrome.tabs.sendMessage(tab.id, { action: 'read_conversation' });
    if (!readResp?.conversation) return;
    const conversation = readResp.conversation;

    const saved = await chrome.storage.local.get([
      'cf_project_path', 'cf_intent', 'cf_expected', 'cf_actual', 'cf_files',
    ]);
    const projectPath = saved.cf_project_path || '';
    let intent  = saved.cf_intent || '';
    let files   = saved.cf_files  ? saved.cf_files.split(' ').filter(Boolean) : [];
    let summary = '';

    try {
      const analyzeData = await postJSON('/analyze', { conversation, project_path: projectPath });
      summary = analyzeData.conversation_summary || '';
      if (!intent && analyzeData.suggested_intent) intent = analyzeData.suggested_intent;
      if (files.length === 0 && analyzeData.detected_files?.length > 0) files = analyzeData.detected_files;
    } catch (_) {}

    const buildData = await postJSON('/build-prompt', {
      conversation, intent,
      expected:             saved.cf_expected || '',
      actual:               saved.cf_actual   || '',
      files, target, project_path: projectPath,
      conversation_summary: summary,
    });

    if (buildData.status === 'ok' && buildData.prompt) {
      await pasteIntoTab(tab.id, buildData.prompt);
    }
  } catch (e) {
    console.error('[cortexfeed Alt+C]', e);
  }
}


// ── Alt+Shift+C — classify + route to best AI tab ────────

async function routeAndPaste() {
  const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  let conversation = '';
  if (activeTab && isAISite(activeTab.url || '')) {
    try {
      const r = await chrome.tabs.sendMessage(activeTab.id, { action: 'read_conversation' });
      if (r?.conversation) conversation = r.conversation;
    } catch (_) {}
  }

  const saved = await chrome.storage.local.get([
    'cf_project_path', 'cf_intent', 'cf_expected', 'cf_actual', 'cf_files',
  ]);
  const projectPath = saved.cf_project_path || '';
  let intent  = saved.cf_intent || '';
  let files   = saved.cf_files  ? saved.cf_files.split(' ').filter(Boolean) : [];
  let summary = '';

  let recommendedAI = 'claude';
  try {
    const classifyData = await postJSON('/classify', {
      intent,
      conversation: conversation.slice(0, 2000),
    });
    if (classifyData.status === 'ok') recommendedAI = classifyData.recommended_ai;
  } catch (_) {}

  if (conversation) {
    try {
      const analyzeData = await postJSON('/analyze', { conversation, project_path: projectPath });
      summary = analyzeData.conversation_summary || '';
      if (!intent && analyzeData.suggested_intent) intent = analyzeData.suggested_intent;
      if (files.length === 0 && analyzeData.detected_files?.length > 0) files = analyzeData.detected_files;
    } catch (_) {}
  }

  const target = TARGET_LABELS[recommendedAI] || 'Claude by Anthropic';
  let prompt = '';
  try {
    const buildData = await postJSON('/build-prompt', {
      conversation, intent,
      expected:             saved.cf_expected || '',
      actual:               saved.cf_actual   || '',
      files, target, project_path: projectPath,
      conversation_summary: summary,
    });
    if (buildData.status === 'ok') prompt = buildData.prompt;
  } catch (_) {}

  if (!prompt) return;

  await handleRouteAndPaste(recommendedAI, prompt);
}


// ── Tab routing — find/open the right AI tab + paste ─────

async function handleRouteAndPaste(ai, prompt) {
  const existingTabs = await chrome.tabs.query({ url: AI_PATTERNS[ai] });

  if (existingTabs.length > 0) {
    const t = existingTabs[0];
    await chrome.tabs.update(t.id, { active: true });
    await chrome.windows.update(t.windowId, { focused: true });
    await delay(400);
    await pasteIntoTab(t.id, prompt);
  } else {
    const newTab = await chrome.tabs.create({ url: AI_URLS[ai] });
    await waitForTabAndPaste(newTab.id, prompt);
  }
}

function waitForTabAndPaste(tabId, prompt) {
  return new Promise((resolve) => {
    // Safety timeout: if tab never fires 'complete', bail after 15s
    const timeout = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, 15000);

    const listener = (id, changeInfo) => {
      if (id === tabId && changeInfo.status === 'complete') {
        clearTimeout(timeout);
        chrome.tabs.onUpdated.removeListener(listener);
        delay(1500).then(async () => {
          try { await pasteIntoTab(tabId, prompt); } catch (_) {}
          resolve();
        });
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
  });
}


// ── Helpers ───────────────────────────────────────────────

function isAISite(url) {
  return url.includes('claude.ai') || url.includes('chatgpt.com') || url.includes('gemini.google.com');
}

function targetFromUrl(url) {
  if (url.includes('claude.ai'))         return 'Claude by Anthropic';
  if (url.includes('chatgpt.com'))       return 'OpenAI ChatGPT';
  if (url.includes('gemini.google.com')) return 'Google Gemini';
  return 'any AI assistant';
}

async function postJSON(path, body) {
  const res = await fetch(SERVER + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
