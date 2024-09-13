import uuid
from datetime import datetime
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model, logout
from django.middleware.csrf import get_token
from django.utils import timezone
from django.db import transaction


from ..models import Notification, Channel, Game, Score


# --------------------------------------------------------------------------------
# ------------------------------------ Utils -------------------------------------
# --------------------------------------------------------------------------------

def get_unauthenticated_response():
    return JsonResponse({
        'success': False,
        'message': 'The user is not authenticated'
    }, status=401)

def get_system_user_error_response():
    return JsonResponse({
        'success': False,
        'message': 'You cannot interact with the system user'
    }, status=401)

def get_valid_user_id(id):
    try:
        user_id = int(id)
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid id'
        }, status=400)
    return user_id

def get_user_or_error(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User does not exist'
        }, status=404)
    return user


def header(request):
	if request.user.is_authenticated:
		return JsonResponse({
			'isAuthenticated': request.user.is_authenticated,
			'username': request.user.username,
			'photo_url': request.user.photo.url,
			'nbNewNotifications': request.user.nbNewNotifications,
		}, status=200)
	else:
		return JsonResponse({
			'isAuthenticated': False,
		}, status=200)

def generate_csrf_token(request):
	return JsonResponse({'token': get_token(request)}, status=200)


# --------------------------------------------------------------------------------
# ---------------------------------- Get Users -----------------------------------
# --------------------------------------------------------------------------------


def isAuthenticated(request):
	if request.user.is_authenticated:
		return JsonResponse({
			'isAuthenticated': True
		}, status=200)

	else:
		return JsonResponse({
			'isAuthenticated': False
		}, status=200)


def get_username(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'username': None
		}, status=401)

	# Convert ID
	try:
		id = int(id)
	except ValueError:
		return JsonResponse({
			'username': None
		}, status=401)

	if id == 0:
		return JsonResponse({
			'success': False,
			'message': "You cannot interact with the system user"
		}, status=200)

	# Check if the user exist
	User = get_user_model()
	try:
		user = User.objects.get(id=id)
	except User.DoesNotExist:
		return JsonResponse({
			'username': None
		}, status=401)

	return JsonResponse({
		'username': user.username
	}, status=200)


