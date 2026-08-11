import { describe, it, expect, beforeEach } from 'vitest';
import { WorkdayAdapter } from '../src/adapters/WorkdayAdapter';

describe('Workday Adapter', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('detects workday form', () => {
    const adapter = new WorkdayAdapter();
    document.body.innerHTML = '<div data-automation-id="workday-application"></div>';
    expect(adapter.detect()).toBe(true);
  });

  it('extracts fields via data-automation-id="formField"', () => {
    document.body.innerHTML = `
      <div data-automation-id="formField">
        <label>Legal Name*</label>
        <input type="text" id="legal_name" name="legal_name" aria-required="true" />
      </div>
    `;
    const adapter = new WorkdayAdapter();
    const fields = adapter.extractForm();
    
    expect(fields.length).toBe(1);
    expect(fields[0].label).toBe('Legal Name');
    expect(fields[0].required).toBe(true);
  });

  it('declares browserExecution as false due to complexity/captcha', () => {
    const adapter = new WorkdayAdapter();
    expect(adapter.getCapabilities().browserExecution).toBe(false);
    expect(adapter.isBrowserExecutionSupported()).toBe(false);
  });
});
