// Shared authentication helpers
function getToken() {
  return localStorage.getItem('access_token');
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null');
  } catch (error) {
    return null;
  }
}

function saveSession(data) {
  if (!data || !data.access_token || !data.user) return;
  localStorage.setItem('access_token', data.access_token);
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token);
  }
  localStorage.setItem('user', JSON.stringify(data.user));
}

function clearSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

function logout() {
  clearSession();
  window.location.href = '/login';
}

function showAlert(message, type = 'info') {
  const box = document.getElementById('alertBox');
  if (!box) return;
  box.className = `alert alert-${type}`;
  box.textContent = message;
  box.classList.remove('d-none');
}
