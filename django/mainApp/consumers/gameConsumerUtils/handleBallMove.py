from .senders.sendUpdateBallPosition import sendUpdateBallPosition
from .senders.sendUpdateScore import sendUpdateScore
from .senders.sendGameOver import sendGameOver
import asyncio

async def updateScore(consumer, gameSettings, paddleID):
	if gameSettings.nbPaddles == 2:
		opponentPaddle = gameSettings.paddles[paddleID ^ 1]
		opponentPaddle.score += 1
		if opponentPaddle.score >= 10:
			gameSettings.paddles[paddleID].isAlive = False
			opponentPaddle.isAlive = False
			gameSettings.paddles[paddleID].rankPosition = 2
			opponentPaddle.rankPosition = 1

			await sendGameOver(consumer, gameSettings, gameSettings.paddles[paddleID])
			await sendGameOver(consumer, gameSettings, opponentPaddle)
	else:
		currentPaddle = gameSettings.paddles[paddleID]
		currentPaddle.score += 1
		if currentPaddle.score >= 10:
			currentPaddle.isAlive = False
			nbAlives = sum(1 for paddle in gameSettings.paddles if paddle.isAlive)
			currentPaddle.rankPosition = nbAlives + 1
			await sendGameOver(consumer, gameSettings, currentPaddle)
			if nbAlives == 1:
				for paddle in gameSettings.paddles:
					if paddle.isAlive:
						paddle.isAlive = False
						paddle.rankPosition = 1
						paddle.score = 10
						await sendGameOver(consumer, gameSettings, paddle)


async def startBall(consumer, gameSettings):
	"""Main loop that controls ball movement, collision detection, and score updates."""
	ball = gameSettings.ball

	while True:
		ball.move()

		# Check for collisions with paddles
		for paddle in gameSettings.paddles:
			ball.checkPaddleCollision(paddle, gameSettings)

		# Check for collisions with walls and update the score if necessary
		paddleID = ball.checkWallCollision(gameSettings)
		if paddleID >= 0:
			await handleScoreUpdate(consumer, gameSettings, paddleID)
			ball.resetBall(gameSettings)
			await asyncio.sleep(1.5)  # Pause before restarting the ball

		await asyncio.sleep(0.01)
		await sendUpdateBallPosition(consumer, gameSettings)


async def handleScoreUpdate(consumer, gameSettings, paddleID):
	"""Updates the score and sends the update to the consumer."""
	await updateScore(consumer, gameSettings, paddleID)
	await sendUpdateScore(consumer, gameSettings)


async def handleBallMove(consumer, gameSettings):
	if gameSettings.ball.task:
		return
	gameSettings.ball.task = asyncio.create_task(startBall(consumer, gameSettings))