def get_user(request, username=None):
	if not request.user.is_authenticated:
		return JsonResponse({
			'user': None,
			'isCurrentUser': False,
			'isAuthenticated': False
		}, status=401)

	index = 1

	# Get information about the current user
	if not username or username == request.user.username or username == "me":
		channels_dict = {}
		allGames_dict = {}
		channels = list(request.user.channels.all())

		# Order by last interaction
		channels.sort(key=lambda x: x.last_interaction, reverse=True)

		for channel in channels:

			# Get users
			users_dict = {}
			for user in channel.users.all():
				users_dict[user.id] = {
					'id': user.id,
					'username': user.username,
					'photo_url': user.photo.url,
					'status': user.status,
					'followed': user.id in request.user.follows,
					'blocked': user.id in request.user.blockedUsers,
				}

			# Get last message of the channel
			last_message_obj = channel.messages.order_by('-timestamp').first()
			if last_message_obj:
				sender = last_message_obj.sender.id
				if sender == request.user.id:
					sender = request.user.username
				else:
					for user in channel.users.all():
						if user.id == int(sender):
							sender = user.username
							break

				last_message = {
					'sender': "You" if sender == request.user.username else sender,
					'message': last_message_obj.message if not last_message_obj.sender.id in request.user.blockedUsers else "This message is blocked",
					'timestamp': timezone.localtime(last_message_obj.timestamp).strftime("%d-%m-%Y %H:%M"),
				}
			else:
				last_message = None

			# Change the name of the channel if it is a private channel
			if channel.private and len(channel.users.all()) == 2:
				for user in channel.users.all():
					if user.id != request.user.id:
						channel_name = user.username
						break
			else:
				channel_name = channel.name

			# Get the creator username
			creator_username = 'No creator available'
			if channel.creator:
				if (channel.creator == request.user.id):
					creator_username = "You"
				else:
					User = get_user_model()
					try:
						user = User.objects.get(id=channel.creator)
						creator_username = user.username
					except User.DoesNotExist:
						pass

			# Add channel to the list
			channels_dict[channel.room_id] = {
				'id': channel.id,
				'room_id': channel.room_id,
				'name': channel_name,
				'private': channel.private,
				'tournament': channel.tournament,
				'users': users_dict,
				'last_message': last_message,
				'creator': channel.creator if channel.creator else None,
				'creator_username': creator_username,
				'description': channel.description if channel.description else 'No description available',
			}

		# Get all games
		game_ids = request.user.player.allGames
		games = Game.objects.filter(id__in=game_ids).order_by('-date')
		for game in games:
			players_info_dict = {}
			id = 1
			players_info_dict[0] = {
				'id': request.user.id,
				'username': request.user.username,
				'photo_url': request.user.photo.url,
			}
			for player in game.playerList:
				User = get_user_model()
				user = User.objects.get(player__id=player)
				if (user.id == request.user.id):
					continue
				players_info_dict[id] = {
					'id': user.id,
					'username': user.username,
					'photo_url': user.photo.url,
				}
				id += 1

			if (game.scores.count() > 2):
				scores = game.scores.filter(player__id=request.user.player.id)
				if (scores == None):
					result = "No result"
				if (scores.first().position == 1):
					result = "1st"
				elif (scores.first().position == 2):
					result = "2nd"
				elif (scores.first().position == 3):
					result = "3rd"
				elif (scores.first().position == 4):
					result = "4th"
			else:
				try:
					scores = game.scores.filter(player__id=request.user.player.id)
					if (scores == None):
						result = "No result"
					else:
						result = str(scores.first().score) + "-"
						for player_id in game.playerList:
							if (player_id != request.user.player.id):
								scores = game.scores.filter(player__id=player_id)
								if (scores == None):
									result = "No result"
								else:
									result += str(scores.first().score)
				except:
					result = "No result"

			gameMode = game.gameMode
			game_mode = ['init_ranked_solo_game', 'init_tournament_game', 'init_death_game']
			game_title = ['Solo Game', 'Tournament Game', 'Deathmatch Game']

			if (game.gameMode in game_mode):
				gameMode = game_title[game_mode.index(game.gameMode)]
			allGames_dict[index] = {
				'id': game.id,
				'date': timezone.localtime(game.date).strftime("%d-%m-%Y %H:%M"),
				'duration': game.duration,
				'playersList': players_info_dict,
				'gameMode': gameMode,
				'result': result,
			}
			index += 1

		if (request.user.player.currentGameID):
			game = Game.objects.get(id=request.user.player.currentGameID)

		# Get player information
		player_info = {
			'currentGameID': request.user.player.currentGameID,
			'gameMode': game.gameMode if request.user.player.currentGameID else None,
			'isReady': request.user.player.isReady,
			'isReady': request.user.player.isReady,
			'soloPoints': request.user.player.soloPoints,
			'deathPoints': request.user.player.deathPoints,
			'tournamentPoints': request.user.player.tournamentPoints,
			'totalPoints': request.user.player.totalPoints,
			'gamePlayed': user.player.score_set.count(),
			'allGames':	allGames_dict,
		}

		# Get information about the user
		user_dict = {
			'id': request.user.id,
			'is42': request.user.is42,
			'isOfficial': request.user.isOfficial,
			'email': request.user.email,
			'emailAlerts': request.user.emailAlerts,
			'username': request.user.username,
			'description': request.user.description,
			'photo_url': request.user.photo.url,
			'status': request.user.status,
			'nbNewNotifications': request.user.nbNewNotifications,
			'channels': channels_dict,
			'follows': request.user.follows,
			'friendRequests': request.user.friendRequests,
			'blockedUsers': request.user.blockedUsers,
			'favoritesChannels': request.user.favoritesChannels,
			'player': player_info,
		}

		return JsonResponse({
			'user': user_dict,
			'isCurrentUser': True,
			'isAuthenticated': True
		}, status=200)

	# Get information about the user with the username
	else:

		allGames_dict = {}
		User = get_user_model()
		try:
			user = User.objects.get(username=username)
		except User.DoesNotExist:
			return JsonResponse({'user': None})


		game_ids = user.player.allGames
		games = Game.objects.filter(id__in=game_ids).order_by('-date')
		for game in games:
			id = 1
			players_info_dict = {}
			players_info_dict[0] = {
				'id': user.id,
				'username': user.username,
				'photo_url': user.photo.url,
			}
			for player in game.playerList:
				User = get_user_model()
				n_user = User.objects.get(player__id=player)
				if (n_user.id == user.id):
					continue
				players_info_dict[id] = {
					'id': n_user.id,
					'username': n_user.username,
					'photo_url': n_user.photo.url,
				}
				id += 1

			if (game.scores.count() > 2):
				scores = game.scores.filter(player__id=user.player.id)
				if (scores == None):
					result = "No result"
				if (scores.first().position == 1):
					result = "1st"
				elif (scores.first().position == 2):
					result = "2nd"
				elif (scores.first().position == 3):
					result = "3rd"
				elif (scores.first().position == 4):
					result = "4th"
			else:
				try:
					scores = game.scores.filter(player__id=user.player.id)
					if (scores == None):
						result = "No result"
					else:
						result = str(scores.first().score) + "-"
						for player_id in game.playerList:
							if (player_id != user.player.id):
								scores = game.scores.filter(player__id=player_id)
								if (scores == None):
									result = "No result"
								else:
									result += str(scores.first().score)
				except:
					result = "No result"

			game_mode = ['init_ranked_solo_game', 'init_tournament_game', 'init_death_game']
			game_title = ['Solo Game', 'Tournament Game', 'Deathmatch Game']

			if (game.gameMode in game_mode):
				gameMode = game_title[game_mode.index(game.gameMode)]

			allGames_dict[index] = {
				'id': game.id,
				'date': timezone.localtime(game.date).strftime("%d-%m-%Y %H:%M"),
				'duration': game.duration,
				'playersList': players_info_dict,
				'gameMode': gameMode,
				'result': result,
			}
			index += 1

		# Get player information
		player_info = {
			'currentGameID': user.player.currentGameID,
			'isReady': user.player.isReady,
			'soloPoints': user.player.soloPoints,
			'deathPoints': user.player.deathPoints,
			'tournamentPoints': user.player.tournamentPoints,
			'totalPoints': user.player.totalPoints,
			'gamePlayed': user.player.score_set.count(),
			'allGames':	allGames_dict,
		}

		user_dict = {
			'id': user.id,
			'isOfficial': user.isOfficial,
			'username': user.username,
			'description': user.description,
			'photo_url': user.photo.url,
			'status': user.status,
			'followed': user.id in request.user.follows,
			'blocked': user.id in request.user.blockedUsers,
			'friendRequests': user.friendRequests,
			'player': player_info,
		}

		return JsonResponse({
			'user': user_dict,
			'isCurrentUser': False
		}, status=200)


