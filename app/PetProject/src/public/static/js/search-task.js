        document.getElementById('searchTaskForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const taskId = document.getElementById('task_id').value;
            const errorMessage = document.getElementById('errorMessage');
            const resultContainer = document.getElementById('resultContainer');

            // Скрываем предыдущие результаты и ошибки
            errorMessage.style.display = 'none';
            resultContainer.style.display = 'none';

            try {
                const response = await fetch(`/tasks/${taskId}`);

                if (!response.ok) {
                    if (response.status === 404) {
                        errorMessage.textContent = 'Task not found. Please check the ID and try again.';
                    } else {
                        errorMessage.textContent = `Error: ${response.statusText}`;
                    }
                    errorMessage.style.display = 'block';
                    return;
                }

                const task = await response.json();

                document.getElementById('taskId').textContent = task.id;
                document.getElementById('taskTitle').textContent = task.title || 'N/A';
                document.getElementById('taskDescription').textContent = task.description || 'N/A';
                document.getElementById('taskAuthor').textContent = task.author_name || (task.author?.username || 'N/A');

                resultContainer.style.display = 'block';

            } catch (error) {
                errorMessage.textContent = `Error: ${error.message}`;
                errorMessage.style.display = 'block';
                console.error('Search task error:', error);
            }
        });