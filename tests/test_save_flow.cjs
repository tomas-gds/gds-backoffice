const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../features/pubmed-scraper/PubmedScraper.jsx'), 'utf8');
const body = source.slice(source.indexOf('  async function saveResults()'), source.indexOf('\n  return <main'));
async function check(format, chooseLocation, cancel = false, invalid = false) {
  let calls = [], closed = false, cleared = false, message = '', error = '';
  const context = { saveFileName: 'my-results.xlsx', pendingBytes: new Uint8Array([1,2]), account: invalid ? {} : { userFolderDirectory: 'C:/Users/backup', desktopDirectory: 'C:/Desktop' }, window: { __TAURI_INTERNALS__: true }, exportFormat: format, chooseLocation, API: 'http://localhost', setError: x => error = x, setSaving: () => {}, setSaveDialogOpen: x => closed = !x, setPendingBytes: x => cleared = x === null, setMessage: x => message = x, browserDownload: () => assert.fail('Unexpected browser fallback'), fetch: async (url, options) => { assert.equal(url, 'http://localhost/pubmed/convert-export'); assert.equal(options.body.get('export_format'), format); return { ok: true, arrayBuffer: async () => new Uint8Array([3,4]).buffer }; }, invoke: async (command, args) => { calls.push({command, args}); return cancel ? null : { exportPath: 'C:/Desktop/result.'+format }; } };
  const save = new Function(...Object.keys(context), body + '\nreturn saveResults;')(...Object.values(context));
  await save();
  if (invalid) { assert.equal(calls.length, 0); assert.ok(error); return; }
  assert.equal(calls[0].command, 'save_pubmed_export');
  assert.equal(calls[0].args.defaultFileName, 'my-results.'+format);
  assert.equal(calls[0].args.chooseExportLocation, chooseLocation);
  assert.deepEqual(calls[0].args.bytes, [3,4]);
  assert.equal(closed, !cancel); assert.equal(cleared, !cancel);
  assert.ok(!message.includes('backup'));
}
(async () => { await check('xlsx', false); await check('csv', true); await check('xlsx', true, true); await check('xlsx', false, false, true); console.log('PASS: Excel, CSV/custom location, picker cancel, required directories and silent backup message.'); })().catch(e => { console.error(e); process.exit(1); });