### users
def users(request):
    if not request.user.is_authenticated:
        return get_unauthenticated_response_users()

    users_dict = get_users_dict(request.user)

    return JsonResponse({
        'users': users_dict
    }, status=200)


def get_unauthenticated_response_users():
    return JsonResponse({
        'users': None
    }, status=401)


def get_users_dict(user):
    users_dict = {}
    users = get_users_except_system_and_self(user)

    for other_user in users:
        users_dict[other_user.id] = {
            'id': other_user.id,
            'username': other_user.username,
            'photo_url': other_user.photo.url,
            'status': other_user.status,
            'followed': other_user.id in user.follows,
            'blocked': other_user.id in user.blockedUsers,
        }

    return users_dict

def get_users_except_system_and_self(user):
    User = get_user_model()
    users = list(User.objects.exclude(id__in=[0, user.id]))
    return users

def change_status(request, status):

	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': 'The user is not authenticated',
			'user_id': None
		}, status=200)

	if (request.user.player.isReady == True):
		request.user.set_status('in-game')
		return JsonResponse({
			'success': True,
			'message': 'Your status had to be set to in-game',
			'user_id': request.user.id,
			'status': 'in-game'
		}, status=200)

	if (request.user.player.currentGameID):
		request.user.set_status('waiting-game')
		return JsonResponse({
			'success': True,
			'message': 'Your status had to be set to waiting-game',
			'user_id': request.user.id,
			'status': 'waiting-game'
		}, status=200)

	request.user.set_status(status)

	return JsonResponse({
		'success': True,
		'message': 'Status changed',
		'user_id':request.user.id
	}, status=200)


# --------------------------------------------------------------------------------
# ---------------------------------- Set Users -----------------------------------
# --------------------------------------------------------------------------------


