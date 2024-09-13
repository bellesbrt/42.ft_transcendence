const elements = {
	field: null,
	paddles: [],
	ball: null,
}

const   keyState = {
    w: false,
    s: false,
    o: false,
    l: false,
	z: false,
	x: false,
	ArrowLeft: false,
	ArrowRight: false,
    ArrowUp: false,
    ArrowDown: false,
};

const	sizes = {
    canvas: 800,
    paddleSize: 100,
    paddleThickness: 20,
    offset: 20,
};
sizes.field = sizes.paddleThickness + sizes.offset;

function createGameCanvas() {
	const gameCanvas = document.getElementById('gameCanvas');
    gameCanvas.width = sizes.canvas;
    gameCanvas.height = sizes.canvas;

    const gameContext = gameCanvas.getContext('2d');
    gameContext.fillStyle = "#E0FFFF";
    gameContext.fillRect(0, 0, gameCanvas.width, gameCanvas.height);

	elements.field = new Field(sizes.canvas);
	elements.field.draw(gameContext);

	return (gameCanvas, gameContext)
}

let pongSocket = null;

function gameProcess(isWaitingPage, gameMode, gameID, playerID) {
    var isReady = false;
	if (!isWaitingPage) {
		gameCanvas, gameContext = createGameCanvas();
	}

    if (!pongSocket || pongSocket.socket.readyState === WebSocket.CLOSED || pongSocket.socket.readyState === WebSocket.CLOSING)
        pongSocket = getSocket(gameID);

    if (!isWaitingPage) {
        if (pongSocket.socket.readyState === WebSocket.OPEN) {
            const init_game_message = {
                type: gameMode,
                playerID: playerID,
            };
            pongSocket.socket.send(JSON.stringify(init_game_message));
        } else {
            pongSocket.socket.addEventListener('open', function (event) {
                const init_game_message = {
                    type: gameMode,
                    playerID: playerID,
                };
                pongSocket.socket.send(JSON.stringify(init_game_message));
            });
        }
    }

    pongSocket.socket.onopen = function() {
    };

    pongSocket.socket.onmessage = function(event) {
        const message = JSON.parse(event.data);


        switch (message.type) {
            case 'reload_page':
                if (isWaitingPage) {
                    router.navigate(`/pong/game/${gameMode}`);
                }
                break;
            case 'init_paddle_position':
                initPaddlePosition(message.id, message.position);
                isReady = true;
                break;
            case 'update_score':
                updateScore(message);
                break;
            case 'update_paddle_position':
                updatePaddlePosition(message.id, message.position);
                break;
            case 'update_ball_position':
                isReady = true;
                updateBallPosition(message.x, message.y, message.color, message.radius);
                break;
            case 'game_over':
                if (message.playerID === playerID) {
                    pongSocket.socket.close();
                    pongSocket = null;
                    isReady = false;
                    gameOver(message);
                }
                break;
        }
    };

    if (!isWaitingPage) {
        document.addEventListener('keydown', function(event) {
            const gameCanvas = document.getElementById('gameCanvas');
            if (gameCanvas && isReady) {
                if (!keyState[event.key] && keyState.hasOwnProperty(event.key)) {
                    keyState[event.key] = true;
                    const message = {
                        type: 'paddle_move',
                        key: 'keydown',
                        direction: getPaddleDirection(event.key),
                        playerID: playerID,
                        paddleKey: event.key,
                    };
                    if (pongSocket && pongSocket.socket.readyState === WebSocket.OPEN) {
                        pongSocket.socket.send(JSON.stringify(message));
                    }
                }

                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key))  {
                    event.preventDefault();
                }
            }
        });

        document.addEventListener('keyup', function(event) {
            const gameCanvas = document.getElementById('gameCanvas');
            if (gameCanvas && isReady) {
                if (keyState.hasOwnProperty(event.key)) {
                    keyState[event.key] = false;
                    const message = {
                        type: 'paddle_move',
                        key: 'keyup',
                        direction: getPaddleDirection(event.key),
                        playerID: playerID,
                        paddleKey: event.key,
                    };
                    if (pongSocket && pongSocket.socket.readyState === WebSocket.OPEN) {
                        pongSocket.socket.send(JSON.stringify(message));
                    }
                }
            }
        });
    }
}