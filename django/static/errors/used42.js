function renderUsed42Page() {
	const appElement = document.getElementById('app');

	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">403</p>
				<p class="error-title">Failed to Connect</p>
				<p class="error-infos">Your 42 email or username is already in use. Please log in manually.</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