def follow(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Convert ID
	try:
		id = int(id)
	except ValueError:
		return JsonResponse({
			'success': False,
			'message': "Invalid id"
		}, status=401)

	if id == 0:
		return JsonResponse({
			'success': False,
			'message': "You cannot interact with the system user"
		}, status=401)

	if id == request.user.id:
		return JsonResponse({
			'success': False,
			'message': "You cannot follow yourself"
		}, status=401)

	# Check if the user exist and if he is not already followed
	User = get_user_model()
	try:
		userTo = User.objects.get(id=id)
		if id in request.user.follows:
			return JsonResponse({
				'success': False,
				'message': "User already followed"
			}, status=401)

		if id in request.user.blockedUsers:
			return JsonResponse({
				'success': False,
				'message': "User is blocked"
			}, status=401)

		if request.user.id in userTo.blockedUsers:
			return JsonResponse({
				'success': False,
				'message': "You are blocked by this user"
			}, status=401)

	except User.DoesNotExist:
		return JsonResponse({
			'success': False,
			'message': "User does not exist"
		}, status=401)

	if (request.user.id in userTo.friendRequests):
		userTo.friendRequests.remove(request.user.id)
		userTo.follows.append(request.user.id)
		userTo.save()
		request.user.follows.append(id)
		request.user.save()

		notification = Notification(user=userTo, type='accept-friend', imageType='user', imageUser=request.user.photo.url, title="New friend", message=f"{request.user.username} accepted your friend request.", redirect=f"/profile/{request.user.username}")
		notification.save()

		return JsonResponse({
			'success': True,
			'message': "Successful follow"
		}, status=200)

	request.user.friendRequests.append(id)
	request.user.save()

	# Don't send the notification if the receiver blocked the sender
	if request.user.id not in userTo.blockedUsers:
		notification = Notification(user=userTo, type='request-friend', imageType='user', userID=request.user.id, imageUser=request.user.photo.url, title="New friend request", message=f"{request.user.username} send you a friend request.", redirect=f"/profile/{request.user.username}")
		notification.save()

	return JsonResponse({
		'success': True,
		'message': "Successful send friend request"
	}, status=200)


def unfollow(request, id):
    if not request.user.is_authenticated:
        return get_unauthenticated_response()

    user_id = get_valid_user_id(id)
    if not user_id:
        return user_id

    if user_id == 0:
        return get_system_user_error_response()

    if user_id == request.user.id:
        return get_self_unfollow_error_response()

    if user_id not in request.user.follows:
        return JsonResponse({
            'success': False,
            'message': 'User is not followed'
        }, status=400)

    unfollow_user(request.user, user_id)

    return JsonResponse({
        'success': True,
        'message': 'Successful unfollow'
    }, status=200)


def get_self_unfollow_error_response():
    return JsonResponse({
        'success': False,
        'message': 'You cannot unfollow yourself'
    }, status=401)


def unfollow_user(user, user_id):
    if user_id in user.follows:
        user.follows.remove(user_id)
        user.save()

        User = get_user_model()
        try:
            user_to_unfollow = User.objects.get(id=user_id)
            user_to_unfollow.follows.remove(user.id)
            user_to_unfollow.save()
        except User.DoesNotExist:
            pass


def block(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Convert ID
	try:
		id = int(id)
	except ValueError:
		return JsonResponse({
			'success': False,
			'message': "Invalid id"
		}, status=401)

	if id == 0:
		return JsonResponse({
			'success': False,
			'message': "You cannot interact with the system user"
		}, status=401)

	if id == request.user.id:
		return JsonResponse({
			'success': False,
			'message': "You cannot block yourself"
		}, status=401)

	# Check if the user exist and if he is not already blocked
	if id in request.user.blockedUsers:
		return JsonResponse({
			'success': False,
			'message': "User already blocked"
		}, status=401)

	# Unfollow the user if he is in the follows list
	if id in request.user.follows:
		request.user.follows.remove(id)

		User = get_user_model()
		try:
			userTo = User.objects.get(id=id)
			userTo.follows.remove(request.user.id)
			userTo.save()
		except User.DoesNotExist:
			pass

	if id in request.user.friendRequests:
		request.user.friendRequests.remove(id)

	# Block the user
	request.user.blockedUsers.append(id)
	request.user.save()

	return JsonResponse({
		'success': True,
		'message': "Successful block"
	}, status=200)


def unblock(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	if id == 0:
		return JsonResponse({
			'success': False,
			'message': "You cannot interact with the system user"
		}, status=401)

	if id == request.user.id:
		return JsonResponse({
			'success': False,
			'message': "You cannot unblock yourself"
		}, status=401)

	# Convert ID
	try:
		id = int(id)
	except ValueError:
		return JsonResponse({
			'success': False,
			'message': "Invalid id"
		}, status=401)

	# Check if the user exist and if he is blocked
	if id not in request.user.blockedUsers:
		return JsonResponse({
			'success': False,
			'message': "User not blocked"
		}, status=401)

	# Unblock the user
	request.user.blockedUsers.remove(id)
	request.user.save()

	return JsonResponse({
		'success': True,
		'message': "Successful unblock"
	}, status=200)


def sign_out(request):
	if request.user.is_authenticated:
		# Sign out the user
		request.user.set_status("offline")
		logout(request)

		return JsonResponse({
			'success': True,
			'message': "Successful sign out"
		}, status=200)

	else:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)


# --------------------------------------------------------------------------------
# ------------------------------ Get Notifications -------------------------------
# --------------------------------------------------------------------------------


def get_notifications(request):
	if not request.user.is_authenticated:
		return JsonResponse({
			'notifications': None
		}, status=401)

	# Get notifications
	notifications = list(request.user.notifications.all().order_by('-date'))
	request.user.nbNewNotifications = 0
	request.user.save()

	notifications_dict = {}
	for notification in notifications:
		notifications_dict[notification.id] = {
			'id': notification.id,
			'title': notification.title,
			'message': notification.message,
			'date': timezone.localtime(notification.date).strftime("%d-%m-%Y %H:%M"),
			'redirect': notification.redirect,
			'interacted': notification.interacted,
			'read': notification.read,
			'type': notification.type,
			'imageType': notification.imageType,
			'imageUser': notification.imageUser,
			'userID': notification.userID,
		}

	# Mark all notifications as read
	request.user.notifications.all().update(read=True)

	return JsonResponse({
		'notifications': notifications_dict
	}, status=200)


def interacted_notification(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Get notification
	try:
		notification = request.user.notifications.get(id=id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': "Notification does not exist"
		}, status=401)

	# Mark the notification as interacted
	notification.interact()

	return JsonResponse({
		'success': True,
		'message': "Notification mark as interacted"
	}, status=200)


# --------------------------------------------------------------------------------
# ------------------------------ Set Notifications -------------------------------
# --------------------------------------------------------------------------------


def delete_notification(request, id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Get notification
	try:
		notification = request.user.notifications.get(id=id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': "Notification does not exist"
		}, status=200)

	# Delete notification
	notification.delete()

	return JsonResponse({
		'success': True,
		'message': "Notification deleted"
	}, status=200)


def delete_all_notifications(request):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Delete all notifications
	request.user.notifications.all().delete()

	return JsonResponse({
		'success': True,
		'message': "All notifications deleted"
	}, status=200)



# --------------------------------------------------------------------------------
# -------------------------------- Get Channels ----------------------------------
# --------------------------------------------------------------------------------


def get_messages(request, room_id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'messages': None
		}, status=401)

	# Get channel
	try:
		channel = request.user.channels.get(room_id=room_id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'messages': None
		}, status=401)

	# Get messages
	messages = channel.messages.all().order_by('timestamp')
	messages_dict = {}

	for message in messages:
		messages_dict[message.id] = {
			'sender': message.sender.id,
			'username': message.sender.username,
			'message': message.message,
			'timestamp': message.timestamp,
		}

	return JsonResponse({
		'messages': messages_dict
	}, status=200)


# --------------------------------------------------------------------------------
# -------------------------------- Set Channels ----------------------------------
# --------------------------------------------------------------------------------


