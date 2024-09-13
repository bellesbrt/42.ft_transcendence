from channels.db import database_sync_to_async
from .classes.gameSettings import GameSettings
from .senders.sendInitPaddlePosition import sendInitPaddlePosition
from .senders.sendUpdateScore import sendUpdateScore
from .senders.sendReloadPage import sendReloadPage
from .handleBallMove import handleBallMove

@database_sync_to_async
def getPlayer(playerID):
	from mainApp.models import Player
	return Player.objects.get(id=playerID)

@database_sync_to_async
def getPlayerIDList(gameSettings, gameID):
	from mainApp.models import Game
	game = Game.objects.get(id=gameID)
	gameSettings.playerIDList = [player for player in game.playerList]

@database_sync_to_async
def getGame(gameID):
	from mainApp.models import Game
	return Game.objects.get(id=gameID)

@database_sync_to_async
def savePlayer(player):
	player.save()


@database_sync_to_async
def sendTournamentReload(consumer):
	from mainApp.models import Game
	gameID = consumer.game_id
	game = Game.objects.get(id=gameID)
	if game.gameMode == 'init_tournament_game_sub_game':
		parentGame = Game.objects.get(id=game.parentGame)
		return parentGame.subGames


async def handleInitGame(consumer, gameID, gameMode, playerID):
	"""Handle the initialization of a game based on the game mode and player readiness."""
	game = await getGame(gameID)
	if not validate_player_in_game(playerID, game):
		return False

	await update_player_ready_status(playerID)

	if gameMode in ['init_local_game', 'init_ai_game', 'init_wall_game']:
		await launchAnyGame(consumer, gameID, gameMode, True)
		return True

	if not await check_all_players_ready(game, consumer, gameID, gameMode):
		return False

	if gameMode in [
		'init_ranked_solo_game',
		'init_death_game',
		'init_tournament_game',
		'init_tournament_game_final_game',
		'init_tournament_game_third_place_game'
	]:
		await launchAnyGame(consumer, gameID, gameMode, False)
	return True

async def launchAnyGame(consumer, gameID, gameMode, isLocalGame):
	"""Initialize and launch a game session based on the provided game settings."""
	if gameID not in consumer.gameSettingsInstances:
		consumer.gameSettingsInstances[gameID] = GameSettings(gameID, gameMode)

	gameSettings = consumer.gameSettingsInstances[gameID]
	gameSettings.isLocalGame = isLocalGame

	await initialize_game(consumer, gameSettings)

async def initialize_game(consumer, gameSettings):
	"""Perform the initial setup for the game by loading player data and sending the initial game state."""
	await getPlayerIDList(gameSettings, gameSettings.gameID)
	await sendInitPaddlePosition(consumer, gameSettings)
	await sendUpdateScore(consumer, gameSettings)
	await handleBallMove(consumer, gameSettings)

def validate_player_in_game(playerID, game):
	"""Check if a player is part of the game."""
	return playerID in game.playerList


async def update_player_ready_status(playerID):
	"""Set the player's readiness status to True and save the player data."""
	player = await getPlayer(playerID)
	player.isReady = True
	await savePlayer(player)


async def check_all_players_ready(game, consumer, gameID, gameMode):
	"""Check if all players in the game are ready. If not, reload pages as needed."""
	for playerID in game.playerList:
		player = await getPlayer(playerID)
		if not player.isReady:
			if gameMode == 'init_tournament_game':
				await reload_tournament_sub_games(consumer, playerID)
			await sendReloadPage(consumer, gameID, playerID)
			return False
	return True


async def reload_tournament_sub_games(consumer, playerID):
	"""Reload tournament sub-games if a player is not ready."""
	subGamesList = await sendTournamentReload(consumer)
	for sub_gameID in subGamesList:
		await sendReloadPage(consumer, sub_gameID, playerID)
