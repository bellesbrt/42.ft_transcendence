function render500Page() {
	const appElement = document.getElementById('app');

	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">500</p>
				<p class="error-title">Internal Server Error</p>
				<p class="error-infos">Please try again later.</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
