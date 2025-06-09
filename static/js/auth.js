document.addEventListener('DOMContentLoaded', function() {
    // Handle password visibility toggle
    const toggleButtons = document.querySelectorAll('.toggle-password');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent form submission
            e.stopPropagation(); // Stop event bubbling
            
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            
            // Toggle password visibility
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fas', 'fa-eye');
                icon.classList.add('fas', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fas', 'fa-eye-slash');
                icon.classList.add('fas', 'fa-eye');
            }
        });
    });

    // Alert dismissal with fade out animation
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 300);
            });
        }
    });

    // Auto-dismiss success alerts after 5 seconds
    const autoAlerts = document.querySelectorAll('.alert-success');
    autoAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });

    // Add shake animation to error alerts
    const errorAlerts = document.querySelectorAll('.alert-error, .alert-danger');
    errorAlerts.forEach(alert => {
        alert.classList.add('shake');
    });

    // Form validation
    const authForm = document.querySelector('.auth-form');
    if (authForm) {
        const passwordInput = authForm.querySelector('#password');
        const confirmPasswordInput = authForm.querySelector('#confirm_password');
        const phoneInput = authForm.querySelector('#phone');

        // Clear custom validity messages when input changes
        const inputs = authForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.setCustomValidity('');
            });
        });

        // Phone number formatting
        if (phoneInput) {
            phoneInput.addEventListener('input', function(e) {
                let value = this.value.replace(/\D/g, '');
                if (value.length > 10) value = value.slice(0, 10);
                this.value = value;
                this.setCustomValidity(value.length === 10 ? '' : 'Phone number must be 10 digits');
            });
        }

        // Password match validation
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', function() {
                if (passwordInput.value === this.value) {
                    this.setCustomValidity('');
                } else {
                    this.setCustomValidity('Passwords do not match');
                }
            });
        }

        // Form submission
        authForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Validate phone number
            if (phoneInput && phoneInput.value.length !== 10) {
                phoneInput.setCustomValidity('Phone number must be 10 digits');
                isValid = false;
            }

            // Validate password match
            if (passwordInput && confirmPasswordInput && 
                passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity('Passwords do not match');
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
                // Show the first error message
                const firstInvalidInput = authForm.querySelector(':invalid');
                if (firstInvalidInput) {
                    firstInvalidInput.focus();
                }
            }
        });
    }
});

// Password strength checker
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    return strength;
}

// Update password field styling based on strength
function updatePasswordStrength(input, strength) {
    const strengthClasses = ['very-weak', 'weak', 'medium', 'strong', 'very-strong'];
    input.classList.remove(...strengthClasses);
    if (strength > 0) {
        input.classList.add(strengthClasses[strength - 1]);
    }
}

// Validate password match
function validatePasswordMatch(password, confirmPassword) {
    if (password.value === confirmPassword.value) {
        confirmPassword.setCustomValidity('');
        confirmPassword.classList.remove('mismatch');
    } else {
        confirmPassword.setCustomValidity('Passwords do not match');
        confirmPassword.classList.add('mismatch');
    }
}

// Form validation
function validateForm(form) {
    const password = form.querySelector('#password');
    const confirmPassword = form.querySelector('#confirm_password');
    const phone = form.querySelector('#phone');

    let isValid = true;

    if (password && confirmPassword) {
        if (password.value !== confirmPassword.value) {
            confirmPassword.setCustomValidity('Passwords do not match');
            isValid = false;
        } else {
            confirmPassword.setCustomValidity('');
        }
    }

    if (phone) {
        if (phone.value.length !== 10) {
            phone.setCustomValidity('Phone number must be 10 digits');
            isValid = false;
        } else {
            phone.setCustomValidity('');
        }
    }

    return isValid;
} 