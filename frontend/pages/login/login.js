/* ============================================================
   TechShop – Main JavaScript
   File: static/js/main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    updateAuthHeader();

    /* ----------------------------------------------------------
       1. TAB SWITCHER – Đăng nhập / Đăng ký
    ---------------------------------------------------------- */
    const tabBtns   = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const panel = document.getElementById(`tab-${target}`);
            if (panel) panel.classList.add('active');
        });
    });

    /* ----------------------------------------------------------
       2. TOGGLE PASSWORD VISIBILITY
    ---------------------------------------------------------- */
    document.querySelectorAll('.toggle-pw').forEach(btn => {
        btn.addEventListener('click', () => {
            const inputId = btn.dataset.target;
            const input   = document.getElementById(inputId);
            if (!input) return;

            if (input.type === 'password') {
                input.type = 'text';
                btn.title  = 'Ẩn mật khẩu';
            } else {
                input.type = 'password';
                btn.title  = 'Hiển thị mật khẩu';
            }
        });
    });

    /* ----------------------------------------------------------
       3. AUTO-DISMISS ALERTS (sau 4 giây)
    ---------------------------------------------------------- */
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity .4s';
            alert.style.opacity    = '0';
            setTimeout(() => alert.remove(), 400);
        }, 4000);
    });

    /* ----------------------------------------------------------
       4. CLIENT-SIDE FORM VALIDATION – Đăng ký
    ---------------------------------------------------------- */
    const registerForm = document.querySelector('#tab-register form');
    if (registerForm) {
        registerForm.addEventListener('submit', e => {
            const pw1 = registerForm.querySelector('[name="password1"]');
            const pw2 = registerForm.querySelector('[name="password2"]');

            if (pw1 && pw2 && pw1.value !== pw2.value) {
                e.preventDefault();
                showInlineError(pw2, 'Mật khẩu xác nhận không khớp.');
            }

            const username = registerForm.querySelector('[name="username"]');
            if (username && username.value.trim().length < 5) {
                e.preventDefault();
                showInlineError(username, 'Tên đăng nhập phải có ít nhất 5 ký tự.');
            }
        });
    }

    function showInlineError(input, message) {
        // Xóa lỗi cũ nếu có
        const old = input.parentElement.querySelector('.inline-error');
        if (old) old.remove();

        const err = document.createElement('span');
        err.className   = 'inline-error';
        err.textContent = message;
        err.style.cssText = 'color:#c0151e;font-size:.8rem;margin-top:4px;display:block;';
        input.parentElement.appendChild(err);
        input.focus();
    }

    /* ----------------------------------------------------------
       5. SEARCH BAR – Enter trigger
    ---------------------------------------------------------- */
    const searchInput = document.querySelector('.search-bar input');
    const searchBtn   = document.querySelector('.search-btn');

    if (searchInput && searchBtn) {
        searchInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') searchBtn.click();
        });
        searchBtn.addEventListener('click', () => {
            const q = searchInput.value.trim();
            if (q) window.location.href = `/shop/?search=${encodeURIComponent(q)}`;
        });
    }

});

function updateAuthHeader() {
    const accountBtn = document.getElementById('accountBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const isLoggedIn = Boolean(localStorage.getItem('access_token'));

    if (accountBtn) {
        accountBtn.hidden = isLoggedIn;
    }

    if (logoutBtn) {
        logoutBtn.hidden = !isLoggedIn;
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login/';
        });
    }
}

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
            body: JSON.stringify({ email, password, guest_session_id: getGuestSessionId() })
        });

        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user_role', data.user ? data.user.role : '');
            if (data.user && data.user.role === 'admin') {
                window.location.href = '/admin-home/';
            } else {
                window.location.href = getSafeNextUrl() || '/shop/';
            }
        } else {
            alert('Đăng nhập thất bại');
        }
    });
}
const registerFormApi = document.getElementById('registerForm');

