// filepath: /c:/Users/DrPower/OneDrive/Documents/code/Gestion projet/Mashru3/static/js/scripts.js
const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#password');

togglePassword.addEventListener('click', function (e) {
    // Toggle the type attribute
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    // Toggle the eye slash icon
    this.classList.toggle('fa-eye-slash');
});