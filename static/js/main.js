// main.js - Interações SPAE

document.addEventListener('DOMContentLoaded', function () {
    // Alternar visibilidade da senha
    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('id_password');

    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', function () {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

            const icon = togglePasswordBtn.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-eye');
                icon.classList.toggle('bi-eye-slash');
            }
        });
    }

    // Preenchimento rápido de credenciais de demonstração
    const demoPills = document.querySelectorAll('.demo-pill');
    const usernameInput = document.getElementById('id_username');

    demoPills.forEach(function (pill) {
        pill.addEventListener('click', function () {
            const user = this.getAttribute('data-user');
            const pass = this.getAttribute('data-pass');

            if (usernameInput) {
                usernameInput.value = user;
            }
            if (passwordInput) {
                passwordInput.value = pass;
            }
            if (passwordInput) {
                passwordInput.focus();
            }
        });
    });
});
