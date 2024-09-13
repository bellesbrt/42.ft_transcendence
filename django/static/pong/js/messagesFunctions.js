function initPaddlePosition(paddleID, position) {
	elements.paddles[paddleID] = new Paddle(paddleID);
	elements.paddles[paddleID].draw(position);
}

function updatePaddlePosition(paddleID, position) {
	const paddle = elements.paddles[paddleID];
	if (paddle) {
		paddle.clear();
		paddle.draw(position);
	}
}

function updateScore(message) {
    const backgroundColors = ['#E21E59', '#1E90FF', '#32CD32', '#8A2BE2'];
    const scoreSpans = document.querySelectorAll('.player_score');
	const scoreSpan = scoreSpans[message.id];
	
	if (!scoreSpan) return;

	const widthMap = {
		1: '100%',
		2: '50%',
		4: '25%'
	};

	scoreSpan.style.width = widthMap[message.nbPaddles] || 'auto';
	scoreSpan.textContent = message.score;
	scoreSpan.style.backgroundColor = backgroundColors[message.id];

	if (message.score >= 10) {
		const paddleID = message.nbPaddles === 2 ? (message.id ^ 1) : message.id;
		const targetSpan = scoreSpans[paddleID];

		if (targetSpan) {
			targetSpan.style.backgroundColor = '#212121';
			targetSpan.style.color = '#DADADA';

			const paddle = elements.paddles[paddleID];
			if (paddle) {
				paddle.clear();
				paddle.draw();
			}
		}
	}
}

function updateBallPosition(x, y, color, radius) {
	if (elements.ball) {
		elements.ball.clear();
	}
	elements.ball = new Ball(x, y, color, radius);
	elements.ball.draw(x, y, color, radius);
}

function gameOver(message) {
	router.navigate(`/pong/game_over/${message.gameID}`);
}