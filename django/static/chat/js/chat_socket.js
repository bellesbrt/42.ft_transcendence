let chatSocket = null;

function chatProcess(roomID, blockedUsers, isPrivate, sender, username) {

	if (chatSocket) {
		chatSocket.shouldClose = true;
		if (chatSocket.socket.readyState !== WebSocket.CLOSED) {
			chatSocket.socket.close();
		}
	}

	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const port = window.location.protocol === 'https:' ? ':8443' : ':8000';
	const socketUrl = `${protocol}//${window.location.hostname}${port}/ws/chat/${roomID}/`;

	chatSocket = { socket: new WebSocket(socketUrl), url: socketUrl, shouldClose: false };

	const chatLog = document.querySelector('#chat-log');
	if (chatLog) chatLog.scrollTop = chatLog.scrollHeight;

	chatSocket.socket.onmessage = e => {
		const data = JSON.parse(e.data);
		if (data.sender >= 0 && data.message) {
			fetch(`/api/get_username/${data.sender}`)
				.then(response => response.json())
				.then(data_username => {
					const msgContainer = document.createElement('p');
					msgContainer.textContent = blockedUsers.includes(data.sender) 
						? 'This user is blocked' 
						: filterMessage(data.message);
					
					msgContainer.className = data.sender === sender 
						? 'my-message' 
						: data.sender === 0 
							? 'system-message' 
							: 'other-message';
					
					if (!blockedUsers.includes(data.sender) && chatLog) {
						if (data.sender !== sender && !isPrivate) {
							const usernameContainer = document.createElement('p');
							usernameContainer.textContent = safeText(data_username?.username || '[UserNotfound]');
							usernameContainer.className = 'other-username';
							if (chatLog.lastElementChild?.dataset.sender != data.sender) {
								chatLog.appendChild(usernameContainer);
							}
						}
						chatLog.appendChild(msgContainer);
						chatLog.scrollTop = chatLog.scrollHeight;
					}
				});
		}
	};

	window.onbeforeunload = () => {
		if (chatSocket) {
			chatSocket.shouldClose = true;
			chatSocket.socket.close();
		}
	};

	chatSocket.socket.onclose = () => {
		if (!chatSocket.shouldClose && chatSocket.socket.readyState === WebSocket.CLOSED) {
			chatSocket.socket = new WebSocket(chatSocket.url);
		}
	};

	const messageInput = document.querySelector('#chat-message-input');
	messageInput.focus();
	messageInput.onkeyup = e => {
		if (e.key === 'Enter') document.querySelector('#chat-message-submit').click();
	};

	document.querySelector('#chat-message-submit').onclick = () => {
		const message = messageInput.value.trim();
		if (message && chatSocket.socket.readyState === WebSocket.OPEN) {
			chatSocket.socket.send(JSON.stringify({ message, sender, username }));
		}
		messageInput.value = '';
	};
}