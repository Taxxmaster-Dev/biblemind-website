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
  assert.equal(route({pathname:'/app/'+name+'.html',search:'?lang=hu'}).redirect,
    '/app/hu/'+name+'.html');
  assert.equal(route({pathname:'/app/'+name+'.html',search:'?lang=es'}).redirect,
    '/app/es/'+name+'.html');
  assert.equal(route({pathname:'/app/'+name+'.html',search:'?lang=en',lang:'ro-RO'}).redirect,
    null, 'Explicit English language must take precedence over device locale');
  for (const lang of ['hu','es','pt','ro','de','it','pl','fr','nl','zh-hans','zh-hant','vi','hi','th','uk','ru','el']) {
    const actual=route({pathname:'/app/'+name+'.html',search:'?lang='+lang});
    assert.equal(actual.redirect,'/app/'+lang+'/'+name+'.html',
      lang+' must open its full legal document');
  }

}
assert.equal(route({pathname:'/privacy.html',search:'?lang=ro'}).redirect,null);
assert.equal(route({pathname:'/ro/privacy.html',search:'?lang=ro'}).redirect,null);
assert.equal(route({pathname:'/app/ro/terms.html',search:'?lang=ro'}).redirect,null);
console.log('PASS: all 18 legal language routes, English opt-in and website-only scope.');
