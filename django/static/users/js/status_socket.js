let statusSocket = null;

document.addEventListener('DOMContentLoaded', function () {
    // Init the socket
    const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocketPort = window.location.protocol === 'https:' ? ':8443' : ':8000';
    const statusSocketUrl = `${websocketProtocol}//${window.location.hostname}${websocketPort}/ws/status/`;

    statusSocket = {
        socket: new WebSocket(statusSocketUrl),
        url: statusSocketUrl,
        shouldClose: false
    };

    statusSocket.socket.onmessage = function (e) {
        const { id, status } = JSON.parse(e.data);

        // Update status display based on user status
        if (status.includes('chat')) {
            status = 'online';
        }

        const userElement = document.querySelector(`.container[data-user-id="${id}"]`);
        if (userElement) {
            const statusElement = userElement.querySelector('.status');
            if (statusElement) {
                statusElement.textContent = status;
            }
        }
    };

    statusSocket.socket.onclose = function () {
        if (!statusSocket.shouldClose && statusSocket.socket.readyState !== WebSocket.CLOSED) {
            statusSocket.socket = new WebSocket(statusSocket.url);
        }
    };

    window.onbeforeunload = function () {
        if (statusSocket && statusSocket.socket.readyState === WebSocket.OPEN) {
            statusSocket.shouldClose = true;
            statusSocket.socket.close();
        }
    };
});

async function sendStatusUpdate(id, status) {
    try {
        if (statusSocket.socket.readyState === WebSocket.OPEN) {
            statusSocket.socket.send(JSON.stringify({ id, status }));
        } else {
            await new Promise((resolve, reject) => {
                const onOpen = () => {
                    statusSocket.socket.send(JSON.stringify({ id, status }));
                    resolve();
                };
                const onError = (e) => reject(new Error('WebSocket error: ' + e));
                statusSocket.socket.addEventListener('open', onOpen, { once: true });
                statusSocket.socket.addEventListener('error', onError, { once: true });
            });
        }
    } catch (error) {
        console.error('Failed to send status update:', error);
    }
}

function SignOutProcess(id) {
    const signOutButton = document.getElementById('sign-out');
    if (signOutButton) {
        sendStatusUpdate(id, 'offline');
    }
}

function SignInProcess(id) {
    const signInButton = document.getElementById('set-status-online');
    if (signInButton) {
        sendStatusUpdate(id, 'online');
    }
}

function changeStatus(id, status) {
    sendStatusUpdate(id, status);
}