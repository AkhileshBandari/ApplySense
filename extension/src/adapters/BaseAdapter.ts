export interface DetectedField {
  id: string;
  label: string;
  name: string;
  type: string;
  options?: string[];
  required: boolean;
  value: string;
  element: HTMLElement;
}

export interface ReviewSummary {
  safeFill: number;
  reviewRequired: number;
  blocked: number;
}

export interface AdapterCapabilities {
  formDetection: boolean;
  fieldExtraction: boolean;
  safeAutofill: boolean;
  browserExecution: boolean;
  multiStep: boolean;
}

export interface BaseAdapter {
  providerName: string;
  version: string;
  
  getCapabilities(): AdapterCapabilities;
  
  /** Returns true if this adapter matches the current page. */
  detect(): boolean;
  
  /** Extracts all form fields without modifying them. */
  extractForm(): DetectedField[];
  
  /** Safely sets a value. Must never call submit. */
  fillField(element: HTMLElement, value: string): void;
  
  /** Provides summary of autofill operation */
  getReviewSummary(): ReviewSummary;
  
  /** Returns true if this adapter supports user-confirmed browser execution */
  isBrowserExecutionSupported?(): boolean;
  
  /** Executes the final submit action by triggering the specific known button. */
  executeFinalSubmit?(): boolean;
}
