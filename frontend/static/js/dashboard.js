/* BizOptima Dashboard */

const API = '';
let currentPredictionId = null;
let charts = {};

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (!token) {
    window.location.href = '/login';
    return;
  }

  updateUserShell(getUser() || {});
  setupNavigation();
  setupEvents();
  loadProfile();
  loadDashboard();
});

function setupEvents() {
  const predictForm = document.getElementById('predictForm');
  if (predictForm) {
    predictForm.addEventListener('submit', handlePredict);
  }

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (event) => {
      event.preventDefault();
      logout();
    });
  }

  const toggleBtn = document.getElementById('sidebarToggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('open');
    });
  }

  const exportPdfBtn = document.getElementById('exportPdfBtn');
  if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', () => {
      if (currentPredictionId) exportPDF(currentPredictionId);
    });
  }
}

function updateUserShell(user) {
  const username = user.username || 'User';
  const business = user.business_name || user.email || 'BizOptima user';
  document.getElementById('userGreeting').textContent = `Hi, ${username}`;
  document.getElementById('userBusiness').textContent = business;
  document.getElementById('userAvatar').textContent = username.slice(0, 1).toUpperCase();
}

function setupNavigation() {
  document.querySelectorAll('.sidebar-link[data-section]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      showSection(link.dataset.section);
    });
  });
}

function showSection(name) {
  document.querySelectorAll('.content-section').forEach((section) => section.classList.add('d-none'));
  const target = document.getElementById(`section-${name}`);
  if (target) target.classList.remove('d-none');

  document.querySelectorAll('.sidebar-link').forEach((link) => link.classList.remove('active'));
  const activeLink = document.querySelector(`.sidebar-link[data-section="${name}"]`);
  if (activeLink) activeLink.classList.add('active');

  const titles = {
    dashboard: 'Dashboard',
    predict: 'Predict Profit',
    whatif: 'What-If Analysis',
    history: 'History',
    model: 'Model Info'
  };
  document.getElementById('pageTitle').textContent = titles[name] || 'BizOptima';

  if (name === 'history') loadHistory();
  if (name === 'model') loadModelInfo();

  document.getElementById('sidebar').classList.remove('open');
}

