        document.getElementById('searchUserForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const userIdentifier = document.getElementById('user_id_or_username').value.trim();
            const errorMessage = document.getElementById('errorMessage');
            const resultContainer = document.getElementById('resultContainer');

            errorMessage.style.display = 'none';
            resultContainer.style.display = 'none';

            try {
                const response = await fetch(`/users/${userIdentifier}`);

                if (!response.ok) {
                    if (response.status === 404) {
                        errorMessage.textContent = 'User not found. Please check the ID/username and try again.';
                    } else {
                        errorMessage.textContent = `Error: ${response.statusText}`;
                    }
                    errorMessage.style.display = 'block';
                    return;
                }

                const user = await response.json();

                document.getElementById('userId').textContent = user.id || 'N/A';
                document.getElementById('userUsername').textContent = user.username || 'N/A';
                document.getElementById('userEmail').textContent = user.email || 'N/A';
                document.getElementById('userAge').textContent = user.age || 'N/A';

                resultContainer.style.display = 'block';

            } catch (error) {
                errorMessage.textContent = `Error: ${error.message}`;
                errorMessage.style.display = 'block';
                console.error('Search user error:', error);
            }
        });