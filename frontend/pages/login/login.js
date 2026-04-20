/* ============================================================
   TechShop – Main JavaScript
   File: static/js/main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

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
            if (q) window.location.href = `/products/?search=${encodeURIComponent(q)}`;
        });
    }

});