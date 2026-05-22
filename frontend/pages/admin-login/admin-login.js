document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const inputId = btn.dataset.target;
      const input = document.getElementById(inputId);
      if (!input) return;

      if (input.type === 'password') {
        input.type = 'text';
        btn.title = 'An mat khau';
      } else {
        input.type = 'password';
        btn.title = 'Hien thi mat khau';
      }
    });
  });

  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity .4s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 4000);
  });
});

const API_BASE = 'http://127.0.0.1:8000/api';

const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const res = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (res.ok) {
      console.log('API response:', data); // <-- thêm dòng này
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_role', data.user ? data.user.role : '');

      if (data.user && data.user.role === 'admin') {
        window.location.href = '/admin-home/';
        return;
      }

      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_role');
      alert('Tai khoan khong co quyen admin');
    } else {
      alert('Dang nhap that bai');
    }
  });
}
