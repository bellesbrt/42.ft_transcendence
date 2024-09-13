from .senders.sendUpdatePaddlePosition import sendUpdatePaddlePosition
import asyncio
import math
import random


async def move_ai_to_aim(consumer, paddle, gameSettings, aim_position):

	def adjust_aim_position(aim_position):
		"""Adjust the target position to ensure the paddle does not go beyond the limits."""
		min_limit = gameSettings.limit
		max_limit = gameSettings.squareSize - gameSettings.paddleSize - gameSettings.limit
		return max(min(aim_position, max_limit), min_limit)

	async def update_position():
		"""Sends the updated paddle position to the client."""
		await sendUpdatePaddlePosition(consumer, paddle)

	aim_position = adjust_aim_position(aim_position)

	while True:
		if abs(paddle.position - aim_position) <= 10:
			paddle.position = round(aim_position)

		if aim_position < paddle.position:
			paddle.moveUp()
		elif aim_position > paddle.position:
			paddle.moveDown()

		await update_position()
		await asyncio.sleep(0.01)


async def compute_aim_position(gameSettings):
	limit = gameSettings.limit
	ball_x = gameSettings.ball.x - limit
	ball_y = gameSettings.ball.y
	angle = normalize_angle(gameSettings.ball.angle)

	width = gameSettings.squareSize - limit * 2
	height = gameSettings.squareSize - limit

	for _ in range(5):
		if is_left_collision(angle):
			collision_y = calculate_left_collision_y(ball_x, ball_y, angle)
			if limit < collision_y < height:
				return collision_y
		else:
			collision_y = calculate_right_collision_y(ball_x, ball_y, angle, width)
			if limit < collision_y < height:
				return collision_y

		if is_bottom_collision(angle):
			collision_x = calculate_bottom_collision_x(ball_x, ball_y, angle, height)
			if limit < collision_x < width:
				ball_x, ball_y, angle = update_ball_position_after_bottom_collision(collision_x, height, angle)
		else:
			collision_x = calculate_top_collision_x(ball_x, ball_y, angle)
			if limit < collision_x < width:
				ball_x, ball_y, angle = update_ball_position_after_top_collision(collision_x, limit, angle)

	return height


def normalize_angle(angle):
	"""Normalize the angle to be within the range of 0 to 2π."""
	return angle % (2 * math.pi)


def is_left_collision(angle):
	"""Check if the ball is moving towards the left wall."""
	return math.pi / 2 < angle < 3 * math.pi / 2


def is_bottom_collision(angle):
	"""Check if the ball is moving towards the bottom wall."""
	return 0 < angle < math.pi


def calculate_left_collision_y(ball_x, ball_y, angle):
	"""Calculate the y-coordinate of the collision with the left wall."""
	return ball_y + (-ball_x * math.tan(angle))


def calculate_right_collision_y(ball_x, ball_y, angle, width):
	"""Calculate the y-coordinate of the collision with the right wall."""
	return ball_y + (width - ball_x) * math.tan(angle)


def calculate_top_collision_x(ball_x, ball_y, angle):
	"""Calculate the x-coordinate of the collision with the top wall."""
	return ball_x + (0 - ball_y) / math.tan(angle)


def calculate_bottom_collision_x(ball_x, ball_y, angle, height):
	"""Calculate the x-coordinate of the collision with the bottom wall."""
	return ball_x + (height - ball_y) / math.tan(angle)


def update_ball_position_after_bottom_collision(collision_x, height, angle):
	"""Update ball position and reflect the angle after hitting the bottom wall."""
	return collision_x, height, -angle


def update_ball_position_after_top_collision(collision_x, limit, angle):
	"""Update ball position and reflect the angle after hitting the top wall."""
	return collision_x, limit, -angle


# executes while the game is in progress
async def ai_loop(consumer, gameSettings, paddle):
	while True:
		# calculates the ball collision
		collision_position = await compute_aim_position(gameSettings)

		# adjusts the collision position / determinates where the paddle should move to
		aim_position = collision_position - gameSettings.paddleSize / 2 + random.randint(-10, 10)

		# creates async task to move the paddle to aim position
		move_task = asyncio.create_task(move_ai_to_aim(consumer, paddle, gameSettings, aim_position))

		# wait before cancel the movement task
		await asyncio.sleep(1)
		move_task.cancel()
