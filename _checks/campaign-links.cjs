const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync('assets/campaign-links.js', 'utf8');
const storage = new Map();
function visit(search = '', referrer = '', blocked = false) {
  const anchor = {href: 'https://apps.apple.com/app/apple-store/id1626937020?ppid=76589797-e154-4662-abbd-d4c5c7a38b05&pt=958359&ct=website&mt=8'};
  const banner = {content: 'app-id=1626937020, affiliate-data=pt=958359&ct=website&mt=8'};
  vm.runInNewContext(source, {URL, URLSearchParams, location: {search},
    sessionStorage: {getItem: key => {if(blocked) throw Error(); return storage.get(key);},
      setItem: (key, value) => storage.set(key, value)},
    document: {referrer, querySelectorAll: () => [anchor], querySelector: () => banner}});
  return {url: new URL(anchor.href), banner: banner.content};
}
assert.equal(visit().url.searchParams.get('ct'), 'website');
assert.equal(visit('?utm_source=reddit').url.searchParams.get('ct'), 'reddit');
assert.equal(visit().url.searchParams.get('ct'), 'reddit');
assert.equal(visit('?ref=tiktok').url.searchParams.get('ppid'), '3bfae5bb-ea40-4c58-b90f-4d3b7b003fa4');
assert.equal(visit('', 'https://chatgpt.com/c/example').url.searchParams.get('ct'), 'ai-chatgpt');
storage.clear();
assert.equal(visit('', 'https://chatgpt.com.evil.example/').url.searchParams.get('ct'), 'website');
assert.equal(visit('?utm_source=reddit', '', true).url.searchParams.get('ct'), 'reddit');
assert.equal(visit('?ref=claude').banner, 'app-id=1626937020, affiliate-data=pt=958359&ct=ai-claude&mt=8');
console.log('OK: defaults, Reddit, session persistence, overrides, product pages, AI referrers, blocked storage and banner tokens');
