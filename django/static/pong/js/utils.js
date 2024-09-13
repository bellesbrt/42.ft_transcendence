function getPaddleDirection(key) {
    const upKeys = ['o', 'w', 'x', 'ArrowLeft', 'ArrowUp'];
    const downKeys = ['l', 's', 'z', 'ArrowRight', 'ArrowDown'];

    if (upKeys.includes(key)) {
        return 'up';
    } else if (downKeys.includes(key)) {
        return 'down';
    }
}

function getSocket(gameID) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const port = window.location.protocol === 'https:' ? ':8443' : ':8000';
    const socketUrl = `${protocol}//${window.location.hostname}${port}/ws/game/${gameID}/`;

    return {
        socket: new WebSocket(socketUrl),
        url: socketUrl,
        shouldClose: false
    };
}