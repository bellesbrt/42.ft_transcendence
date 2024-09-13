// API
function fetchAPI(url) {
	return fetch(url, { method: 'GET', headers: { 'Content-Type': 'application/json' } })
		.then(response => response.json());
}

// Status

fetchAPI('/api/get_game_info').then(data => {
	if (data.success) {
		gameMode = data.gameMode;
		gameID = data.game_id;
		playerID = data.player_id;
		if (gameID && playerID) gameProcess(true, gameMode, gameID, playerID);
	}
});

function sendDisconnectSignal() {
	fetchAPI('/api/change_status/offline').then(data => {
		if (data.user_id) changeStatus(data.user_id, 'offline');
	});
}

function handleVisibilityChange() {
	const status = document.hidden ? 'offline' : 'online';
	fetchAPI(`/api/change_status/${status}`).then(data => {
		if (data.user_id) changeStatus(data.user_id, status);
	});
}

document.addEventListener("visibilitychange", handleVisibilityChange, false);

// Router

let isPopStateEvent = false;

const router = {
	routes: {
		'/': renderChooseModePage,
		'/sign_in/': renderSignInPage,
		'/sign_up/': renderSignUpPage,
		'/reset_password/': renderResetPasswordPage,
		'/reset_password_id/:resetPasswordID': renderResetPasswordIDPage,
		'/profile/:username': renderProfilePage,
		'/friends/': renderFriendsPage,
		'/pong/': renderChooseModePage,
		'/pong/ranked/': renderRankedPage,
		'/pong/practice/': renderPracticePage,
		'/pong/wait_players/:gameMode': renderWaitPlayers,
		'/pong/game/:gameMode': renderGamePage,
		'/pong/game_over/:gameID': renderGameOverPage,
		'/chat/': renderChatPage,
		'/chat/new/': renderNewRoomPage,
		'/chat/:id': renderRoomPage,
		'/notifications/': renderNotificationsPage,
		'/ranking/:sortedBy': renderRankingPage,
		'/token42/': renderToken42Page,
		'/down42/': renderDown42Page,
		'/used42/': renderUsed42Page,
		'/auth42/': renderAuth42Page,
	},

	navigate(route) {
		if (typeof route !== 'string') return;

		const matchingRoute = Object.keys(this.routes).find(r =>
			new RegExp(`^${r.replace(/:[^\s/]+/g, '([\\w-]+)')}$`).test(route)
		);

		if (matchingRoute) {
			const params = route.match(new RegExp(matchingRoute.replace(/:[^\s/]+/g, '([\\w-]+)'))).slice(1);
			this.routes[matchingRoute](...params);
			if (!isPopStateEvent) history.pushState({ route }, '', route);
			isPopStateEvent = false;
		} else {
			render404Page();
		}
	}
};

// Cookies

function getCookie(name) {
	const cookies = document.cookie.split(';');
	for (const cookie of cookies) {
		const [key, value] = cookie.trim().split('=');
		if (key === name) return decodeURIComponent(value);
	}
	return null;
}

// Navigation & Routing

async function navigateTo(event, route) {
	event.preventDefault();
	router.navigate(route);
	renderHeader();
}

document.addEventListener('click', event => {
	let target = event.target;
	while (target && target !== document) {
		if ((target.tagName === 'BUTTON' || target.tagName === 'A') && !target.hasAttribute('data-ignore-click')) {
			event.preventDefault();
			navigateTo(event, target.getAttribute('data-route'));
			return;
		}
		target = target.parentNode;
	}
});

window.addEventListener('popstate', event => {
	if (event.state?.route) {
		isPopStateEvent = true;
		router.navigate(event.state.route);
	}
});

// Utils

function renderField(field) {
	return `
		<label for="${field.name}">${field.label}</label>
		<div class="input-container">
			<input type="${field.type}" id="${field.name}" name="${field.name}" autocomplete="on" value="${field.value || ''}" accept="${field.accept || ''}" ${field.disabled ? 'disabled' : ''}/>
			${field.type === 'password' ? 
				`<button data-ignore-click type="button" class="show-password" id="show-${field.name}">
					<img class="img-password" src="/static/users/img/eye_open.png" alt="Show/Hide"/>
				</button>` 
			: ''}
		</div>
		<p class="error-alert" id="error-${field.name}"></p>
	`;
}

document.addEventListener('click', event => {
	if (event.target.classList.contains('show-password')) {
		const input = event.target.previousElementSibling;
		const isPassword = input.type === 'password';
		input.type = isPassword ? 'text' : 'password';
		event.target.firstElementChild.src = isPassword ? '/static/users/img/eye_close.png' : '/static/users/img/eye_open.png';
	}
});

let listFR = [], listEN = [], listPT = [];
fetch('/static/badwords/fr.json').then(response => response.json()).then(data => listFR = data.words);
fetch('/static/badwords/en.json').then(response => response.json()).then(data => listEN = data.words);
fetch('/static/badwords/pt.json').then(response => response.json()).then(data => listPT = data.words);

function filterMessage(message) {
	message = message.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
	const filterList = [...listFR, ...listEN, ...listPT];
	for (const word of filterList) {
		const normalizedWord = word.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
		message = message.replace(new RegExp(normalizedWord, 'gi'), '*'.repeat(word.length));
	}
	return message;
}

function safeText(unsafeText) {
	const div = document.createElement('div');
	div.innerText = unsafeText;
	return div.innerHTML;
}

// Observer

window.addEventListener('DOMContentLoaded', () => {
	router.navigate(window.location.pathname);
	renderHeader();
	if (!getCookie('csrftoken')) {
		fetch('/api/generate_csrf_token/')
			.then(response => response.json())
			.then(data => document.cookie = `csrftoken=${data.token};path=/`);
	}
});
