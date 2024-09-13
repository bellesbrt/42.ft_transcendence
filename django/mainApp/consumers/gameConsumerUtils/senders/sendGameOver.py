from channels.db import database_sync_to_async

@database_sync_to_async
def addStatToPlayer(playerID, paddle):
	from mainApp.models import Player, Score, Game
	player = Player.objects.get(id=playerID)
	gameID = player.currentGameID
	game = Game.objects.get(id=gameID)

	score = Score(player=player, position=paddle.rankPosition, score=paddle.score)
	score.save()

	game.scores.add(score)
	game.save()

async def sendGameOver(consumer, gameSettings, paddle):
	"""
	Sends a 'game_over' message to all connected clients for a specific game.

	Args:
		consumer: The consumer instance handling WebSocket connections.
		gameSettings: The settings and state of the current game.
		paddle: The paddle that caused the game to end.
	"""
	# Determine the player ID based on the game mode and paddle ID.
	playerID = gameSettings.playerIDList[0] if gameSettings.isLocalGame else gameSettings.playerIDList[paddle.id]


	# Add statistics to the player if not a local game.
	if not gameSettings.isLocalGame:
		await addStatToPlayer(playerID, paddle)

	# Send the 'game_over' event to the WebSocket group associated with the game.
	await consumer.channel_layer.group_send(f'game_{gameSettings.gameID}',
		{
			'type': 'game_over',
			'gameID': gameSettings.gameID,
			'playerID': playerID,
		}
	)
