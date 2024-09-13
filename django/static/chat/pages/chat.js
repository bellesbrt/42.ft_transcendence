function renderChannel(channel) {
	let badgeMap = {
		"general": "🌍 Global",
		"private": "👥 Private discussion",
		"tournament": "🎯 Tournament",
		"official": "⭐ Official"
	  };
	  
	  let badge = badgeMap[channel.room_id] || 
				  (channel.private ? badgeMap["private"] :
				  channel.tournament ? badgeMap["tournament"] :
				  !channel.creator ? badgeMap["official"] : "");

	let sender = channel.last_message ? (channel.last_message.sender === 0 ? "System" : channel.last_message.sender) : '';
	let lastMessage = channel.last_message ? `
		<p class="chat-last-message-timestamp">${safeText(channel.last_message.timestamp)}</p>
		<div class="chat-last-message-container">
			<p class="chat-last-message-sender">${safeText(sender)}: </p>
			<p class="chat-last-message">${safeText(filterMessage(channel.last_message.message.substring(0, 50)))}${safeText(channel.last_message.message.length > 50 ? '...' : '')}</p>
		</div>` 
		: '<p class="chat-last-message-timestamp">No message yet, be the first!</p>';

	return `
		<div class="a-chat">
			<a class="chat-container" data-route="/chat/${channel.room_id}">
				<h4 class="chat-badge">${safeText(badge)}</h4>
				<h3 class="chat-name">${safeText(channel.name)}</h3>
				${lastMessage}
			</a>
			<button class="chat-info-button" id="${channel.room_id}">
				<img class="chat-info-button-img" src="/static/chat/img/info.png" alt="Info">
			</button>
		</div>`;
}

function renderChatPage() {
	fetchAPI('/api/isAuthenticated').then(data => {
		if (!data.isAuthenticated) return router.navigate('/sign_in/');

		fetchAPI('/api/get_user').then(dataUser => {
			const userChannels = Object.values(dataUser.user.channels);
			const favChannels = dataUser.user.favoritesChannels;
			const nonFavChannels = userChannels.filter(c => !favChannels.includes(c.room_id));

			document.getElementById('app').innerHTML = `<h1>Chats</h1>${favChannels.length ? `<h3 class="chat-section">• ${favChannels.length === 1 ? 'Favorite' : 'Favorites'}</h3><div class="chat-scrollable">${favChannels.map(renderChannel).join('')}</div>` : ''}`;
			document.getElementById('app').innerHTML += nonFavChannels.length ? `<h3 class="chat-section">• Channels</h3><div class="chat-scrollable">${nonFavChannels.map(renderChannel).join('')}</div>` : '<p>No channels available.</p>';

			document.getElementById('app').innerHTML += `<button class="profile-button" data-route="/chat/new/">Start a new chat group ➜</button>`;
			handleChatInfoButtons(dataUser.user.channels);
		});
	});
}

function handleChatInfoButtons(channels) {
	document.querySelectorAll('.chat-info-button').forEach(button => {
		button.addEventListener('click', () => showPopup(channels[button.id]));
	});
}

function showPopup(channel) {
	let popupHTML = `
		<div class="popup-background" id="popup-background"></div>
		<div class="popup">
			<h3 class="title-popup">Information</h3>
			<p class="popup-info">Name: ${safeText(channel.name)}</p>
			<p class="popup-info">Description: ${safeText(channel.description)}</p>
			<p class="popup-info">Creator: ${safeText(channel.creator_username)}</p>
			<p class="popup-info">Private: ${channel.private ? 'Yes' : 'No'}</p>
			<p class="popup-info">Members: ${Object.values(channel.users).map(u => safeText(u.username)).join(', ')}</p>
			${channel.room_id !== "general" ? `<button class="button-leave-popup" id="leave-chat">Leave</button>` : ''}
			<button class="close-popup" id="close-popup">Close</button>
		</div>`;

	document.body.insertAdjacentHTML('beforeend', popupHTML);
	addPopupEvents(channel);
}

function addPopupEvents(channel) {
	document.getElementById('close-popup').addEventListener('click', closePopup);
	document.getElementById('popup-background').addEventListener('click', closePopup);
	if (document.getElementById('leave-chat')) {
		document.getElementById('leave-chat').addEventListener('click', () => fetchAPI(`/api/leave_channel/${channel.room_id}`).then(data => {
			if (data.success) {
				closePopup();
				router.navigate('/chat/');
			}
		}));
	}
}

function closePopup() {
	document.querySelector('.popup').remove();
	document.getElementById('popup-background').remove();
}