async function apiRequest(url, method = 'GET', body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`
    }
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(API + url, opts);
  if (res.status === 401 || res.status === 422) {
    clearSession();
    window.location.href = '/login';
    throw new Error('Session expired. Please sign in again.');
  }
  return res;
}

async function loadProfile() {
  try {
    const res = await apiRequest('/api/auth/profile');
    const data = await res.json();
    if (res.ok && data.user) {
      localStorage.setItem('user', JSON.stringify(data.user));
      updateUserShell(data.user);
    }
  } catch (error) {
    console.error('Profile load error:', error);
  }
}

async function loadDashboard() {
  try {
    const res = await apiRequest('/api/predictions/dashboard');
    const data = await res.json();

    if (!data.has_data) {
      document.getElementById('dashboardEmpty').classList.remove('d-none');
      document.querySelectorAll('#section-dashboard .chart-card, #section-dashboard .stat-card').forEach((el) => {
        el.style.opacity = '0.45';
      });
      return;
    }

    document.getElementById('dashboardEmpty').classList.add('d-none');
    document.querySelectorAll('#section-dashboard .chart-card, #section-dashboard .stat-card').forEach((el) => {
      el.style.opacity = '1';
    });

    document.getElementById('statTotalPredictions').textContent = data.summary.total_predictions;
    document.getElementById('statAvgProfit').textContent = formatCurrency(data.summary.avg_profit);
    document.getElementById('statAvgHealth').textContent = `${data.summary.avg_health_score}/100`;
    document.getElementById('statBestProfit').textContent = formatCurrency(data.summary.best_profit);

    drawProfitTrend(data.labels, data.profits);
    drawRiskPie(data.risk_distribution);
    drawRevExpChart(data.labels, data.revenues, data.expenses);
    drawFeatureChart(data.feature_importances, 'featureChart');
  } catch (error) {
    console.error('Dashboard load error:', error);
  }
}

function drawProfitTrend(labels, profits) {
  const ctx = document.getElementById('profitTrendChart').getContext('2d');
  if (charts.profitTrend) charts.profitTrend.destroy();
  charts.profitTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.slice(-10),
      datasets: [{
        label: 'Predicted Profit',
        data: profits.slice(-10),
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.12)',
        tension: 0.38,
        fill: true,
        pointBackgroundColor: '#2563eb',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    },
    options: chartDefaults('$')
  });
}

function drawRiskPie(risks) {
  const ctx = document.getElementById('riskPieChart').getContext('2d');
  if (charts.riskPie) charts.riskPie.destroy();
  charts.riskPie = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [{
        data: [risks['Low Risk'] || 0, risks['Medium Risk'] || 0, risks['High Risk'] || 0],
        backgroundColor: ['#16803c', '#b7791f', '#d92d20'],
        borderColor: '#ffffff',
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#667085', font: { size: 12, family: 'Inter' }, usePointStyle: true }
        }
      },
      cutout: '64%'
    }
  });
}

function drawRevExpChart(labels, revenues, expenses) {
  const ctx = document.getElementById('revExpChart').getContext('2d');
  if (charts.revExp) charts.revExp.destroy();
  charts.revExp = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.slice(-8),
      datasets: [
        { label: 'Revenue', data: revenues.slice(-8), backgroundColor: '#0f766e', borderRadius: 6 },
        { label: 'Expenses', data: expenses.slice(-8), backgroundColor: '#d92d20', borderRadius: 6 }
      ]
    },
    options: chartDefaults('$')
  });
}

function drawFeatureChart(importances, canvasId) {
  if (!importances || Object.keys(importances).length === 0) return;
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (charts[canvasId]) charts[canvasId].destroy();

  const labels = Object.keys(importances).map((key) => titleCase(key.replaceAll('_', ' ')));
  const values = Object.values(importances).map((value) => Number((value * 100).toFixed(1)));
  const colors = ['#2563eb', '#0f766e', '#16803c', '#b7791f', '#0e7490'];

  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ label: 'Importance (%)', data: values, backgroundColor: colors, borderRadius: 6 }]
    },
    options: {
      ...chartDefaults('%'),
      indexAxis: 'y'
    }
  });
}

async function handlePredict(event) {
  event.preventDefault();
  const btn = document.getElementById('predictBtn');
  const btnText = document.getElementById('predictBtnText');
  const spinner = document.getElementById('predictSpinner');

  btnText.classList.add('d-none');
  spinner.classList.remove('d-none');
  btn.disabled = true;

  const payload = {
    revenue: parseFloat(document.getElementById('p_revenue').value),
    expenses: parseFloat(document.getElementById('p_expenses').value),
    marketing_spend: parseFloat(document.getElementById('p_marketing').value),
    employee_count: parseInt(document.getElementById('p_employees').value, 10),
    operational_cost: parseFloat(document.getElementById('p_opex').value),
    report_name: document.getElementById('p_name').value.trim() || 'Business Analysis'
  };

  try {
    const res = await apiRequest('/api/predictions/predict', 'POST', payload);
    const data = await res.json();

    if (res.ok) {
      displayResults(data);
      currentPredictionId = data.prediction_id;
      loadDashboard();
    } else {
      alert(data.error || 'Prediction failed. Please check your inputs.');
    }
  } catch (error) {
    alert(error.message || 'Prediction failed.');
  } finally {
    btnText.classList.remove('d-none');
    spinner.classList.add('d-none');
    btn.disabled = false;
  }
}

function displayResults(data) {
  document.getElementById('resultsEmpty').classList.add('d-none');
  document.getElementById('resultsPanel').classList.remove('d-none');

  const profit = data.predicted_profit || 0;
  const profitEl = document.getElementById('r_profit');
  profitEl.textContent = formatCurrency(profit);
  profitEl.style.color = profit >= 0 ? 'var(--green)' : 'var(--red)';
  document.getElementById('r_id').textContent = `#${data.prediction_id}`;

  const health = Number(data.health_score || 0);
  document.getElementById('r_health').textContent = `${health}/100`;
  const bar = document.getElementById('r_healthBar');
  bar.style.width = `${Math.max(0, Math.min(100, health))}%`;
  bar.style.background = health >= 70 ? 'var(--green)' : health >= 40 ? 'var(--amber)' : 'var(--red)';

  const riskEl = document.getElementById('r_risk');
  riskEl.textContent = data.risk_level || '--';
  riskEl.style.color = { 'Low Risk': 'var(--green)', 'Medium Risk': 'var(--amber)', 'High Risk': 'var(--red)' }[data.risk_level] || 'var(--text)';

  document.getElementById('r_margin').textContent = `${Number(data.metrics.profit_margin || 0).toFixed(1)}%`;
  document.getElementById('r_expenseRatio').textContent = `${Number(data.metrics.expense_ratio || 0).toFixed(1)}%`;
  document.getElementById('r_roi').textContent = `${Number(data.metrics.marketing_roi || 0).toFixed(2)}x`;

  const suggestions = document.getElementById('r_suggestions');
  suggestions.innerHTML = '';
  (data.suggestions || []).forEach((suggestion) => {
    suggestions.appendChild(createSuggestion(suggestion));
  });
}

