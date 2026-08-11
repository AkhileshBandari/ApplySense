import { describe, it, expect, beforeEach } from 'vitest';
import { SmartRecruitersAdapter } from '../src/adapters/SmartRecruitersAdapter';

describe('SmartRecruiters Adapter', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('detects smartrecruiters script', () => {
    const adapter = new SmartRecruitersAdapter();
    document.body.innerHTML = '<script src="https://st.smartrecruiters.com/widget.js"></script>';
    expect(adapter.detect()).toBe(true);
  });

  it('extracts fields via .form-group', () => {
    document.body.innerHTML = `
      <div class="form-group">
        <label>Resume<span class="required-asterisk">*</span></label>
        <input type="text" id="resume" name="resume" />
      </div>
    `;
    const adapter = new SmartRecruitersAdapter();
    const fields = adapter.extractForm();
    
    expect(fields.length).toBe(1);
    expect(fields[0].label).toBe('Resume');
    expect(fields[0].required).toBe(true);
  });

  it('declares browserExecution as false', () => {
    const adapter = new SmartRecruitersAdapter();
    expect(adapter.getCapabilities().browserExecution).toBe(false);
  });
});
