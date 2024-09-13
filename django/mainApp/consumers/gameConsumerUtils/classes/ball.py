import math
import random

class Ball:
	def __init__(self, gameSettings):
		self.task = None
		self.color = "#F19705"
		self.y = gameSettings.squareSize / 2
		self.x = gameSettings.squareSize / 2
		self.radius = 10
		self.speed = 5
		self.speedBase = 8

		# Set the initial angle based on the paddles' positions.
		self.angle = random.choice(self.__getRandomAngle(gameSettings))


	def __getRandomAngle(self, gameSettings):
		"""Generate a list of potential angles based on the active paddles."""
		randomAngles = []

		angle_map = {
			0: math.pi,  # Left paddle: 180 degrees
			1: 0,  # Right paddle: 0 degrees
			2: -math.pi / 2,  # Top paddle: -90 degrees
			3: math.pi / 2  # Bottom paddle: 90 degrees
		}

		for paddle in gameSettings.paddles:
			if paddle.isAlive:
				randomAngles.append(angle_map.get(paddle.id, 0))

		return randomAngles


	def __powerShot(self, paddle, collisionPosition):
		"""Adjusts the ball's speed, color, and radius based on the collision position."""

		# Calculate the speed factor based on the collision position.
		speedFactor = 1 - abs(collisionPosition - 0.5)
		self.speed = self.speedBase * speedFactor * 1.8

		# Adjust the ball's color and radius based on the speed factor.
		if speedFactor > 0.9:
			self.color = paddle.color
			self.radius = 8
		else:
			self.color = "#F19705"  # Default color
			self.radius = 10


	def __getReflectionAngle(self, paddle, maxAngle, reflectionAngle):
		"""Calculate the reflection angle of the ball based on the paddle's position."""

		# Calculate the reflection angle based on paddle ID and its orientation.
		adjustedAngle = max(-maxAngle, min(maxAngle, reflectionAngle))

		if paddle.id == 0:  # Left paddle
			self.angle = adjustedAngle
		elif paddle.id == 1:  # Right paddle
			self.angle = math.pi - adjustedAngle
		elif paddle.id == 2:  # Top paddle
			self.angle = math.pi / 2 - adjustedAngle
		elif paddle.id == 3:  # Bottom paddle
			self.angle = -math.pi / 2 + adjustedAngle


	def checkPaddleCollision(self, paddle, gameSettings):
		"""Detects and handles the collision between the ball and a paddle."""
		if not paddle.isAlive:
			return

		# Determine paddle dimensions based on orientation (vertical or horizontal).
		if paddle.id in [2, 3]:  # Vertical paddles
			thickness, size = gameSettings.paddleSize, gameSettings.paddleThickness
			offset, position = paddle.position, paddle.offset
		else:  # Horizontal paddles
			thickness, size = gameSettings.paddleThickness, gameSettings.paddleSize
			offset, position = paddle.offset, paddle.position

		# Calculate the closest point on the paddle to the ball.
		closestX = max(offset, min(self.x, offset + thickness))
		closestY = max(position, min(self.y, position + size))
		distance = math.sqrt((self.x - closestX) ** 2 + (self.y - closestY) ** 2)

		if distance < self.radius:
			# Determine the collision position relative to the paddle.
			collisionPosition = (closestX - offset) / thickness if paddle.id in [2, 3] else (closestY - position) / size
			reflectionAngle = (collisionPosition - 0.5) * math.pi
			maxAngle = math.pi / 3

			# Reflect the ball and apply power shot adjustments.
			self.__getReflectionAngle(paddle, maxAngle, reflectionAngle)
			self.__powerShot(paddle, collisionPosition)


	def checkWallCollision(self, gameSettings):
		"""Checks for wall collisions and handles reflections or game over scenarios."""
		max_position = gameSettings.squareSize - gameSettings.limit
		collision_checks = {
			0: self.x <= 0,
			1: self.x >= gameSettings.squareSize,
			2: self.y <= 0,
			3: self.y >= gameSettings.squareSize
		}

		reflection_checks = {
			0: self.x <= gameSettings.limit,
			1: self.x >= max_position,
			2: self.y <= gameSettings.limit,
			3: self.y >= max_position
		}

		for paddle in gameSettings.paddles:
			if paddle.isAlive:
				if collision_checks.get(paddle.id, False):
					return paddle.id
			else:
				if reflection_checks.get(paddle.id, False):
					if paddle.id in [0, 1]:
						self.angle = math.pi - self.angle
					else:
						self.angle = -self.angle

		return -1


	def move(self):
		"""Update the ball's position based on its current speed and angle."""
		delta_x = self.speed * math.cos(self.angle)
		delta_y = self.speed * math.sin(self.angle)
		self.x += delta_x
		self.y += delta_y

	def resetBall(self, gameSettings):
		"""Reset the ball to its initial position and speed."""
		self.radius = 10
		self.y = gameSettings.squareSize / 2
		self.x = gameSettings.squareSize / 2
		self.color = "#F19705"
		self.speed = 5

		self.angle = random.choice(self.__getRandomAngle(gameSettings))
