document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('callForm');
    const resultDiv = document.getElementById('jrpcResponse');

    if (!form || !resultDiv) {
        console.error('Форма или элемент для вывода результата не найдены!');
        return;
    }

    form.addEventListener('submit', handleFormSubmit);

    async function handleFormSubmit(event) {
        event.preventDefault();

        try {
            const formData = new FormData(form);
            const response = await sendFormData(form.action, formData);
            const responseData = await parseResponse(response);
            displayResult(responseData);
        } catch (error) {
            console.error('Ошибка при отправке формы:', error);
            resultDiv.innerHTML = 'Произошла ошибка при отправке формы.';
        }
    }

    async function sendFormData(url, formData) {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        return response;
    }

    async function parseResponse(response) {
        try {
            return await response.json();
        } catch (error) {
            throw new Error('Ошибка при парсинге JSON');
        }
    }

    function displayResult(data) {
        resultDiv.innerHTML = JSON.stringify(data, null, 2);
    }
});