def create_channel(request):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': 'The user is not authenticated'
		}, status=401)

	# Get parameters
	private = request.GET.get('private', 'False') == 'True'
	try:
		user_ids = list(map(int, request.GET.getlist('user_ids')))
	except ValueError:
		return JsonResponse({
			'success': False,
			'message': 'Invalid user_ids'
		}, status=401)

	# Create a default channel name
	channel_name = "group"

	# Channel information
	room_id = str(uuid.uuid4())
	users = []

	# Get the users
	User = get_user_model()
	for user_id in user_ids:
		try:
			user = User.objects.get(id=user_id)
			users.append(user)
		except User.DoesNotExist:
			return JsonResponse({
				'success': False,
				'message': f"User {user_id} does not exist"
			}, status=401)

	# Check if the channel is empty
	if len(users) == 0:
		return JsonResponse({
			'success': False,
			'message': 'The channel is empty'
		}, status=401)

	# Check if the channel is really private
	if private and len(users) != 2:
		return JsonResponse({
			'success': False,
			'message': 'A private channel must have exactly two users'
		}, status=401)

	# Check if a private channel already exists between the two users
	if len(users) == 2:
		existing_channel = Channel.objects.filter(private=True, users=users[0]).filter(users=users[1])
		if existing_channel.exists():
			return JsonResponse({
				'success': False,
				'message': 'A private channel already exists between the two users'
			}, status=401)

	# Create the channel
	channel = Channel.objects.create(private=private, room_id=room_id, name=channel_name)
	channel.users.set(users)
	channel.save()

	return JsonResponse({
		'success': True,
		'message': 'Channel created',
		'room_id': room_id
	}, status=200)


def add_to_favorite(request, room_id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Check if the channel exist
	try:
		request.user.channels.get(room_id=room_id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': "Channel does not exist"
		}, status=401)

	# Check if the channel is not already in favorite
	if room_id in request.user.favoritesChannels:
		return JsonResponse({
			'success': False,
			'message': "Channel already in favorite"
		}, status=401)

	request.user.favoritesChannels.append(room_id)
	request.user.save()

	return JsonResponse({
		'success': True,
		'message': "Successful add to favorite",
		'list': request.user.favoritesChannels
	}, status=200)


def remove_from_favorite(request, room_id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': "The user is not authenticated"
		}, status=401)

	# Check if the channel exist
	try:
		request.user.channels.get(room_id=room_id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': "Channel does not exist"
		}, status=401)

	# Check if he is not already in favorite
	if not room_id in request.user.favoritesChannels:
		return JsonResponse({
			'success': False,
			'message': "Channel is not in favorite"
		}, status=401)

	request.user.favoritesChannels.remove(room_id)
	request.user.save()

	return JsonResponse({
		'success': True,
		'message': "Successful remove from favorite",
		'list': request.user.favoritesChannels
	}, status=200)


def add_user_to_room(request, room_id, user_id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': 'The user is not authenticated'
		}, status=401)

	if user_id == 0:
		return JsonResponse({
			'success': False,
			'message': 'You cannot interact with the system user'
		}, status=401)

	# Get the channel
	try:
		channel = request.user.channels.get(room_id=room_id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': 'Channel does not exist'
		}, status=401)

	# Get the user
	User = get_user_model()
	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		return JsonResponse({
			'success': False,
			'message': 'User does not exist'
		}, status=401)

	# Add the user to the channel
	if (user in channel.users.all()):
		return JsonResponse({
			'success': False,
			'message': 'User already in the channel'
		}, status=401)
	channel.users.add(user)
	channel.save()

	return JsonResponse({
		'success': True,
		'message': 'User added to the channel',
		'username': user.username
	}, status=200)


### Leave Channel
def leave_channel(request, room_id):
    if not request.user.is_authenticated:
        return get_unauthenticated_response()

    channel = get_channel_or_error(request.user, room_id)
    if not channel:
        return channel

    if request.user not in channel.users.all():
        return JsonResponse({
            'success': False,
            'message': 'User not in the channel'
        }, status=401)

    remove_from_favorites(request.user, room_id)
    remove_user_from_channel(request.user, channel)

    return JsonResponse({
        'success': True,
        'message': 'User left the channel'
    }, status=200)

def remove_from_favorites(user, room_id):
    if room_id in user.favoritesChannels:
        user.favoritesChannels.remove(room_id)
        user.save()

def get_channel_or_error(user, room_id):
    try:
        channel = user.channels.get(room_id=room_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Channel does not exist'
        }, status=404)
    return channel

def remove_user_from_channel(user, channel):
    channel.users.remove(user)
    channel.save()


def create_invite_game(request, room_id):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False,
			'message': 'User not authenticated'
		}, status=401)

	try:
		channel = request.user.channels.get(room_id=room_id)
	except ObjectDoesNotExist:
		return JsonResponse({
			'success': False,
			'message': 'Channel does not exist'
		}, status=401)

	if (len(channel.users.all()) != 2):
		return JsonResponse({
			'success': False,
			'message': 'Not enough players in the channel'
		}, status=401)

	if (request.user.player.id not in channel.users.all().values_list('player__id', flat=True)):
		return JsonResponse({
			'success': False,
			'message': 'User not in the channel'
		}, status=401)

	if (request.user.player.id in channel.player_list):
		return JsonResponse({
			'success': False,
			'message': 'You are already asking for a game'
		}, status=401)

	if (request.user.player.currentGameID != None):
		return JsonResponse({
			'success': False,
			'message': 'You are already in a game or waiting for a game'
		}, status=401)

	channel.player_list.append(request.user.player.id)
	channel.save()

	if len(channel.player_list) == 2:
		# Get the other player
		other_player = channel.users.exclude(id=request.user.id).first()
		request.user.player.currentGameID = other_player.player.currentGameID
		request.user.player.allGames.append(other_player.player.currentGameID)
		request.user.player.save()
		# Get the game
		game = Game.objects.get(id=other_player.player.currentGameID)
		game.playerList.append(request.user.player.id)
		game.save()
		# Clear the player list
		channel.player_list = []
		channel.save()
		return JsonResponse({
			'success': True,
			'message': 'Game joined'
		}, status=200)

	newGame = Game.objects.create(
		duration=0,
		gameMode='init_ranked_solo_game',
		playerList=[request.user.player.id],
		isPrivate=True,
		room_id=room_id,
	)
	newGame.save()

	request.user.player.currentGameID = newGame.id
	request.user.player.allGames.append(newGame.id)
	request.user.player.save()

	return JsonResponse({
		'success': True,
		'message': 'Game created'
	}, status=200)


