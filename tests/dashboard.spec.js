import { test, expect } from '@playwright/test';
test.use({ launchOptions: { executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' } });
test('dashboard controls and persistent inventory requests', async ({ page }) => {
  const products = [{id:'rice',name:'Basmati rice',category:'Grains',default_unit:'bags',minimum_stock:8,current_stock:18},{id:'dal',name:'Toor dal',category:'Pulses',default_unit:'bags',minimum_stock:8,current_stock:5}];
  const activity = [];
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url()); const path=url.pathname.replace('/api','');
    let result={};
    if(path==='/products' && route.request().method()==='GET') result=products;
    if(path==='/products' && route.request().method()==='POST') { const p=route.request().postDataJSON(); products.push({...p,current_stock:0}); result=p; }
    if(path==='/activity') result=activity;
    if(path==='/transactions') {const tx=route.request().postDataJSON(); products.find(p=>p.id===tx.product_id).current_stock+=tx.quantity; activity.push({id:1,title:'Basmati rice',detail:'Purchase 3 bags',time:'Today',type:'in',color:'green'});}
    if(path.endsWith('/story')) result={product_name:'Basmati rice',explanation:'21 bags remain.',timeline:[]};
    if(path==='/voice/process') result={status:'answer',message:'Toor dal: 5 bags (reorder at 8)'};
    await route.fulfill({json:result});
  });
  await page.goto(process.env.BOLI_TEST_URL || 'http://127.0.0.1:5174', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.stock-card')).toHaveCount(2);
  await page.getByRole('button',{name:/Running low/}).click(); await expect(page.locator('.stock-card')).toHaveCount(1);
  await page.getByRole('button',{name:/All items/}).click();
  await page.getByPlaceholder('Find an item…').fill('rice'); await expect(page.locator('.stock-card')).toHaveCount(1);
  await page.getByPlaceholder('Find an item…').fill('');
  await page.getByRole('button',{name:'Quick add',exact:true}).click();
  await page.getByLabel('Quantity (bags)').fill('3'); await page.getByRole('button',{name:'Save entry'}).click();
  await expect(page.locator('.stock-card').first()).toContainText('21');
  await page.locator('.stock-card').first().click(); await expect(page.getByRole('dialog')).toContainText('21 bags remain'); await page.getByRole('button',{name:'Close',exact:true}).click();
  for(const name of ['Sales & buys','Insights','Item catalog','Reports','Settings']) {
    await page.getByRole('button',{name,exact:true}).click(); await expect(page.getByRole('dialog')).toBeVisible(); await page.getByRole('button',{name:'Close',exact:true}).click();
  }
  await page.getByRole('button',{name:'Notifications',exact:true}).click(); await expect(page.getByRole('dialog')).toContainText('Toor dal'); await page.getByRole('button',{name:'Close',exact:true}).click();
  await page.getByRole('button',{name:'Help',exact:true}).click(); await expect(page.getByRole('dialog')).toContainText('microphone'); await page.getByRole('button',{name:'Close',exact:true}).click();
  await page.getByRole('button',{name:'Hindi + English',exact:true}).click(); await page.getByLabel('Voice input language').selectOption('English'); await page.getByRole('button',{name:'Save language'}).click();
  await expect(page.locator('.lang-pill')).toContainText('English');
  await page.getByRole('button',{name:'What should I reorder?',exact:true}).click(); await page.getByRole('button',{name:'Ask',exact:true}).click(); await expect(page.getByRole('dialog')).toContainText('Toor dal'); await page.getByRole('button',{name:'Close',exact:true}).click();
  const download = page.waitForEvent('download'); await page.getByRole('button',{name:'Share today’s view'}).click(); expect((await download).suggestedFilename()).toMatch(/bolistock.*csv/);
  await page.screenshot({path:'tests/dashboard-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844}); await expect(page.locator('.speak-button')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.screenshot({path:'tests/dashboard-mobile.png',fullPage:true});
  expect(errors).toEqual([]);
});