if (registerFormApi) {
    registerFormApi.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fullName = document.getElementById('reg-full-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const phone = document.getElementById('reg-phone').value.trim();
        const password1 = document.getElementById('reg-password').value;
        const password2 = document.getElementById('reg-password2').value;

        if (password1 !== password2) {
            alert('Mật khẩu xác nhận không khớp.');
            return;
        }

        const res = await fetch(`${API_BASE}/auth/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                phone: phone,
                password: password1
            })
        });

        const data = await res.json();

        if (res.ok) {
            alert('Đăng ký thành công. Vui lòng đăng nhập.');
            document.querySelector('[data-tab="login"]').click();
        } else {
            const message = Object.values(data).flat().join('\n');
            alert(message || 'Đăng ký thất bại.');
        }
    });
}

function getGuestSessionId() {
    let sessionId = localStorage.getItem('guest_session_id');
    if (!sessionId) {
        const randomPart = crypto.randomUUID
            ? crypto.randomUUID().replace(/-/g, '')
            : `${Date.now()}${Math.random().toString(16).slice(2)}`;
        sessionId = `guest_${randomPart}`;
        localStorage.setItem('guest_session_id', sessionId);
    }
    return sessionId;
}

function getSafeNextUrl() {
    const next = new URLSearchParams(window.location.search).get('next');
    if (!next || !next.startsWith('/') || next.startsWith('//')) {
        return '';
    }
    return next;
}

const forgotPasswordForm = document.getElementById('forgotPasswordForm');
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('forgot-email').value.trim();
        const button = forgotPasswordForm.querySelector('button[type="submit"]');
        const oldText = button.textContent;
        button.disabled = true;
        button.textContent = 'Đang gửi...';

        try {
            const res = await fetch(`${API_BASE}/auth/password-reset/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (!res.ok) {
                showAuthMessage('forgotPasswordMessage', getApiMessage(data, 'Không thể gửi liên kết đặt lại mật khẩu.'), 'error');
                return;
            }

            const debugLink = data.reset_url
                ? `<br><a href="${data.reset_url}">Mở link đặt lại mật khẩu</a>`
                : '';
            showAuthMessage('forgotPasswordMessage', `${data.message || 'Vui lòng kiểm tra email của bạn.'}${debugLink}`, 'success');
        } catch (error) {
            showAuthMessage('forgotPasswordMessage', 'Không thể kết nối backend.', 'error');
        } finally {
            button.disabled = false;
            button.textContent = oldText;
        }
    });
}

const resetPasswordForm = document.getElementById('resetPasswordForm');
if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resetData = getResetPathData();
        if (!resetData) {
            showAuthMessage('resetPasswordMessage', 'Liên kết đặt lại mật khẩu không hợp lệ.', 'error');
            return;
        }

        const password = document.getElementById('reset-password').value;
        const passwordConfirm = document.getElementById('reset-password-confirm').value;
        if (password !== passwordConfirm) {
            showAuthMessage('resetPasswordMessage', 'Mật khẩu xác nhận không khớp.', 'error');
            return;
        }

        const button = resetPasswordForm.querySelector('button[type="submit"]');
        const oldText = button.textContent;
        button.disabled = true;
        button.textContent = 'Đang xử lý...';

        try {
            const res = await fetch(`${API_BASE}/auth/password-reset/confirm/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: resetData.uid,
                    token: resetData.token,
                    password,
                    password_confirm: passwordConfirm
                })
            });
            const data = await res.json();

            if (!res.ok) {
                showAuthMessage('resetPasswordMessage', getApiMessage(data, 'Không thể đặt lại mật khẩu.'), 'error');
                return;
            }

            showAuthMessage('resetPasswordMessage', 'Đặt lại mật khẩu thành công. Bạn có thể đăng nhập bằng mật khẩu mới.', 'success');
            resetPasswordForm.reset();
        } catch (error) {
            showAuthMessage('resetPasswordMessage', 'Không thể kết nối backend.', 'error');
        } finally {
            button.disabled = false;
            button.textContent = oldText;
        }
    });
}

function getResetPathData() {
    const parts = window.location.pathname.split('/').filter(Boolean);
    const resetIndex = parts.indexOf('reset-password');
    if (resetIndex === -1 || !parts[resetIndex + 1] || !parts[resetIndex + 2]) {
        return null;
    }

    return {
        uid: parts[resetIndex + 1],
        token: parts[resetIndex + 2]
    };
}

function showAuthMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.hidden = false;
    element.className = `auth-message ${type}`;
    element.innerHTML = message;
}

function getApiMessage(data, fallback) {
    if (!data || typeof data !== 'object') return fallback;
    if (data.message) return data.message;
    if (data.error) return data.error;
    if (data.detail) return data.detail;

    const values = Object.values(data).flat();
    return values.length ? values.join('\n') : fallback;
}
