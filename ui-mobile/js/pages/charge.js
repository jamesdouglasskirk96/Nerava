import { apiPost } from '../core/api.js';
const $ = (s)=>document.querySelector(s);

export function initCharge(){
  // basic placeholder – location-based verification hook (dual radius job can call /v1/dual/start)
  const root = document.getElementById('page-charge'); if (!root) return;
  // No scan UI. Show a tiny hint if needed.
}