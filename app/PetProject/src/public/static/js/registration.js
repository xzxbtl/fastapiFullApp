document.getElementById('registration-form').addEventListener('submit', async function(e){
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('.submit-btn');
    const btnText = form.querySelector('#btn-text');
    const spinner = form.querySelector('#spinner');
    const formErrors = document.getElementById('form-errors');

    document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
    formErrors.style.display = 'none';

    btnText.textContent = 'Processing...';
    spinner.style.display = 'block';
    submitBtn.disabled = true;

    try{
        const regData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            confirm_password: document.getElementById('confirmPassword').value,
        };

        const response = await fetch("/api/auth/registration/", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(regData)
        });

        const data = await response.json()

        if (!response.ok) {
            if(response.status === 401) {
                formErrors.textContent = "Password mismatch";
                formErrors.style.display = 'block';
            }
            else if (response.status === 400){
                formErrors.textContent = "User with this username or email already exists";
                formErrors.style.display = 'block';
            }
            else if (response.status === 422 && data.detail) {
                if (Array.isArray(data.detail)) {
                    data.detail.forEach(error => {
                        const field = error.loc[1];
                        const errorElement = document.getElementById(`${field}-error`);
                        if(errorElement) errorElement.textContent = error.msg;
                    });
                } else {
                    formErrors.textContent = data.detail || 'Incorrect username or password';
                    formErrors.style.display = 'block';
                }
            } else {
                formErrors.textContent = data.detail || 'Error Authorization';
                formErrors.style.display = 'block';
            }
            throw new Error(data.detail || 'Registration failed');
        }

        window.location.href = '/';

    } catch (error){
        console.error('Registration error:', error);
        if (!formErrors.textContent) {
            formErrors.textContent = 'Error';
            formErrors.style.display = 'block';
        }
    } finally {
        btnText.textContent = 'Register';
        spinner.style.display = 'none';
        submitBtn.disabled = false;
    }
})