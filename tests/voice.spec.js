import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const messages = JSON.parse(readFileSync(new URL('../shared/voice_messages.json', import.meta.url), 'utf8'));
test.use({ launchOptions: { executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' } });
const baseURL = process.env.BOLI_TEST_URL || 'http://127.0.0.1:5174';
async function setup(page, selected = 'English') {
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.addInitScript(({ selected }) => {
    localStorage.setItem('boli-language', JSON.stringify(selected));
    window.voiceRequests = []; window.spoken = [];
    class FakeRecognition {
      constructor() { window.recognition = this; }
      start() { this.onstart?.(); }
      abort() { this.aborted = true; this.onend?.(); }
    }
    window.SpeechRecognition = FakeRecognition;
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    Object.defineProperty(window, 'speechSynthesis', { value: {
      getVoices: () => ['en','hi','te','ta','kn','ml','mr','bn'].map(code => ({lang:code+'-IN',name:code})),
      cancel: () => {},
      speak: utterance => { window.spoken.push({text:utterance.text,lang:utterance.lang,voice:utterance.voice?.lang}); utterance.onstart?.(); utterance.onend?.(); },
    }});
  }, { selected });
  await page.route('**/api/products', route => route.fulfill({json:[{id:'rice',name:'Rice',category:'Grains',default_unit:'kg',minimum_stock:3,current_stock:20}]}));
  await page.route('**/api/activity', route => route.fulfill({json:[]}));
}

test('selected language reaches recognition, command API, and spoken response in all eight languages', async ({ page }) => {
  await setup(page);
  const requests = [];
  await page.route('**/api/voice/process', route => {
    const body=route.request().postDataJSON(); requests.push(body);
    return route.fulfill({json:{status:'ok',message:messages[body.language].healthy,language:body.language}});
  });
  await page.goto(baseURL, {waitUntil:'domcontentloaded'});
  for (const [label,code,phrase] of [['English','en','Add 3 kg rice'],['हिंदी','hi','तीन किलो चावल जोड़ो'],['తెలుగు','te','మూడు కిలోల బియ్యం జోడించు'],['தமிழ்','ta','மூன்று கிலோ அரிசி சேர்'],['ಕನ್ನಡ','kn','ಮೂರು ಕೆಜಿ ಅಕ್ಕಿ ಸೇರಿಸು'],['മലയാളം','ml','മൂന്ന് കിലോ അരി ചേർക്കുക'],['मराठी','mr','तीन किलो तांदूळ जोडा'],['বাংলা','bn','তিন কেজি চাল যোগ করো']]) {
    await page.locator('.lang-pill').click();
    await page.getByLabel('Voice input language').selectOption(label);
    await page.getByRole('button',{name:'Save language'}).click();
    await page.locator('.speak-button').click();
    expect(await page.evaluate(() => window.recognition.lang)).toBe(code+'-IN');
    const before=requests.length;
    await page.evaluate(text => {
      const result=[{transcript:text}]; result.isFinal=false;
      window.recognition.onresult({results:[result]});
    },phrase);
    expect(requests.length).toBe(before);
    await page.evaluate(text => {
      const result=[{transcript:text}]; result.isFinal=true;
      const handler=window.recognition.onresult;
      handler({results:[result]}); handler({results:[result]});
    },phrase);
    await expect(page.locator('.transcript')).toContainText(messages[code].healthy);
    expect(requests.length).toBe(before+1);
    expect(requests.at(-1)).toEqual({text:phrase,language:code});
    await expect.poll(() => page.evaluate(() => window.spoken.at(-1)?.lang)).toBe(code+'-IN');
    expect(await page.evaluate(() => window.spoken.at(-1).voice)).toBe(code+'-IN');
    const count=await page.evaluate(() => window.spoken.length);
    await page.locator('.response-speaker').click();
    await expect.poll(() => page.evaluate(() => window.spoken.length)).toBe(count+1);
  }
});

test('permission failures and cancellation do not send commands; typed fallback works', async ({page}) => {
  await setup(page,'हिंदी'); let calls=0;
  await page.route('**/api/voice/process',route=>{calls++;return route.fulfill({json:{status:'answer',message:'Rice: 20 किलो उपलब्ध है।'}});});
  await page.goto(baseURL,{waitUntil:'domcontentloaded'});
  await page.locator('.speak-button').click();
  await page.locator('.speak-button').click();
  expect(await page.evaluate(()=>window.recognition.aborted)).toBe(true); expect(calls).toBe(0);
  await page.locator('.speak-button').click();
  await page.evaluate(()=>window.recognition.onerror({error:'not-allowed'}));
  await expect(page.locator('.transcript')).toContainText(messages.hi.permission);
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel(messages.hi.request,{exact:true}).fill('चावल कितना बचा है?');
  await page.getByRole('button',{name:messages.hi.submit,exact:true}).click();
  await expect(page.getByRole('dialog')).toContainText('20 किलो');
  expect(calls).toBe(1);
});

test('API failure is localized and never announced as saved', async ({page}) => {
  await setup(page,'తెలుగు');
  await page.route('**/api/voice/process',route=>route.fulfill({status:500,body:'Internal Server Error'}));
  await page.goto(baseURL,{waitUntil:'domcontentloaded'});
  await page.getByPlaceholder('Type or ask something…').fill('3 కిలోల బియ్యం జోడించు');
  await page.getByRole('button',{name:'Ask',exact:true}).click();
  await expect(page.locator('.transcript')).toContainText(messages.te.server);
  await expect(page.getByPlaceholder('Type or ask something…')).not.toHaveValue('');
  await expect(page.locator('.speak-button')).toBeEnabled();
});

test('unsupported browser opens typed entry and missing playback voice is explained', async ({page}) => {
  await setup(page);
  await page.addInitScript(()=>{window.SpeechRecognition=undefined; window.webkitSpeechRecognition=undefined;});
  await page.goto(baseURL,{waitUntil:'domcontentloaded'});
  await page.locator('.speak-button').click();
  await expect(page.getByRole('dialog')).toContainText(messages.en.unavailable);
  await page.getByRole('button',{name:'Close',exact:true}).click();
  await page.evaluate(()=>window.speechSynthesis.getVoices=()=>[{lang:'fr-FR'}]);
  await page.locator('.response-speaker').click();
  await expect(page.getByText(messages.en.noVoice,{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>window.spoken.length)).toBe(0);
});
