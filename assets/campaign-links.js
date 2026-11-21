/* Session-scoped App Store acquisition attribution; no analytics dependencies. */
(() => {
  const book = '76589797-e154-4662-abbd-d4c5c7a38b05';
  const widgets = '3bfae5bb-ea40-4c58-b90f-4d3b7b003fa4';
  const ai = '941c5747-8463-4433-b4b0-e0a8f4c24ca7';
  const pages = { x: book, reddit: book, tiktok: widgets, instagram: widgets,
    website: book, producthunt: ai, bio: book,
    'ai-chatgpt': ai, 'ai-claude': ai, 'ai-perplexity': ai };
  const normalize = value => {
    value = (value || '').toLowerCase();
    if (['chatgpt', 'claude', 'perplexity'].includes(value)) value = 'ai-' + value;
    return Object.hasOwn(pages, value) ? value : '';
  };
  const query = new URLSearchParams(location.search);
  let channel = normalize(query.get('utm_source')) || normalize(query.get('ref'));
  if (!channel && document.referrer) {
    try {
      const host = new URL(document.referrer).hostname;
      channel = ({ 'chatgpt.com': 'ai-chatgpt', 'claude.ai': 'ai-claude',
        'perplexity.ai': 'ai-perplexity' })[host] || '';
    } catch {}
  }
  try {
    channel = channel || normalize(sessionStorage.getItem('quotify-channel'));
    if (channel) sessionStorage.setItem('quotify-channel', channel);
  } catch {}
  const rewrite = href => {
    const url = new URL(href);
    url.searchParams.set('ct', channel || 'website');
    if (channel) url.searchParams.set('ppid', pages[channel]);
    return url.href;
  };
  document.querySelectorAll('a[href*="apps.apple.com/"]').forEach(anchor => {
    const url = new URL(anchor.href);
    if (url.hostname === 'apps.apple.com' && /\/id1626937020$/.test(url.pathname)) {
      anchor.href = rewrite(anchor.href);
    }
  });
  const banner = document.querySelector('meta[name="apple-itunes-app"]');
  if (banner) {
    banner.content = banner.content
      .replace(/ct=website/g, 'ct=' + (channel || 'website'))
      .replace(/app-argument=(.*)$/, (_, href) => 'app-argument=' + rewrite(href));
  }
})();
