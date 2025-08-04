document.addEventListener('DOMContentLoaded', function() {
    // Инициализация счетчиков символов
    initCharCounters();

    // Обработчик формы поиска
    document.getElementById('searchUserForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleUserSearch();
    });

    // Обработчик формы редактирования
    document.getElementById('editUserForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleUserUpdate();
    });

    // Обработчик кнопки "Edit Another User"
    document.getElementById('editAnotherBtn').addEventListener('click', resetToSearchForm);

    // Обработчик ввода пароля
    document.getElementById('password').addEventListener('input', updatePasswordStrength);
});

function resetPasswordStrength() {
    const meter = document.getElementById('strengthMeter');
    meter.style.width = '0%';
    meter.style.backgroundColor = '';
}

async function handleUserSearch() {
    const userIdentifier = document.getElementById('user_id_or_username').value.trim();
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.style.display = 'none';

    try {
        const response = await fetch(`/users/admin/search/${userIdentifier}`);

        if (!response.ok) {
            errorMessage.textContent = response.status === 404
                ? 'User not found. Please check the ID/username and try again.'
                : `Error: ${response.statusText}`;
            errorMessage.style.display = 'block';
            return;
        }

        const user = await response.json();
        showEditForm(user);
    } catch (error) {
        console.error('Search error:', error);
        errorMessage.textContent = 'An error occurred while fetching user data.';
        errorMessage.style.display = 'block';
    }
}

function showEditForm(user) {
    // Заполняем форму редактирования
    document.getElementById('user_id').value = user.id;
    document.getElementById('username').value = user.username || '';
    document.getElementById('editUsername').textContent = user.username || '';
    document.getElementById('age').value = user.age || '';
    document.getElementById('email').value = user.email || '';
    document.getElementById('bio').value = user.bio || '';
    document.getElementById('password').value = '';

    const accessLevelElement = document.getElementById('access_level');
    if (accessLevelElement) {
        accessLevelElement.value = user.access_level || 1;
    }

    // Обновляем счетчики символов
    updateAllCharCounters();

    // Переключаем видимость
    document.getElementById('searchContainer').style.display = 'none';
    document.getElementById('editContainer').style.display = 'block';
}

async function handleUserUpdate() {
    const formData = {
        id: document.getElementById('user_id').value,
        username: document.getElementById('username').value,
        age: document.getElementById('age').value || null,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value || null,
        bio: document.getElementById('bio').value || null
    };

    const accessLevelElement = document.getElementById('access_level');
    if (accessLevelElement) {
        formData.access_level = accessLevelElement.value;
    }

    try {
        const updateResponse = await fetch(`/users/edit/${formData.id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!updateResponse.ok) {
            throw new Error(await updateResponse.text());
        }

        const updatedUser = await updateResponse.json();
        showResult(updatedUser);

    } catch (error) {
        console.error('Update error:', error);
        alert('Error updating user: ' + error.message);
    }
}

function showResult(user) {
    // Заполняем данные результата
    document.getElementById('resultId').textContent = user.id;
    document.getElementById('resultUsername').textContent = user.username || 'N/A';
    document.getElementById('resultEmail').textContent = user.email || 'N/A';
    document.getElementById('resultAge').textContent = user.age || 'N/A';
    document.getElementById('resultAccessLevel').textContent = user.access_level || 'N/A';
    document.getElementById('resultBio').textContent = user.bio || 'N/A';

    // Переключаем видимость
    document.getElementById('editContainer').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'block';
}

function resetToSearchForm() {
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('searchContainer').style.display = 'block';
    document.getElementById('searchUserForm').reset();
    document.getElementById('user_id_or_username').focus();
    resetPasswordStrength()
}

function updatePasswordStrength() {
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

    meter.style.backgroundColor =
        strength <= 1 ? '#e74c3c' :
        strength <= 3 ? '#f39c12' : '#2ecc71';
}

function updateUserCounterStyle(counterElement, currentLength, maxLength) {
    counterElement.classList.remove('warning', 'error');

    if (currentLength > maxLength * 0.9) {
        counterElement.classList.add('error');
    } else if (currentLength > maxLength * 0.7) {
        counterElement.classList.add('warning');
    }
}

function updateAllCharCounters() {
    const fields = [
        {id: 'username', max: 64, counter: 'usernameCounter'},
        {id: 'email', max: 64, counter: 'emailCounter'},
        {id: 'bio', max: 140, counter: 'bioCounter'},
        {id: 'password', max: 64, counter: 'passwordCounter'}
    ];

    fields.forEach(field => {
        const input = document.getElementById(field.id);
        const counter = document.getElementById(field.counter);

        if (input && counter) {
            const length = input.value.length;
            counter.textContent = `${length}/${field.max}`;
            updateUserCounterStyle(counter, length, field.max);
        }
    });
}

function initCharCounters() {
    const fields = [
        {id: 'username', max: 64, counter: 'usernameCounter'},
        {id: 'email', max: 64, counter: 'emailCounter'},
        {id: 'bio', max: 140, counter: 'bioCounter'},
        {id: 'password', max: 64, counter: 'passwordCounter'}
    ];

    fields.forEach(field => {
        const input = document.getElementById(field.id);
        const counter = document.getElementById(field.counter);

        if (input && counter) {
            input.addEventListener('input', () => {
                const length = input.value.length;
                counter.textContent = `${length}/${field.max}`;
                updateUserCounterStyle(counter, length, field.max);
            });

            counter.textContent = `0/${field.max}`;
        }
    });
}