# --------------------------------------------------------------------------------
# ---------------------------------- Get Games -----------------------------------
# --------------------------------------------------------------------------------

### get_game_info
def get_game_info(request):
    if not request.user.is_authenticated:
        return get_unauthenticated_response_game_info()

    game = get_user_game(request.user)
    if not game:
        return get_unauthenticated_response_game_info()

    if game.gameMode == 'init_tournament_game':
        game = handle_tournament_game(game, request.user)

    players_info = get_players_info(game.playerList)
    game_type = get_game_type(game.gameMode)

    response_data = {
        'success': True,
        'game_id': game.id,
        'user_id': request.user.id,
        'player_id': request.user.player.id,
        'players_username': players_info['usernames'],
        'players_photo': players_info['photos'],
        'type_game': game_type,
        'room_id': request.user.player.currentRoomID,
        'gameMode': game.gameMode
    }

    return JsonResponse(response_data, status=200)

def get_unauthenticated_response_game_info():
    return JsonResponse({
        'success': False,
        'game_id': None,
        'player_id': None
    }, status=200)

def get_user_game(user):
    game_id = user.player.currentGameID
    if not game_id:
        return None

    try:
        return Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return None

def handle_tournament_game(game, user):
    if user.player.id not in game.playerList:
        return

    user.player.currentGameID = game.id
    user.player.save()
    return game

def get_players_info(player_ids):
    User = get_user_model()
    usernames = []
    photos = []
    for player_id in player_ids:
        user = User.objects.get(player__id=player_id)
        usernames.append(user.username)
        photos.append(user.photo.url)
    return {'usernames': usernames, 'photos': photos}

def get_game_type(game_mode):
    local_game_modes = ['init_local_game', 'init_ai_game', 'init_wall_game']
    return 'local' if game_mode in local_game_modes else 'online'


### Get Game Over

def get_game_over(request, gameID):
    if not is_authenticated(request):
        return unauthorized_response()

    player = request.user.player
    if not is_player_in_game(player, gameID):
        return not_in_game_response()

    game = get_game_or_respond(gameID)
    if not game:
        return game_does_not_exist_response()

    gameMode = game.gameMode

    if is_simple_game_mode(gameMode):
        return handle_simple_game_mode(game, player, gameMode)

    scores = get_player_scores(game, player)
    if not scores:
        return no_score_found_response()

    return handle_game_modes(game, player, scores, gameMode)


def is_authenticated(request):
    return request.user.is_authenticated


def unauthorized_response():
    return JsonResponse({'success': False}, status=401)


def is_player_in_game(player, gameID):
    return player.currentGameID == gameID


def not_in_game_response():
    return JsonResponse({
        'success': False,
        'message': 'The user is not in the game'
    }, status=200)


def get_game_or_respond(gameID):
    try:
        return Game.objects.get(id=gameID)
    except Game.DoesNotExist:
        return None


def game_does_not_exist_response():
    return JsonResponse({
        'success': False,
        'message': 'Game does not exist'
    }, status=200)


def is_simple_game_mode(gameMode):
    return gameMode in ['init_local_game', 'init_ai_game', 'init_wall_game']


def handle_simple_game_mode(game, player, gameMode):
    end_game(game, player)
    return JsonResponse({
        'success': True,
        'gameMode': gameMode,
        'user_id': player.user.id,
    }, status=200)


def get_player_scores(game, player):
    return game.scores.filter(player__id=player.id).first()


def no_score_found_response():
    return JsonResponse({
        'success': False,
        'message': 'No score found'
    }, status=200)


def handle_game_modes(game, player, scores, gameMode):
    score = scores.score
    position = scores.position

    if gameMode == "init_ranked_solo_game":
        update_solo_game_scores(player, score)
    elif gameMode == "init_death_game":
        update_death_game_scores(player, position)
    elif gameMode == "init_tournament_game_sub_game":
        return redirect_to_finals_game(game, player)
    elif gameMode == "init_tournament_game_final_game":
        score = handle_final_game(player, position)
    elif gameMode == "init_tournament_game_third_place_game":
        score, position = handle_third_place_game(player, position)

    end_game(game, player)

    return JsonResponse({
        'success': True,
        'score': score,
        'position': position,
        'gameMode': gameMode,
        'user_id': player.user.id,
    }, status=200)


def update_solo_game_scores(player, score):
    player.soloPoints.append(score + (player.soloPoints[-1] if player.soloPoints else 0))
    player.totalPoints.append(score + (player.totalPoints[-1] if player.totalPoints else 0))
    player.save()


def update_death_game_scores(player, position):
    positionsScore = [10, 7, 3, 0]
    player.deathPoints.append(positionsScore[position - 1] + (player.deathPoints[-1] if player.deathPoints else 0))
    player.totalPoints.append(positionsScore[position - 1] + (player.totalPoints[-1] if player.totalPoints else 0))
    player.save()


