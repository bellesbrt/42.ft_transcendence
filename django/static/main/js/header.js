function renderHeader() {

	fetchAPI('/api/header').then(data => {
		const header = document.querySelector('.header-menu');

		if (data.isAuthenticated) {

			header.classList.add('user-authenticated');
			header.classList.remove('user-guest');

			document.getElementById('header-username').textContent = data.username;
			document.getElementById('header-user-photo').src = data.photo_url;
			
			if (data.nbNewNotifications > 99)
				document.getElementById('header-notification-count').textContent = '99+';
			else {
				document.getElementById('header-notification-count').textContent = data.nbNewNotifications;
			}

		} else {
			header.classList.add('user-guest');
			header.classList.remove('user-authenticated');
		}
	})
	.catch((error) => {});
}