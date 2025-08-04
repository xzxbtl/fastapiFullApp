document.getElementById('password').addEventListener('input', function() {
    const password = this.value;
    const meter = document.getElementById('strengthMeter');
    let strength = 0;

    if (password.length > 0) strength += 1;
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;

    const width = strength * 20;
    meter.style.width = width + '%';

    if (strength <= 1) {
        meter.style.backgroundColor = '#e74c3c';
    } else if (strength <= 3) {
        meter.style.backgroundColor = '#f39c12';
    } else {
        meter.style.backgroundColor = '#2ecc71';
    }
});


document.getElementById('createUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.querySelector('#createUserForm .submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Creating...';

    try {
        const userData = {
            username: document.getElementById('username').value,
            age: document.getElementById('age').value || 18,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            access_level: parseInt(document.getElementById('access_level').value)
        };

        const response = await fetch('/users/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create user');
        }

        const result = await response.json();
        showResultUser(result);

    } catch (error) {
        showError(error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create User';
    }
});

function showResultUser(user) {
    const form = document.getElementById('createUserForm');
    const resultUserContainer = document.getElementById('resultContainer');

    document.getElementById('resultId').textContent = user.id;
    document.getElementById('resultUsername').textContent = user.username;
    document.getElementById('resultAge').textContent = user.age ? user.age : 18;
    document.getElementById('resultPassword').textContent = user.password;
    document.getElementById('resultEmail').textContent = user.email;
    document.getElementById('resultAccess').textContent = user.access_level;

    form.style.display = 'none';
    resultUserContainer.style.display = 'block';
}


document.getElementById('createAnotherBtn').addEventListener('click', function() {
    document.getElementById('createUserForm').style.display = 'block';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('createUserForm').reset();
    updateUserCharCounters();
});


function updateUserCharCounters() {
    const username = document.getElementById('username');
    const password = document.getElementById('email');
    const email = document.getElementById('password');

    const usernameCounter = document.getElementById('usernameCounter')
    const passwordCounter = document.getElementById('passwordCounter')
    const emailCounter = document.getElementById('emailCounter')

    usernameCounter.textContent = `${username.value.length}/64`;
    passwordCounter.textContent = `${passwordCounter.value.length}/64`;
    emailCounter.textContent = `${emailCounter.value.length}/64`;


    // Подсветка для юзернейма
    updateUserCounterStyle(usernameCounter, username.value.length, 64);
    // Подсветка для пароля
    updateUserCounterStyle(passwordCounter, password.value.length, 64);
    // Подсветка для емеил
    updateUserCounterStyle(emailCounter, email.value.length, 64);
}


function updateUserCounterStyle(counterElement, currentLength, maxLength) {
    counterElement.classList.remove('warning', 'error');

    if (currentLength > maxLength * 0.9) {
        counterElement.classList.add('error');
    } else if (currentLength > maxLength * 0.7) {
        counterElement.classList.add('warning');
    }
}

document.getElementById('username').addEventListener('input', updateUserCharCounters);
document.getElementById('password').addEventListener('input', updateUserCharCounters);
document.getElementById('email').addEventListener('input', updateUserCharCounters);

document.addEventListener('DOMContentLoaded', updateUserCharCounters);