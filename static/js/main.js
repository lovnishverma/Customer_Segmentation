// ─────────────────────────────────────────────────────────────
//  Customer Segmentation — Frontend JS
// ─────────────────────────────────────────────────────────────

/** Sync slider → number input */
function syncInput(field) {
  if (field === 'income') {
    document.getElementById('annual_income').value =
      document.getElementById('income_slider').value;
  } else {
    document.getElementById('spending_score').value =
      document.getElementById('spending_slider').value;
  }
}

/** Sync number input → slider */
function syncSlider(field) {
  if (field === 'income') {
    document.getElementById('income_slider').value =
      document.getElementById('annual_income').value;
  } else {
    document.getElementById('spending_slider').value =
      document.getElementById('spending_score').value;
  }
}

/** Set example values */
function setValues(income, spending) {
  document.getElementById('annual_income').value  = income;
  document.getElementById('spending_score').value = spending;
  document.getElementById('income_slider').value  = income;
  document.getElementById('spending_slider').value= spending;
}

/** Main predict function */
async function predict() {
  const income   = document.getElementById('annual_income').value;
  const spending = document.getElementById('spending_score').value;

  if (!income || !spending) {
    showError('Please fill in both fields.');
    return;
  }

  // Show spinner
  document.getElementById('spinner').classList.remove('d-none');

  try {
    const formData = new FormData();
    formData.append('annual_income',  income);
    formData.append('spending_score', spending);

    const response = await fetch('/predict', {
      method: 'POST',
      body:   formData,
    });

    const data = await response.json();
    document.getElementById('spinner').classList.add('d-none');

    if (!response.ok || data.error) {
      showError(data.error || 'Prediction failed. Please try again.');
      return;
    }

    renderResult(data);

  } catch (err) {
    document.getElementById('spinner').classList.add('d-none');
    showError('Network error. Make sure the Flask server is running.');
  }
}

/** Render prediction result */
function renderResult(data) {
  const body = document.getElementById('result-body');

  // Distance bars (normalized)
  const maxDist = Math.max(...data.distances);
  const distBars = data.distances.map((d, i) => {
    const pct = maxDist > 0 ? ((maxDist - d) / maxDist * 100).toFixed(1) : 0;
    const isSelected = i === data.cluster_id;
    const color = isSelected ? data.color : '#cbd5e1';
    return `
      <div class="distance-bar-item">
        <div class="d-flex justify-content-between mb-1">
          <span>${isSelected ? '⭐ ' : ''}Cluster ${i}</span>
          <span>${pct}% match</span>
        </div>
        <div class="d-bar">
          <div class="d-bar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
      </div>`;
  }).join('');

  body.innerHTML = `
    <div class="result-cluster w-100">
      <div class="text-center mb-3">
        <div class="result-emoji">${data.emoji}</div>
        <div class="result-name" style="color:${data.color}">${data.cluster_name}</div>
        <span class="result-cluster-badge" style="background:${data.color}">
          Cluster ${data.cluster_id} of ${data.total_clusters - 1}
        </span>
      </div>

      <div class="result-info-grid">
        <div class="info-chip">
          <strong>Annual Income</strong>
          $${data.annual_income}k / year
        </div>
        <div class="info-chip">
          <strong>Spending Score</strong>
          ${data.spending_score} / 100
        </div>
        <div class="info-chip">
          <strong>Income Level</strong>
          ${data.income_level}
        </div>
        <div class="info-chip">
          <strong>Spending Level</strong>
          ${data.spending_level}
        </div>
      </div>

      <p class="text-muted small">${data.description}</p>

      <div class="strategy-box">
        <strong>💡 Marketing Strategy:</strong><br/>
        ${data.strategy}
      </div>

      <div class="distance-bar-wrap mt-3">
        <small class="text-muted fw-semibold">Cluster Match Scores:</small>
        <div class="mt-2">${distBars}</div>
      </div>
    </div>
  `;
}

/** Show error in result panel */
function showError(message) {
  const body = document.getElementById('result-body');
  body.innerHTML = `
    <div class="text-center text-danger">
      <div style="font-size:2.5rem">⚠️</div>
      <p class="mt-2 fw-semibold">${message}</p>
    </div>`;
}

// Allow Enter key to trigger prediction
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') predict();
});