def handle_final_game(player, position):
    tournamentPositionsScore = [20, 15]
    score = tournamentPositionsScore[position - 1]
    player.tournamentPoints.append(score + (player.tournamentPoints[-1] if player.tournamentPoints else 0))
    player.totalPoints.append(score + (player.totalPoints[-1] if player.totalPoints else 0))
    player.save()

    save_score(player, position, score)
    return score


def handle_third_place_game(player, position):
    tournamentPositionsScore = [7, 0]
    score = tournamentPositionsScore[position - 1]
    player.tournamentPoints.append(score + (player.tournamentPoints[-1] if player.tournamentPoints else 0))
    player.totalPoints.append(score + (player.totalPoints[-1] if player.totalPoints else 0))
    player.save()

    save_score(player, position + 2, score)
    return score, position + 2


def save_score(player, position, score):
    score_obj = Score(player=player, position=position, score=score)
    score_obj.save()
    last_game = Game.objects.get(id=player.allGames[-1])
    last_game.scores.add(score_obj)
    last_game.save()


def end_game(game, player):
    game.isOver = True
    game.save()

    player.currentGameID = None
    player.isReady = False
    player.save()

### Get Ranking Point

def get_ranking_points(request, sortedBy):
    if not is_authenticated(request):
        return unauthorized_response()

    users = get_all_users()
    order, sortedBy = parse_sorting_method(sortedBy)

    calculate_average_points(users)

    sorted_users = sort_users(users, sortedBy, order)
    users_dict = build_users_dict(sorted_users, request.user, order)

    return JsonResponse({'success': True, 'users': users_dict}, status=200)


def is_authenticated(request):
    return request.user.is_authenticated


def unauthorized_response():
    return JsonResponse({'success': False}, status=401)


def get_all_users():
    User = get_user_model()
    return User.objects.all()


def parse_sorting_method(sortedBy):
    if len(sortedBy.split('_')) == 2:
        return sortedBy.split('_')[1], sortedBy.split('_')[0]
    return None, sortedBy


def calculate_average_points(users):
    for user in users:
        if len(user.player.totalPoints) > 1:
            soloPoints = user.player.soloPoints[-1]
            deathPoints = user.player.deathPoints[-1]
            tournamentPoints = user.player.tournamentPoints[-1] / 2
            totalPoints = soloPoints + deathPoints + tournamentPoints
            user.player.averagePoints = round((totalPoints / (len(user.player.totalPoints) - 1)) * 100) / 100
        else:
            user.player.averagePoints = 0
        user.save()


def sort_users(users, sortedBy, order):
    sort_key = {
        'solo': lambda x: x.player.soloPoints[-1],
        'death': lambda x: x.player.deathPoints[-1],
        'tournament': lambda x: x.player.tournamentPoints[-1],
        'total': lambda x: x.player.totalPoints[-1],
        'game': lambda x: len(x.player.totalPoints),
        'average': lambda x: x.player.averagePoints
    }.get(sortedBy, lambda x: 0)

    sorted_users = sorted(users, key=sort_key, reverse=True)
    if order:
        sorted_users.reverse()
    return sorted_users


def build_users_dict(sorted_users, current_user, order):
    users_dict = {}
    rank = len(sorted_users) - 1 if order else 1
    index = 0

    for user in sorted_users:
        if user.id == 0:
            continue

        player_dict = build_player_dict(user)
        users_dict[index] = build_user_dict(user, player_dict, current_user, rank)

        index += 1
        rank = rank - 1 if order else rank + 1

    return users_dict


def build_player_dict(user):
    return {
        'currentGameID': user.player.currentGameID,
        'isReady': user.player.isReady,
        'soloPoints': user.player.soloPoints,
        'deathPoints': user.player.deathPoints,
        'tournamentPoints': user.player.tournamentPoints,
        'totalPoints': user.player.totalPoints,
        'averagePoints': user.player.averagePoints,
        'gamePlayed': user.player.score_set.count(),
    }


def build_user_dict(user, player_dict, current_user, rank):
    return {
        'id': user.id,
        'username': user.username,
        'photo_url': user.photo.url,
        'status': user.status,
        'followed': user.id in current_user.follows,
        'blocked': user.id in current_user.blockedUsers,
        'player': player_dict,
        'rank': rank,
    }

# --------------------------------------------------------------------------------
# ---------------------------------- Set Games -----------------------------------
# --------------------------------------------------------------------------------


def	quit_game(request):
	if not request.user.is_authenticated:
		return JsonResponse({
			'success': False
		}, status=401)

	player = request.user.player

	if (player.currentGameID != None):
		try:
			game = Game.objects.get(id=player.currentGameID)
		except Game.DoesNotExist:
			return JsonResponse({
				'success': False,
				'message': "Game does not exist"
			}, status=401)
		if (game.gameMode in ['init_tournament_game', 'init_ranked_solo_game', 'init_death_game'] and player.isReady == True):
			return JsonResponse({
				'success': False,
				'message': "You cannot quit this game"
			}, status=401)
		game.playerList.remove(player.id)
		if (len(game.playerList) == 0):
			game.isOver = True
		game.save()
	else:
		return JsonResponse({
			'success': False,
			'message': "User is not in a game"
		}, status=401)

	if (game.gameMode in ['init_tournament_game', 'init_ranked_solo_game', 'init_death_game']):
		player.allGames.pop()
	player.currentGameID = None
	player.isReady = False
	player.save()


	if (game.isPrivate):
		# Remove the player from the channel player list
		try:
			channel = Channel.objects.get(room_id=game.room_id)
			channel.player_list.remove(player.id)
			channel.save()
		except Channel.DoesNotExist:
			return JsonResponse({
				'success': False,
				'message': "Channel does not exist"
			}, status=401)
		return JsonResponse({
			'success': True,
			'message': "send-quit",
			'room_id': game.room_id
		}, status=200)

	return JsonResponse({
		'success': True
	}, status=200)


