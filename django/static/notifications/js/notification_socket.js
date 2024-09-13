document.addEventListener('DOMContentLoaded', () => {
    const isSecure = window.location.protocol === 'https:';
    const websocketPort = isSecure ? ':8443' : ':8000';
    const websocketProtocol = isSecure ? 'wss:' : 'ws:';
    const notificationSocketUrl = `${websocketProtocol}//${window.location.hostname}${websocketPort}/ws/notifications/`;

    const notificationSocket = {
        socket: new WebSocket(notificationSocketUrl),
        shouldClose: false
    };

    notificationSocket.socket.onmessage = () => renderHeader();

    notificationSocket.socket.onclose = () => {
        if (!notificationSocket.shouldClose) {
            notificationSocket.socket = new WebSocket(notificationSocketUrl);
        }
    };

    window.onbeforeunload = () => {
        if (notificationSocket.socket) {
            notificationSocket.shouldClose = true;
            notificationSocket.socket.close();
        }
    };
});