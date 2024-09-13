function render404Page() {
	const random = Math.random();
	let errorInfos = "Please check the URL and try again.";
	if (random < 0.1) {
		errorInfos = "You are lost in the woods. You should have listened to your mother and stayed on the path.";
	}

	const appElement = document.getElementById('app');
	
	if (appElement) {
		appElement.innerHTML = `
			<div class="error-container">
				<p class="error-code">404</p>
				<p class="error-title">Page not found</p>
				<p class="error-infos">${safeText(errorInfos)}</p>
			</div>
		`;
	} else {
		console.error("Element with id 'app' not found.");
	}
}
