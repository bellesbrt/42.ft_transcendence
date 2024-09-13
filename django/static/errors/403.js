function render403Page() {
	const appElement = document.getElementById('app');
	
	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">403</p>
				<p class="error-title">Forbidden</p>
				<p class="error-infos">Access denied</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
