document.getElementById('createTaskForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.querySelector('#createTaskForm .submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Creating...';

    try {
        const taskData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim() || null,
        };

        // Валидация
        if (!taskData.title || taskData.title.length > 80) {
            throw new Error('Title must be between 1-80 characters');
        }
        if (taskData.description && taskData.description.length > 300) {
            throw new Error('Description cannot exceed 300 characters');
        }

        const response = await fetch('/tasks/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(taskData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create task');
        }

        const result = await response.json();

        showResult(result);

    } catch (error) {
        showError(error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Task';
    }
});

function showResult(task) {
    const form = document.getElementById('createTaskForm');
    const resultContainer = document.getElementById('resultContainer');

    document.getElementById('resultId').textContent = task.id;
    document.getElementById('resultTitle').textContent = task.title;
    document.getElementById('resultAuthor').textContent = task.author_name || task.author?.username;

    form.style.display = 'none';
    resultContainer.style.display = 'block';
}

document.getElementById('createAnotherBtn').addEventListener('click', function() {
    document.getElementById('createTaskForm').style.display = 'block';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('createTaskForm').reset();
    updateCharCounters();
});


function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.textContent = message;

    const formContainer = document.querySelector('.form-container');
    formContainer.prepend(errorDiv);

    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}


document.getElementById('createAnotherBtn').addEventListener('click', function() {
    document.getElementById('createTaskForm').style.display = 'block';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('createTaskForm').reset();
});

function updateCharCounters() {
    const titleInput = document.getElementById('title');
    const descTextarea = document.getElementById('description');

    const titleCounter = document.getElementById('titleCounter');
    const descCounter = document.getElementById('descCounter');

    // Обновляем значения
    titleCounter.textContent = `${titleInput.value.length}/80`;
    descCounter.textContent = `${descTextarea.value.length}/300`;

    // Подсветка для заголовка
    updateCounterStyle(titleCounter, titleInput.value.length, 80);
    // Подсветка для описания
    updateCounterStyle(descCounter, descTextarea.value.length, 300);
    // Подсветка для автора
}

function updateCounterStyle(counterElement, currentLength, maxLength) {
    counterElement.classList.remove('warning', 'error');

    if (currentLength > maxLength * 0.9) {
        counterElement.classList.add('error');
    } else if (currentLength > maxLength * 0.7) {
        counterElement.classList.add('warning');
    }
}

document.getElementById('title').addEventListener('input', updateCharCounters);
document.getElementById('description').addEventListener('input', updateCharCounters);
document.getElementById('author_name').addEventListener('input', updateCharCounters);

document.addEventListener('DOMContentLoaded', updateCharCounters);