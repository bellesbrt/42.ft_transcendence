function renderAuth42Page() {
	const appElement = document.getElementById('app');

	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">403</p>
				<p class="error-title">Access Refused</p>
				<p class="error-infos">You should authorize the website to use your account.</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
