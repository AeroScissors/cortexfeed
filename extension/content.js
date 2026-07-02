const SITE = (() => {
  const host = window.location.hostname;
  if (host.includes('claude.ai')) return 'claude';
  if (host.includes('chatgpt.com')) return 'chatgpt';
  if (host.includes('gemini.google.com')) return 'gemini';
  return 'unknown';
})();

// ── Read conversation ─────────────────────────────────────

function readConversation() {
  let messages = [];

  if (SITE === 'claude') {
    // Try multiple selector strategies in order of reliability
    const selectors = [
      '[data-testid^="conversation-turn"]',   // numbered turns (current)
      '[data-testid="conversation-turn"]',     // unnumbered turns
      '[class*="claude-message"]',
      '[class*="human-turn"]',
      '.font-claude-message',
      '.human-turn',
    ];
    const combined = selectors.join(', ');
    const seen = new Set();
    document.querySelectorAll(combined).forEach(el => {
      if (!seen.has(el)) {
        seen.add(el);
        const text = el.innerText.trim();
        if (text && text.length > 5) messages.push(text);
      }
    });
  }

  else if (SITE === 'chatgpt') {
    const selectors = [
      '[data-message-author-role]',
      '[class*="prose"]',
      '.markdown',
      '[class*="message"]'
    ];
    for (const sel of selectors) {
      const els = document.querySelectorAll(sel);
      if (els.length > 0) {
        els.forEach(el => {
          const role = el.getAttribute('data-message-author-role') || 'message';
          const text = el.innerText.trim();
          if (text && text.length > 10) {
            messages.push('[' + role.toUpperCase() + ']: ' + text);
          }
        });
        break;
      }
    }
  }

  else if (SITE === 'gemini') {
    document.querySelectorAll(
      'model-response, user-query, .query-text, .response-content, ' +
      'message-content, .conversation-container [class*="message"]'
    ).forEach(el => {
      const tag = el.tagName ? el.tagName.toLowerCase() : '';
      const role = (tag === 'user-query' || el.classList.contains('query-text')) ? 'USER' : 'GEMINI';
      const text = el.innerText.trim();
      if (text && text.length > 5) messages.push('[' + role + ']: ' + text);
    });
  }

  return messages.join('\n\n---\n\n');
}

// ── Find the active chat input ────────────────────────────

function findInput() {
  if (SITE === 'claude') {
    return (
      document.querySelector('[contenteditable="true"][data-lexical-editor]') ||
      document.querySelector('[contenteditable="true"]')
    );
  }

  if (SITE === 'chatgpt') {
    return (
      document.querySelector('#prompt-textarea') ||
      document.querySelector('textarea[placeholder]') ||
      document.querySelector('[contenteditable="true"]')
    );
  }

  if (SITE === 'gemini') {
    // Gemini wraps its Quill editor inside <rich-textarea>'s SHADOW DOM.
    // document.querySelector() cannot pierce shadow roots — we must do it manually.
    const richTextarea = document.querySelector('rich-textarea');
    if (richTextarea) {
      // open shadow root
      const shadow = richTextarea.shadowRoot;
      if (shadow) {
        const inner =
          shadow.querySelector('.ql-editor[contenteditable="true"]') ||
          shadow.querySelector('[contenteditable="true"]');
        if (inner) return inner;
      }
      // shadow not exposed — try children directly
      const inner =
        richTextarea.querySelector('.ql-editor') ||
        richTextarea.querySelector('[contenteditable="true"]');
      if (inner) return inner;
    }

    // Flat DOM fallbacks (older Gemini builds without shadow root)
    return (
      document.querySelector('.ql-editor[contenteditable="true"]')         ||
      document.querySelector('[data-placeholder][contenteditable="true"]') ||
      document.querySelector('div[contenteditable="true"][role="textbox"]')||
      [...document.querySelectorAll('[contenteditable="true"]')].at(-1)    ||
      null
    );
  }

  return null;
}

// ── Paste strategies ──────────────────────────────────────

function tryPasteIntoTextarea(el, text) {
  try {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    setter.call(el, text);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  } catch (_) {
    return false;
  }
}

function tryExecCommand(el, text) {
  try {
    el.focus();
    // Select all content inside the element (not the whole page)
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    // insertText replaces the selection
    const ok = document.execCommand('insertText', false, text);
    // Quill fires its own 'text-change' via MutationObserver, but also
    // needs an 'input' event to sync its internal delta model.
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text, inputType: 'insertText' }));
    return ok;
  } catch (_) {
    return false;
  }
}

function tryClipboardEvent(el, text) {
  try {
    el.focus();
    const dt = new DataTransfer();
    dt.setData('text/plain', text);
    dt.setData('text/html', text.replace(/\n/g, '<br>'));
    el.dispatchEvent(new ClipboardEvent('paste', {
      clipboardData: dt,
      bubbles: true,
      cancelable: true,
    }));
    return true;
  } catch (_) {
    return false;
  }
}

function tryDirectDOM(el, text) {
  try {
    el.focus();
    el.innerText = text;
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }));
    return true;
  } catch (_) {
    return false;
  }
}

// ── Paste orchestrator ────────────────────────────────────

function pastePrompt(text) {
  const input = findInput();

  if (!input) {
    // No input found — copy to clipboard so user can paste manually
    navigator.clipboard.writeText(text)
      .then(() => showToast('No input found — copied! Paste with Ctrl+V'))
      .catch(() => showToast('Could not find input or copy to clipboard'));
    return;
  }

  // TEXTAREA: use native React-compatible setter
  if (input.tagName === 'TEXTAREA') {
    if (tryPasteIntoTextarea(input, text)) {
      showToast('cortexfeed — prompt pasted!');
      return;
    }
  }

  // CONTENTEDITABLE: cascade through strategies
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

  // All strategies failed — clipboard fallback
  navigator.clipboard.writeText(text)
    .then(() => showToast('Paste strategies failed — copied! Press Ctrl+V'))
    .catch(() => showToast('Could not paste'));
}

// ── Toast ─────────────────────────────────────────────────

function showToast(message) {
  const existing = document.getElementById('cortexfeed-toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.id = 'cortexfeed-toast';
  toast.innerText = message;
  toast.style.cssText = [
    'position:fixed', 'bottom:24px', 'right:24px',
    'background:#1a1a2e', 'color:#00d4ff',
    'border:1px solid #00d4ff',
    'padding:12px 20px', 'border-radius:8px',
    'font-family:monospace', 'font-size:13px',
    'z-index:999999',
    'box-shadow:0 4px 20px rgba(0,212,255,0.3)',
    'transition:opacity 0.3s',
  ].join(';');
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Message listener ──────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'read_conversation') {
    const conversation = readConversation();
    sendResponse({ conversation, site: SITE });
    return true;
  }
  if (message.action === 'paste_prompt') {
    pastePrompt(message.prompt);
    sendResponse({ status: 'pasted' });
    return true;
  }
  return true;
});
