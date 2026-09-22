import {test, expect} from '@playwright/test';

async function mockApis(page:any) {
  await page.route('**/api/sessions', async route => {
    if (route.request().method()==='POST') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'sess-browser',telemetry_key:'browser-test-key'})});
    return route.fulfill({status:200,contentType:'application/json',body:'[]'});
  });
  await page.route('**/api/sessions/**', async route => {
    const method=route.request().method();
    if (method==='POST') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({accepted:true})});
    return route.fulfill({status:200,contentType:'application/json',body:'{}'});
  });
}

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    class FakeRecorder { static isTypeSupported(){return true;} ondataavailable:any; state='inactive'; constructor(public stream:any, public options:any){} start(){this.state='recording';} stop(){this.state='inactive'; this.ondataavailable?.({data:new Blob(['segment'],{type:'video/webm'})});} }
    // @ts-ignore
    window.MediaRecorder=FakeRecorder;
    // @ts-ignore
    navigator.mediaDevices={getUserMedia: async()=>({getTracks:()=>[{stop(){}}], addEventListener(){}, removeEventListener(){}}), addEventListener(){}, removeEventListener(){}};
    // @ts-ignore
    HTMLMediaElement.prototype.play=async()=>{};
  });
});

test('candidate consent gate and recording indicator', async ({page}) => {
  await page.goto('/#capture');
  await expect(page.getByText('CANDIDATE CAPTURE / CONSENTED MOCK EXAM')).toBeVisible();
  const start=page.getByRole('button',{name:'Grant permissions and start'});
  await expect(start).toBeDisabled();
  await page.getByRole('checkbox').check();
  await expect(start).toBeEnabled();
});

test('mocked capture starts, uploads a segment, and stops', async ({page}) => {
  let mediaUploads=0; page.on('request', request => { if (request.url().includes('/media')) mediaUploads++; });
  await mockApis(page); await page.goto('/#capture'); await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:'Grant permissions and start'}).click();
  await expect(page.getByText(/RECORDING ACTIVE/)).toBeVisible();
  await page.evaluate(() => document.dispatchEvent(new Event('copy')));
  await expect(page.getByText(/Adaptive sample interval/)).toBeVisible();
  await page.getByRole('button',{name:'Stop session'}).click();
  await expect.poll(() => mediaUploads).toBe(1);
  await expect(page.getByText('Session completed')).toBeVisible();
});

test('permission denial is surfaced without a recording indicator', async ({page}) => {
  await page.addInitScript(() => { /* @ts-ignore */ navigator.mediaDevices.getUserMedia=async()=>{throw new Error('Permission denied');}; });
  await mockApis(page); await page.goto('/#capture'); await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:'Grant permissions and start'}).click();
  await expect(page.getByText('Capture unavailable')).toBeVisible();
  await expect(page.getByText(/RECORDING ACTIVE/)).not.toBeVisible();
});

test('reviewer mode exposes candidate capture navigation', async ({page}) => {
  await page.goto('/');
  await expect(page.getByRole('button',{name:/Open candidate capture/})).toBeVisible();
});
