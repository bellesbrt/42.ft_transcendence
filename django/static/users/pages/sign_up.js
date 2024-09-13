function renderSignUpPage() {

	fetchAPI('/api/isAuthenticated').then(data => {
		if (data.isAuthenticated) {
			document.getElementById('app').innerHTML = `
				<div class="already-log-in">
					<p class="log-in-message">You are already connected, please log out before log in.</p>
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
				{ name: 'username', label: 'Username', type: 'text' },
				{ name: 'email', label: 'Email', type: 'email' },
				{ name: 'password', label: 'Password', type: 'password' }
			];

			const fieldsHtml = fields.map(renderField).join('');

			document.getElementById('app').innerHTML = `
				<div class="all-screen">
					<div class="form-div">
						<form method="POST" class="sign-form">
							<h3 class="sign-title">Sign up</h3>
							${fieldsHtml}
							<p class="error-message" id="error-message"></p>
							<input type="submit" value="Sign up"/>
						</form>
					</div>
				</div>
			`;

			document.querySelector('.sign-form').addEventListener('submit', async function(event) {
				event.preventDefault();

				document.getElementById('error-username').textContent = '';
				document.getElementById('error-email').textContent = '';
				document.getElementById('error-password').textContent = '';
				document.getElementById('error-message').textContent = '';

				const username = document.getElementById('username').value;
				const email = document.getElementById('email').value;
				const password = document.getElementById('password').value;

				if (!username) {
					document.getElementById('error-username').textContent = 'This field is required.';
				}
				if (!email) {
					document.getElementById('error-email').textContent = 'This field is required.';
				}
				if (!password) {
					document.getElementById('error-password').textContent = 'This field is required.';
				}

				if (!username || !email || !password) {
					return ;
				}

				const response = await fetch('/sign_up/', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-CSRFToken': getCookie('csrftoken'),
					},
					body: JSON.stringify({ username, email, password })
				});

				if (response.headers.get('content-type').includes('application/json')) {
					const responseData = await response.json();

					if (responseData.success) {
						renderHeader();

						router.navigate('/pong/');
						return ;
					
					} else {
						document.getElementById('error-username').textContent = responseData.username;
						document.getElementById('error-email').textContent = responseData.email;
						document.getElementById('error-password').textContent = responseData.password;
						document.getElementById('error-message').textContent = responseData.message;
					}

				} else {
					document.getElementById('error-message').textContent = "The server encountered an unexpected error.";
				}
			});
		}
	})
}
