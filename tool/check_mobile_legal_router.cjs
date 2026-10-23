'use strict';
// No external dependencies: evaluate only the legal-locale route decision.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync(require('node:path').join(__dirname, '../app/legal-locale-router.js'), 'utf8');

function route({pathname='/app/privacy.html', search='', lang='en-US'}) {
  let redirect=null;
  let listener=null;
  const ctx = {
    URLSearchParams,
    Set,
    navigator: {language:lang, languages:[lang]},
    location: {
      pathname, search, hash: '',
      replace(path) {redirect=path;},
    },
    document: {
      addEventListener(name, handler) {
        assert.equal(name, 'DOMContentLoaded');
        listener=handler;
      },
    },
  };
  vm.runInNewContext(script, ctx, {timeout:1000});
  return {redirect, listener:!!listener};
}

for (const name of ['privacy','terms','copyright','data-deletion']) {
  assert.equal(route({pathname:'/app/'+name+'.html',search:'?lang=ro'}).redirect,
    '/app/ro/'+name+'.html');
  assert.equal(route({pathname:'/app/'+name+'.html',lang:'ro-RO'}).redirect,
    '/app/ro/'+name+'.html');
  assert.equal(route({pathname:'/app/'+name+'.html',search:'?lang=en',lang:'ro-RO'}).redirect,
    null, 'Explicit English language must take precedence over device locale');
  for (const lang of ['hu','de','fr','zh-hant','hi']) {
    const actual=route({pathname:'/app/'+name+'.html',search:'?lang='+lang});
    assert.equal(actual.redirect,null,lang+' must not redirect to a missing translation');
    assert.equal(actual.listener,true,lang+' must disclose English fallback in the DOM');
  }
}
assert.equal(route({pathname:'/privacy.html',search:'?lang=ro'}).redirect,null);
assert.equal(route({pathname:'/ro/privacy.html',search:'?lang=ro'}).redirect,null);
assert.equal(route({pathname:'/app/ro/terms.html',search:'?lang=ro'}).redirect,null);
console.log('PASS: Romanian legal redirect, English opt-in, missing-language fallbacks and separate website scope.');