function createSuggestion(suggestion) {
  const item = document.createElement('div');
  item.className = `suggestion-item ${suggestion.type || 'info'}`;

  const title = document.createElement('div');
  title.className = 'suggestion-title';
  const icon = document.createElement('i');
  icon.className = `bi ${suggestion.icon || iconForType(suggestion.type)}`;
  title.appendChild(icon);
  title.appendChild(document.createTextNode(suggestion.title || 'Recommendation'));

  const message = document.createElement('div');
  message.className = 'suggestion-msg';
  message.textContent = suggestion.message || '';

  item.appendChild(title);
  item.appendChild(message);
  return item;
}

async function runWhatIf() {
  const getVal = (id) => {
    const value = document.getElementById(id).value;
    return value ? parseFloat(value) : null;
  };

  const original = {
    revenue: getVal('w_o_revenue'),
    expenses: getVal('w_o_expenses'),
    marketing_spend: getVal('w_o_marketing'),
    employee_count: getVal('w_o_employees'),
    operational_cost: getVal('w_o_opex')
  };
  const modified = {
    revenue: getVal('w_m_revenue'),
    expenses: getVal('w_m_expenses'),
    marketing_spend: getVal('w_m_marketing'),
    employee_count: getVal('w_m_employees'),
    operational_cost: getVal('w_m_opex')
  };

  const allFilled = [original, modified].every((scenario) => Object.values(scenario).every((value) => value !== null));
  if (!allFilled) {
    alert('Please fill all fields in both scenarios.');
    return;
  }

  const btn = document.getElementById('compareBtn');
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
  btn.disabled = true;

  try {
    const res = await apiRequest('/api/predictions/what-if', 'POST', { original, modified });
    const data = await res.json();

    if (res.ok) {
      document.getElementById('whatifResults').classList.remove('d-none');
      document.getElementById('w_o_profit').textContent = formatCurrency(data.original.predicted_profit);
      document.getElementById('w_o_risk').textContent = data.original.risk_level;
      document.getElementById('w_o_health').textContent = `${data.original.health_score}/100`;
      document.getElementById('w_m_profit').textContent = formatCurrency(data.modified.predicted_profit);
      document.getElementById('w_m_risk').textContent = data.modified.risk_level;
      document.getElementById('w_m_health').textContent = `${data.modified.health_score}/100`;

      const diff = data.comparison;
      const diffProfit = document.getElementById('w_diff_profit');
      diffProfit.textContent = `${diff.profit_change >= 0 ? '+' : ''}${formatCurrency(diff.profit_change)}`;
      diffProfit.style.color = diff.profit_change >= 0 ? 'var(--green)' : 'var(--red)';
      document.getElementById('w_diff_summary').textContent = diff.summary;
    } else {
      alert(data.error || 'What-if analysis failed.');
    }
  } catch (error) {
    alert(error.message || 'What-if analysis failed.');
  } finally {
    btn.innerHTML = '<i class="bi bi-arrows-collapse d-block fs-4 mb-1"></i>Compare';
    btn.disabled = false;
  }
}

