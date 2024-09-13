from channels.db import database_sync_to_async
from .senders.sendUpdatePaddlePosition import sendUpdatePaddlePosition
from .handleAIMove import ai_loop
import asyncio

def keyupReset(direction, paddle):
	paddle.keyState[direction] = False
	if paddle.taskAsyncio[direction]:
		paddle.taskAsyncio[direction].cancel()


async def keydownLoop(direction, paddle, consumer, gameSettings):
	opposite_direction = 'down' if direction == 'up' else 'up'
	paddle.keyState[opposite_direction] = False

	move_functions = {
		'up': paddle.moveUp,
		'down': paddle.moveDown
	}

	def can_move():
		if direction == 'up':
			return paddle.position > gameSettings.limit
		elif direction == 'down':
			return paddle.position < gameSettings.squareSize - gameSettings.limit - gameSettings.paddleSize
		return False

	while paddle.keyState[direction]:
		if can_move():
			move_functions[direction]()

		await sendUpdatePaddlePosition(consumer, paddle)
		await asyncio.sleep(0.01)


async def handlePaddleMove(consumer, message, gameSettings, playerID):
	direction = message['direction']
	paddle = get_target_paddle(gameSettings, message, playerID)

	if not paddle:
		return

	ai_paddle = gameSettings.paddles[1]
	if gameSettings.isAIGame and ai_paddle.aiTask is None:
		ai_paddle.aiTask = asyncio.create_task(ai_loop(consumer, gameSettings, ai_paddle))

	if paddle.isAlive:
		handle_key_event(direction, message['key'], paddle, consumer, gameSettings)

def get_target_paddle(gameSettings, message, playerID):
	"""Identifies the correct paddle based on the game type and the message received."""
	if gameSettings.isLocalGame:
		if message['paddleKey'] in ['w', 's']:
			return gameSettings.paddles[0]
		elif message['paddleKey'] in ['o', 'l'] and not gameSettings.isAIGame:
			return gameSettings.paddles[1]
	else:
		playerIndex = gameSettings.playerIDList.index(playerID)
		return gameSettings.paddles[playerIndex]
	return None

def handle_key_event(direction, key_event, paddle, consumer, gameSettings):
	"""Handles key press ('keydown') or release ('keyup') events."""
	if key_event == 'keydown':
		if paddle.keyState[direction]:
			return
		paddle.keyState[direction] = True
		paddle.taskAsyncio[direction] = asyncio.create_task(
			keydownLoop(direction, paddle, consumer, gameSettings)
		)
	elif key_event == 'keyup':
		keyupReset(direction, paddle)

