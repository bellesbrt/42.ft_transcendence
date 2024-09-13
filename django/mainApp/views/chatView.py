from django.shortcuts import render
from django.http import JsonResponse
from mainApp.utils import containBadwords
from mainApp.models import Channel

import uuid, json

MAX_NAME_LENGTH = 30
MAX_DESCRIPTION_LENGTH = 150

def chat(request):
	if request.method == 'GET':
		return render(request, 'base.html')

def room(request, room_id):
	if request.method == 'GET':
		# Update user status
		if request.user.is_authenticated:
			request.user.set_status('chat:' + room_id)

		return render(request, 'base.html')

def new(request):
    if request.method == 'GET':
        return render(request, 'base.html')

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'The user is not authenticated'}, status=401)

        name, description = get_form_data(request.body)
        if not validate_name(name):
            return JsonResponse({'success': False, 'name': 'The name is invalid'}, status=401)
        if not validate_description(description):
            return JsonResponse({'success': False, 'description': 'The description is invalid'}, status=401)

        room_id = create_chat_group(request.user, name, description)
        return JsonResponse({'success': True, 'message': 'The chat group is created', 'room_id': room_id}, status=200)

def get_form_data(request_body):
    data = json.loads(request_body)
    return data.get('name', ''), data.get('description', '')

def validate_name(name):
    return bool(name and len(name) <= MAX_NAME_LENGTH and not name.isspace() and not containBadwords(name))

def validate_description(description):
    return len(description) <= MAX_DESCRIPTION_LENGTH and not containBadwords(description)

def create_chat_group(user, name, description):
    room_id = str(uuid.uuid4())
    users = [user.id]

    channel = Channel.objects.create(private=False, room_id=room_id, name=name, description=description)
    channel.users.set(users)
    channel.creator = user.id
    channel.save()

    return room_id

