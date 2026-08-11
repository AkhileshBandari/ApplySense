import { describe, it, expect, beforeEach } from 'vitest';
import { WorkableAdapter } from '../src/adapters/WorkableAdapter';

describe('Workable Adapter', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('detects workable form via data-ui', () => {
    const adapter = new WorkableAdapter();
    document.body.innerHTML = '<form data-ui="application-form"></form>';
    expect(adapter.detect()).toBe(true);
  });

  it('extracts fields via data-ui="form-field"', () => {
    document.body.innerHTML = `
      <div data-ui="form-field">
        <label>Portfolio URL*</label>
        <input type="text" id="portfolio" name="portfolio" required />
      </div>
    `;
    const adapter = new WorkableAdapter();
    const fields = adapter.extractForm();
    
    expect(fields.length).toBe(1);
    expect(fields[0].label).toBe('Portfolio URL');
    expect(fields[0].required).toBe(true);
  });

  it('declares browserExecution as false', () => {
    const adapter = new WorkableAdapter();
    expect(adapter.getCapabilities().browserExecution).toBe(false);
  });
});
