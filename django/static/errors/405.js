function render405Page() {
	const appElement = document.getElementById('app');
	
	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">405</p>
				<p class="error-title">Method Not Allowed</p>
				<p class="error-infos">Please check the URL and try again.</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