async function loadHistory() {
  const tbody = document.getElementById('historyTableBody');
  tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading...</td></tr>';

  try {
    const res = await apiRequest('/api/predictions/history');
    const data = await res.json();

    if (!data.predictions || data.predictions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No predictions yet. <button class="btn btn-link p-0 align-baseline" onclick="showSection('predict')">Make your first prediction</button></td></tr>`;
      return;
    }

    tbody.innerHTML = '';
    data.predictions.forEach((prediction) => {
      const riskClass = { 'Low Risk': 'risk-low', 'Medium Risk': 'risk-medium', 'High Risk': 'risk-high' }[prediction.risk_level] || '';
      const healthClass = prediction.health_score >= 60 ? 'health-good' : prediction.health_score >= 40 ? 'health-fair' : 'health-poor';
      const profitColor = prediction.predicted_profit >= 0 ? 'var(--green)' : 'var(--red)';
      const date = new Date(prediction.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' });

      tbody.insertAdjacentHTML('beforeend', `
        <tr>
          <td>#${prediction.id}</td>
          <td>${escapeHTML(date)}</td>
          <td>${formatCurrency(prediction.revenue)}</td>
          <td>${formatCurrency(prediction.expenses)}</td>
          <td style="color:${profitColor}; font-weight:800">${formatCurrency(prediction.predicted_profit)}</td>
          <td><span class="risk-badge ${riskClass}">${escapeHTML(prediction.risk_level)}</span></td>
          <td><span class="${healthClass}">${prediction.health_score}/100</span></td>
          <td>
            <button class="btn btn-outline-danger btn-sm py-1 px-2" onclick="deletePrediction(${prediction.id})" aria-label="Delete prediction ${prediction.id}">
              <i class="bi bi-trash"></i>
            </button>
            <button class="btn btn-outline-success btn-sm py-1 px-2 ms-1" onclick="exportPDF(${prediction.id})" aria-label="Export prediction ${prediction.id}">
              <i class="bi bi-file-earmark-pdf"></i>
            </button>
          </td>
        </tr>
      `);
    });
  } catch (error) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger py-4">Error loading history.</td></tr>';
  }
}

async function deletePrediction(id) {
  if (!confirm('Delete this prediction?')) return;
  try {
    const res = await apiRequest(`/api/predictions/${id}`, 'DELETE');
    if (res.ok) {
      loadHistory();
      loadDashboard();
    }
  } catch (error) {
    alert(error.message || 'Delete failed.');
  }
}

async function loadModelInfo() {
  try {
    const res = await apiRequest('/api/predictions/model-info');
    const data = await res.json();

    document.getElementById('m_r2').textContent = `${((data.r2_score || 0) * 100).toFixed(1)}%`;
    document.getElementById('m_mae').textContent = formatCurrency(data.mae || 0);
    document.getElementById('m_rmse').textContent = formatCurrency(data.rmse || 0);
    document.getElementById('m_trees').textContent = data.n_estimators || 200;

    if (data.feature_importances) {
      drawFeatureChart(data.feature_importances, 'modelFeatureChart');
    }
  } catch (error) {
    console.error('Model info error:', error);
  }
}

async function exportPDF(predId) {
  const response = await fetch(`/api/exports/pdf/${predId}`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  if (!response.ok) {
    alert('PDF export failed.');
    return;
  }
  const blob = await response.blob();
  downloadBlob(blob, `bizoptima_report_${predId}.pdf`);
}

async function exportCSV() {
  const response = await fetch('/api/exports/csv', {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  if (!response.ok) {
    alert('CSV export failed. Run at least one prediction first.');
    return;
  }
  const blob = await response.blob();
  downloadBlob(blob, 'bizoptima_predictions.csv');
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '--';
  const number = Number(value);
  const abs = Math.abs(number);
  const sign = number < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

function chartDefaults(unit = '') {
  return {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: { color: '#667085', font: { size: 12, family: 'Inter' }, usePointStyle: true }
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const raw = ctx.parsed.y ?? ctx.parsed.x ?? ctx.raw;
            return unit === '$' ? ` ${formatCurrency(raw)}` : ` ${ctx.raw}${unit}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#667085', font: { size: 11, family: 'Inter' } },
        grid: { color: '#e6edf5' }
      },
      y: {
        ticks: { color: '#667085', font: { size: 11, family: 'Inter' } },
        grid: { color: '#e6edf5' }
      }
    }
  };
}

function iconForType(type) {
  return {
    success: 'bi-check-circle',
    warning: 'bi-exclamation-triangle',
    danger: 'bi-exclamation-octagon',
    info: 'bi-info-circle'
  }[type] || 'bi-lightbulb';
}

function titleCase(value) {
  return value.replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  })[char]);
}
