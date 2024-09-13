function renderDown42Page() {
	const appElement = document.getElementById('app');

	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">401</p>
				<p class="error-title">The 42 API is Down</p>
				<p class="error-infos">Please contact the administrator.</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
