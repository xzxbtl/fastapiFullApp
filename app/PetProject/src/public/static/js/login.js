        document.getElementById('login-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = form.querySelector('.submit-btn');
            const btnText = form.querySelector('#btn-text');
            const spinner = form.querySelector('#spinner');
            const formErrors = document.getElementById('form-errors');
            
            // Сброс ошибок
            document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
            formErrors.style.display = 'none';
            
            // Показать спиннер
            btnText.textContent = 'Processing...';
            spinner.style.display = 'block';
            submitBtn.disabled = true;
            
            try {
                const formData = {
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value,
                    confirm_password: document.getElementById('password').value,
                };
                
                const response = await fetch('/api/auth/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    if (response.status === 401) {
                        formErrors.textContent = "User not Found";
                        formErrors.style.display = 'block';
                    }
                    else if (response.status === 422 && data.detail) {
                        if (Array.isArray(data.detail)) {
                            data.detail.forEach(error => {
                                const field = error.loc[1];
                                const errorElement = document.getElementById(`${field}-error`);
                                if (errorElement) errorElement.textContent = error.msg;
                            });
                        } else {
                            formErrors.textContent = data.detail || 'Incorrect username or password';
                            formErrors.style.display = 'block';
                        }
                    } else {
                        formErrors.textContent = data.detail || 'Error Authorization';
                        formErrors.style.display = 'block';
                    }
                    throw new Error(data.detail || 'Login failed');
                }

                // Успешная авторизация
                window.location.href = '/'; // Редирект

            } catch (error) {
                console.error('Login error:', error);
                if (!formErrors.textContent) {
                    formErrors.textContent = 'Error';
                    formErrors.style.display = 'block';
                }
            } finally {
                btnText.textContent = 'Login';
                spinner.style.display = 'none';
                submitBtn.disabled = false;
            }
        });