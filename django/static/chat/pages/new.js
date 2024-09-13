function renderNewRoomPage() {
	fetchAPI('/api/isAuthenticated').then(data => {
		if (!data.isAuthenticated) return router.navigate('/sign_in/');
	});

	const fieldsHtml = [
		{ name: 'input-group-name', label: 'Name (required)', type: 'text' },
		{ name: 'input-group-description', label: 'Description', type: 'text' }
	].map(renderField).join('');

	document.getElementById('app').innerHTML = `
		<div class="all-screen">
			<div class="form-div">
				<form method="POST" class="sign-form">
					<h3 class="sign-title">New chat group</h3>
					${fieldsHtml}
					<p class="error-message" id="error-message"></p>
					<input type="submit" value="Create"/>
				</form>
			</div>
		</div>
	`;

	document.querySelector('.sign-form').addEventListener('submit', async event => {
		event.preventDefault();
		['name', 'description'].forEach(field => document.getElementById(`error-input-group-${field}`).textContent = '');
		document.getElementById('error-message').textContent = '';

		const response = await fetch('/chat/new/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
			body: JSON.stringify({
				name: document.getElementById('input-group-name').value,
				description: document.getElementById('input-group-description').value
			})
		});

		const responseData = await response.json();
		if (responseData.success) return router.navigate(`/chat/${responseData.room_id}`);
		['name', 'description'].forEach(field => document.getElementById(`error-input-group-${field}`).textContent = responseData[field]);
		document.getElementById('error-message').textContent = responseData.message || "The server encountered an unexpected error.";
	});
}
