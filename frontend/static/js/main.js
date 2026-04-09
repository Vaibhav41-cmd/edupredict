/**
 * main.js — Global JavaScript for Student Prediction System
 * Handles: form submissions, AJAX calls, UI interactions
 */

"use strict";

/* ── Utility: AJAX helper ─────────────────────────────────────────────────── */
async function apiFetch(url, method = "GET", body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Request failed");
  return data;
}

/* ── Button loading state ─────────────────────────────────────────────────── */
function setLoading(btn, state) {
  if (state) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing…';
    btn.disabled = true;
    btn.classList.add("btn-loading");
  } else {
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
    btn.disabled = false;
    btn.classList.remove("btn-loading");
  }
}

/* ── Form submit loading ──────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {

  // Add loading state to all form submit buttons
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", function (e) {
      if (!form.checkValidity()) return; // browser validation
      const btn = form.querySelector('[type="submit"]');
      if (btn) setLoading(btn, true);
    });
  });

  // Confirm dialogs for delete forms
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Sidebar active link highlight (fallback)
  const path = window.location.pathname;
  document.querySelectorAll(".sidebar-nav .nav-link").forEach((link) => {
    if (link.getAttribute("href") && path.startsWith(link.getAttribute("href")) && link.getAttribute("href") !== "/") {
      link.classList.add("active");
    }
  });

  // Auto-dismiss alerts
  document.querySelectorAll(".alert.alert-dismissible").forEach((alert) => {
    setTimeout(() => {
      try {
        bootstrap.Alert.getOrCreateInstance(alert).close();
      } catch (_) {}
    }, 6000);
  });

  // Number input: prevent negative via keyboard
  document.querySelectorAll('input[type="number"][min="0"]').forEach((inp) => {
    inp.addEventListener("blur", () => {
      const min = parseFloat(inp.min ?? 0);
      const max = parseFloat(inp.max ?? Infinity);
      const val = parseFloat(inp.value);
      if (!isNaN(val)) inp.value = Math.min(Math.max(val, min), max);
    });
  });

  // Tooltip init (Bootstrap 5)
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    new bootstrap.Tooltip(el, { trigger: "hover" });
  });
});

/* ── Quick Predict (API call from any page) ───────────────────────────────── */
async function quickPredict(formData) {
  const resultDiv = document.getElementById("quickPredictResult");
  if (!resultDiv) return;

  try {
    resultDiv.innerHTML = `<div class="text-center py-3"><span class="spinner-border text-primary"></span></div>`;
    const data = await apiFetch("/api/v1/predict/quick", "POST", formData);
    const pred = data.data;
    const isPass = pred.result === "PASS";
    const color = isPass ? "#10b981" : "#ef4444";
    const icon = isPass ? "✅" : "❌";

    resultDiv.innerHTML = `
      <div class="p-4 rounded-3 text-center" style="background:${isPass ? "#f0fdf4" : "#fff1f2"};border:2px solid ${color}">
        <div style="font-size:2.5rem">${icon}</div>
        <div class="display-6 fw-700 mt-2" style="color:${color}">${pred.result}</div>
        <div class="text-muted mt-1 mb-3" style="font-size:.85rem">Predicted by ${pred.model_name}</div>
        <div class="row g-2 text-center">
          <div class="col-6">
            <div class="fw-700 text-success" style="font-size:1.3rem">${(pred.pass_probability*100).toFixed(1)}%</div>
            <small class="text-muted">Pass Probability</small>
          </div>
          <div class="col-6">
            <div class="fw-700 text-danger" style="font-size:1.3rem">${(pred.fail_probability*100).toFixed(1)}%</div>
            <small class="text-muted">Fail Probability</small>
          </div>
        </div>
        <div class="mt-3" style="background:#e2e8f0;height:8px;border-radius:4px;overflow:hidden">
          <div style="background:#10b981;height:100%;width:${(pred.pass_probability*100).toFixed(1)}%;border-radius:4px;transition:width .6s ease"></div>
        </div>
        <div class="mt-2" style="font-size:.75rem;color:#94a3b8">
          Confidence: <strong>${pred.confidence_level}</strong>
        </div>
      </div>`;
  } catch (err) {
    resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-x-circle me-2"></i>${err.message}</div>`;
  }
}

/* ── Copy to clipboard ────────────────────────────────────────────────────── */
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
    setTimeout(() => (btn.innerHTML = orig), 2000);
  });
}

/* ── Chart.js global defaults ─────────────────────────────────────────────── */
if (typeof Chart !== "undefined") {
  Chart.defaults.font.family = "Inter, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = "#64748b";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;
}
