import { describe, it, expect, beforeEach, vi } from 'vitest';
import { GreenhouseAdapter } from '../src/adapters/GreenhouseAdapter';
import { LeverAdapter } from '../src/adapters/LeverAdapter';
import { AshbyAdapter } from '../src/adapters/AshbyAdapter';
import { GenericAdapter } from '../src/adapters/GenericAdapter';

describe('Adapter Architecture Tests', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  describe('Greenhouse Adapter', () => {
    it('detects greenhouse form', () => {
      const adapter = new GreenhouseAdapter();
      document.body.innerHTML = '<form action="https://boards.greenhouse.io/submit"></form>';
      expect(adapter.detect()).toBe(true);
    });

    it('rejects false positive generic #application_form without greenhouse link', () => {
      const adapter = new GreenhouseAdapter();
      document.body.innerHTML = '<form id="application_form"></form><div>I love greenhouse gas emissions</div>';
      expect(adapter.detect()).toBe(false);
    });

    it('extracts fields without submitting', () => {
      document.body.innerHTML = `
        <form id="application_form">
          <div class="field">
            <label>First Name<span class="asterisk">*</span></label>
            <input type="text" id="first_name" name="first_name" required />
          </div>
          <button type="submit" id="submit_app">Submit Application</button>
        </form>
      `;
      const adapter = new GreenhouseAdapter();
      const fields = adapter.extractForm();
      
      expect(fields.length).toBe(1);
      expect(fields[0].label).toBe('First Name');
      expect(fields[0].required).toBe(true);
      expect(fields[0].id).toBe('first_name');
    });

    it('does not click submit when filling field', () => {
      document.body.innerHTML = `<input type="text" id="first_name" />`;
      const el = document.getElementById('first_name') as HTMLElement;
      
      const submitSpy = vi.spyOn(HTMLFormElement.prototype, 'submit');
      
      const adapter = new GreenhouseAdapter();
      adapter.fillField(el, 'Akhilesh');
      
      expect((el as HTMLInputElement).value).toBe('Akhilesh');
      expect(submitSpy).not.toHaveBeenCalled();
    });
  });

  describe('Lever Adapter', () => {
    it('detects lever form', () => {
      const adapter = new LeverAdapter();
      document.body.innerHTML = '<form action="https://jobs.lever.co/company/job"></form>';
      expect(adapter.detect()).toBe(true);
    });

    it('extracts fields correctly', () => {
      document.body.innerHTML = `
        <div class="application-field">
          <label class="application-label">Email<span class="required">*</span></label>
          <input type="email" id="email" name="email" required />
        </div>
      `;
      const adapter = new LeverAdapter();
      const fields = adapter.extractForm();
      
      expect(fields.length).toBe(1);
      expect(fields[0].label).toBe('Email');
    });
  });

  describe('Ashby Adapter', () => {
    it('extracts fields via aria-labels', () => {
      document.body.innerHTML = `
        <input type="text" aria-label="Phone Number" />
      `;
      const adapter = new AshbyAdapter();
      const fields = adapter.extractForm();
      
      expect(fields.length).toBe(1);
      expect(fields[0].label).toBe('Phone Number');
    });
  });
  
  describe('Generic Adapter', () => {
    it('ignores submit buttons', () => {
      document.body.innerHTML = `
        <input type="text" placeholder="Name" />
        <input type="submit" value="Send" />
      `;
      const adapter = new GenericAdapter();
      const fields = adapter.extractForm();
      
      expect(fields.length).toBe(1);
      expect(fields[0].type).toBe('text');
    });
  });
});