### Join Tournament

def join_tournament(request):
    if not is_authenticated(request):
        return user_not_authenticated_response()

    if not is_in_game(request.user):
        return user_not_in_game_response()

    game = get_user_game(request.user)
    if not game:
        return game_not_found_response()

    if not is_tournament_game(game):
        return not_a_tournament_response()

    response = try_join_existing_channel(game, request.user)
    if response:
        return response

    return create_new_tournament_channel(request.user)


def is_authenticated(request):
    return request.user.is_authenticated


def is_in_game(user):
    return user.player.currentGameID is not None


def get_user_game(user):
    try:
        return Game.objects.get(id=user.player.currentGameID)
    except Game.DoesNotExist:
        return None


def is_tournament_game(game):
    return game.gameMode == "init_tournament_game"


def try_join_existing_channel(game, user):
    channels = Channel.objects.filter(tournament=True, isFull=False)

    for channel in channels:
        if user in channel.users.all():
            return JsonResponse({
                'success': False,
                'message': "User already in tournament"
            }, status=401)

        if channel.users.count() < 4:
            add_user_to_channel(channel, user)
            update_game_full_status(game, channel)
            return user_joined_tournament_response(channel)

    return None


def add_user_to_channel(channel, user):
    channel.users.add(user)
    channel.save()
    user.player.currentRoomID = channel.room_id
    user.player.save()


def update_game_full_status(game, channel):
    if channel.users.count() == 4:
        game.isFull = True
        game.save()


def create_new_tournament_channel(user):
    room_id = str(uuid.uuid4())
    channel = Channel.objects.create(
        tournament=True,
        room_id=room_id,
        name='Tournament ' + datetime.now().strftime("%d-%m %H:%M")
    )
    add_user_to_channel(channel, user)

    return JsonResponse({
        'success': True,
        'message': "Created tournament",
        'room_id': room_id
    }, status=200)


def user_not_authenticated_response():
    return JsonResponse({
        'success': False,
        'message': "The user is not authenticated"
    }, status=401)


def user_not_in_game_response():
    return JsonResponse({
        'success': False,
        'message': "User is not in a game"
    }, status=401)


def game_not_found_response():
    return JsonResponse({
        'success': False,
        'message': "Game does not exist"
    }, status=401)


def not_a_tournament_response():
    return JsonResponse({
        'success': False,
        'message': "Game is not a tournament"
    }, status=401)


def user_joined_tournament_response(channel):
    return JsonResponse({
        'success': True,
        'message': "User joined the tournament",
        'room_id': channel.room_id
    }, status=200)


def create_finals_game(game, player, isFinal):
    gameMode = f"{game.gameMode}_{'final_game' if isFinal else 'third_place_game'}"

    newGame = Game.objects.create(
        duration=0,
        gameMode=gameMode,
        playerList=[player.id],
        parentGame=game.id,
    )

    if isFinal:
        game.finalGame = newGame.id
    else:
        game.thirdPlaceGame = newGame.id

    game.save()
    return newGame


def create_finals_game(game, player, isFinal):
	if (isFinal):
		gameMode = game.gameMode + "_final_game"
	else:
		gameMode = game.gameMode + "_third_place_game"

	newGame = Game.objects.create(
		duration=0,
		gameMode=gameMode,
		playerList=[player.id],
		parentGame=game.id,
	)
	newGame.save()

	if (isFinal):
		game.finalGame = newGame.id
	else:
		game.thirdPlaceGame = newGame.id
	game.save()
	return (newGame)


def redirect_to_finals_game(subGame, player):
    with transaction.atomic():
        try:
            game = Game.objects.select_for_update().get(id=subGame.parentGame)
            scores = subGame.scores.filter(player__id=player.id).first()
            if scores is None:
                raise ValueError("Score not found for player")

            score = scores.score
            position = scores.position

            User = get_user_model()
            user = User.objects.get(player=player)
        except (Game.DoesNotExist, User.DoesNotExist, ValueError) as e:
            return JsonResponse({'success': False}, status=401)

        message = None
        finalGame = None

        if position == 1:
            finalGame = game.finalGame
            if not finalGame:
                finalGame = create_finals_game(game, player, True)
                message = f"{user.username}: Get ready for the final game"
            else:
                finalGame = Game.objects.get(id=finalGame)
        elif position == 2:
            finalGame = game.thirdPlaceGame
            if not finalGame:
                finalGame = create_finals_game(game, player, False)
                message = f"{user.username}: Get ready for the third place game"
            else:
                finalGame = Game.objects.get(id=finalGame)

        finalGame.playerList.append(player.id)
        finalGame.save()

        player.currentGameID = finalGame.id
        player.isReady = False
        player.save()

    # Get the tournament channel with the player list
    try:
        channel = Channel.objects.filter(tournament=True, users__id=user.id).latest('id')
    except Channel.DoesNotExist:
        channel = None

    return JsonResponse(
        {
            'success': True,
            'redirectGameMode': finalGame.gameMode,
            'score': score,
            'position': position,
            'game_mode': game.gameMode,
            'room_id': channel.room_id if channel else None,
            'message': message
        },
        status=200
    )
