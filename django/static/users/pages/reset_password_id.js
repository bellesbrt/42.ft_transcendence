function renderResetPasswordIDPage() {
	fetchAPI('/api/isAuthenticated').then(data => {
		if (data.isAuthenticated) {
			document.getElementById('app').innerHTML = `
				<div class="already-log-in">
					<p class="log-in-message">You are already connected, please logout before reset a password.</p>
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
				{ name: 'password', label: 'New password', type: 'password' },
				{ name: 'password-confirmation', label: 'Password confirmation', type: 'password' },
			];

			const fieldsHtml = fields.map(renderField).join('');

			document.getElementById('app').innerHTML = `
				<div class="all-screen">
					<div class="form-div">
						<form method="POST" class="sign-form">
							<h3 class="sign-title">New password</h3>
							${fieldsHtml}
							<p class="error-message" id="error-message"></p>
							<input type="submit" value="Change your password"/>
						</form>
					</div>
				</div>
			`;

			document.querySelector('.sign-form').addEventListener('submit', async function(event) {
				event.preventDefault();

				document.getElementById('error-password').textContent = '';
				document.getElementById('error-password-confirmation').textContent = '';

				const password = document.getElementById('password').value;
				const passwordConfirmation = document.getElementById('password-confirmation').value;

				if (!password) {
					document.getElementById('error-password').textContent = 'This field is required.';
					return;
				}
				if (!passwordConfirmation) {
					document.getElementById('error-password-confirmation').textContent = 'This field is required.';
					return;
				}
				if (password !== passwordConfirmation) {
					document.getElementById('error-password-confirmation').textContent = 'The password confirmation does not match the password.';
					return;
				}

				const response = await fetch('/reset_password_id/' + window.location.pathname.split('/')[2], {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
					body: JSON.stringify({ password })
				});

				if (response.headers.get('content-type').includes('application/json')) {
					const responseData = await response.json();

					if (responseData.success) {
						renderHeader();

						router.navigate('/sign_in/');
						return ;
					
					} else {
						document.getElementById('error-password').textContent = responseData.password;
						document.getElementById('error-password-confirmation').textContent = responseData.passwordConfirmation;
						document.getElementById('error-message').textContent = responseData.message;
					}

				} else {
					document.getElementById('error-message').textContent = "The server encountered an unexpected error.";
				}
			});
		}
	})
}