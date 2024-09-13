import json
from django.contrib.auth import get_user_model

def containBadwords(message):
	language_list = ['fr', 'en']
	badwords = []

	# Load badwords from files
	for language in language_list:
		with open(f'/home/app/web/staticfiles/badwords/{language}.json', 'r') as file:
			data = json.load(file)
			badwords.extend(data['words'])

	# List of some bad word first names
	badwordsNames = [
		"hitler",
		"mussolini",
		"staline",
		"adolph",
		"pétain",
		"kimjongun",
		"poutine",
		"benladen",
		"zemmour",
		"alqaeda",
		"daesh"
	]

	message = message.lower()

	for word in badwordsNames:
		if message.find(word.lower()) != -1:
			return True

	for word in badwords:
		if message.find(word.lower()) != -1:
			return True

	return False


def set_all_users_offline():
	try:
		User = get_user_model()
		for user in User.objects.all():
			user.set_status("offline")
	except:
		pass
