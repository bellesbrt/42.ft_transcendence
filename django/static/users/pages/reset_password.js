function renderResetPasswordPage() {
	fetchAPI('/api/isAuthenticated').then(data => {
		if (data.isAuthenticated) {
			document.getElementById('app').innerHTML = `
				<div class="already-log-in">
					<p class="log-in-message">You are already connected, you can change your password in your profile.</p>
					<button class="log-in-button" id="sign-out">Sign out</button>
				</div>
			`;

			document.getElementById('sign-out').addEventListener('click', async function(event) {

				fetchAPI('/api/sign_out').then(data => {
					renderHeader();
					
					router.navigate('/sign_in/');
					return ;
				});
			});
		
		} else {

			const fields = [
				{ name: 'email', label: 'Email', type: 'email' },
			];

			const fieldsHtml = fields.map(renderField).join('');

			document.getElementById('app').innerHTML = `
				<div class="all-screen">
					<div class="form-div">
						<form method="POST" class="sign-form">
							<h3 class="sign-title">Reset password</h3>
							${fieldsHtml}
							<p class="error-message" id="error-message"></p>
							<input type="submit" value="Send the email"/>
						</form>
					</div>
				</div>
			`;

			document.querySelector('.sign-form').addEventListener('submit', async function(event) {
				event.preventDefault();

				document.getElementById('error-email').textContent = '';

				const email = document.getElementById('email').value;

				if (!email) {
					document.getElementById('error-email').textContent = 'This field is required.';
					return;
				}

				const response = await fetch('/reset_password/', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
					body: JSON.stringify({ email })
				});

				if (response.headers.get('content-type').includes('application/json')) {
					const responseData = await response.json();

					if (responseData.success) {
						renderHeader();

						document.getElementById('error-message').textContent = "If the email provided is correct, you will receive a link to reset your password.";
						return ;
					
					} else {
						document.getElementById('error-email').textContent = responseData.email;
						document.getElementById('error-message').textContent = responseData.message;
					}

				} else {
					document.getElementById('error-message').textContent = "The server encountered an unexpected error.";
				}
			});
		}
	})
}