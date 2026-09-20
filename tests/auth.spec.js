import { test, expect } from '@playwright/test';
test.use({ launchOptions: { executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' } });
const baseURL = process.env.BOLI_TEST_URL || 'http://127.0.0.1:5173';

test('new user signs up, sees their name, reloads, signs out and signs back in', async ({page}) => {
  let user = null;
  let account = null;
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.route('**/api/auth/**', route => {
    const path = new URL(route.request().url()).pathname;
    const body = route.request().postDataJSON();
    if (path.endsWith('/signup')) { account = body; user = {id:1,name:body.name,email:body.email}; }
    if (path.endsWith('/logout')) { user = null; return route.fulfill({status:204}); }
    if (path.endsWith('/login')) {
      if (body.password !== account.password) return route.fulfill({status:401,json:{detail:'Email or password is incorrect.'}});
      user = {id:1,name:account.name,email:account.email};
    }
    return route.fulfill({status:user ? 200 : 401,json:user || {detail:'Please sign in.'}});
  });
  await page.route('**/api/products', route => route.fulfill({json:[]}));
  await page.route('**/api/activity', route => route.fulfill({json:[]}));
  await page.goto(baseURL);
  await page.getByRole('button',{name:'Sign up',exact:true}).click();
  await page.getByLabel('Full name').fill('Ananya Rao');
  await page.getByLabel('Email address').fill('ananya@example.com');
  await page.getByLabel('Password',{exact:true}).fill('secure-pass-123');
  await page.getByLabel('Confirm password').fill('different-pass');
  await page.getByRole('button',{name:'Create account',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Passwords do not match');
  await page.getByLabel('Confirm password').fill('secure-pass-123');
  await page.getByRole('button',{name:'Create account',exact:true}).click();
  await expect(page.locator('.breadcrumb')).toContainText('Good morning, Ananya Rao');
  await expect(page.locator('.profile-row')).toContainText('Ananya Rao');
  await expect(page.locator('.profile-avatar')).toHaveText('AR');
  await page.reload();
  await expect(page.locator('.breadcrumb')).toContainText('Good morning, Ananya Rao');
  await page.getByRole('button',{name:'Sign out',exact:true}).click();
  await page.getByLabel('Email address').fill('ananya@example.com');
  await page.getByLabel('Password',{exact:true}).fill('wrong-pass');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Email or password is incorrect');
  await page.getByLabel('Password',{exact:true}).fill('secure-pass-123');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.locator('.breadcrumb')).toContainText('Good morning, Ananya Rao');
  await page.setViewportSize({width:390,height:844});
  await expect(page.locator('.breadcrumb strong')).toBeVisible();
});
