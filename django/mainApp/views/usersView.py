import imghdr
from io import BytesIO
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import redirect
from django.core.files.base import ContentFile
from django.core.files import File
from django.contrib.auth import login, get_user_model
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.middleware.csrf import get_token
from datetime import datetime
import urllib.request, json, base64, uuid

import requests
import os
import re

from mainApp.utils import containBadwords
from mainApp.models import Player
from ..models import CustomUser, Channel


# 42 API
HOST = os.environ.get('HOST')
API_USER = 'https://api.intra.42.fr/v2/me'
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

# Views
@ensure_csrf_cookie
def sign_in(request):
    if request.method == 'GET':
        get_token(request)
        return render(request, 'base.html')

    elif request.method == 'POST':
        email, password = get_credentials(request)
        user = authenticate_user(email, password)

        if user == 'emailError':
            return invalid_email_response()
        elif user == 'passwordError':
            return invalid_password_response()
        else:
            login(request, user)
            user.set_status("online")
            send_login_email(request, user)
            return successful_login_response()

def get_credentials(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')
    return email, password

def authenticate_user(email, password):
    return authenticate_custom_user(email=email, password=password)

def invalid_email_response():
    response = {"success": False, "email": "Invalid email"}
    return JsonResponse(response, status=401)

def invalid_password_response():
    response = {"success": False, "password": "Invalid password"}
    return JsonResponse(response, status=401)

def successful_login_response():
    response = {"success": True, "message": "Successful login"}
    return JsonResponse(response, status=200)

def send_login_email(request, user):
    if user.emailAlerts:
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        message = f"""
        <p>Hello <b>{user.username}</b>,</p>

        <h3>Information:</h3>
        <p>
        - <b>Date</b>: {date}<br>
        - <b>Time</b>: {time}<br>
        - <b>IP address</b>: {request.META.get('REMOTE_ADDR')}
        </p>
        """

        send_mail(
            'New connection to your account',
            message,
            'Transcendence',
            [user.email],
            html_message=message,
            fail_silently=True,
        )


### sign_up
@ensure_csrf_cookie
def sign_up(request):
    if request.method == 'GET':
        get_token(request)
        return render(request, 'base.html')

    elif request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not validate_email_signup(email):
            return JsonResponse({"success": False, "message": "Invalid email format"}, status=401)

        if not validate_username(username):
            return JsonResponse({"success": False, "message": "Invalid username"}, status=401)

        user = create_user(username, email, password)
        login_user(request, user)
        join_general_channel(user)
        send_welcome_email(user)

        return JsonResponse({"success": True, "message": "Successful sign up"}, status=200)

def validate_email_signup(email):
    try:
        validate_email(email)
    except ValidationError:
        return False

    if CustomUser.objects.filter(email=email).exists():
        return False

    return True

def validate_username(username):
    if CustomUser.objects.filter(username=username).exists():
        return False
    elif not re.match('^[a-zA-Z0-9-]*$', username):
        return False
    elif len(username) < 4:
        return False
    elif len(username) > 20:
        return False
    elif containBadwords(username):
        return False

    return True

def create_user(username, email, password):
    user = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    user.save()
    return user

def login_user(request, user):
    login(request, user)
    user.set_status("online")

def join_general_channel(user):
    try:
        channel = Channel.objects.get(room_id="general")
        channel.users.add(user)
    except Exception:
        channel = Channel.objects.create(name="General", room_id="general")
        channel.users.set([user])
        channel.save()

def send_welcome_email(user):
    if user.emailAlerts:
        message = f"""
        <p>Hello <b>{user.username}</b>,</p>
        """
        send_mail(
            'Welcome to transcendence',
            message,
            'Transcendence',
            [user.email],
            html_message=message,
            fail_silently=True,
        )


### reset password
@ensure_csrf_cookie
def reset_password(request):
    if request.method == 'GET':
        return render(request, 'base.html')

    if request.method == 'POST':
        email = get_email_from_request(request)
        if not is_valid_email(email):
            return JsonResponse({"success": False, "email": "Invalid email format"}, status=401)

        if not user_exists(email):
            return JsonResponse({"success": True, "message": "Successful email sent"}, status=200)

        user = CustomUser.objects.get(email=email)
        if user.is42:
            return JsonResponse({"success": False, "message": "This email is associated with a 42 account"}, status=401)

        reset_password_id = generate_reset_password_id()
        update_user_reset_password_id(user, reset_password_id)

        if user.emailAlerts:
            send_reset_password_email(user, reset_password_id)

        return JsonResponse({"success": True, "message": "Successful email sent"}, status=200)

def get_email_from_request(request):
    data = json.loads(request.body)
    return data.get('email')

def is_valid_email(email):
    if not email:
        return False
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def user_exists(email):
    return CustomUser.objects.filter(email=email).exists()

def generate_reset_password_id():
    return str(uuid.uuid4())

def update_user_reset_password_id(user, reset_password_id):
    user.resetPasswordID = reset_password_id
    user.save()

def send_reset_password_email(user, reset_password_id):
    message = f"""
    <p>Hello <b>{user.username}</b>,</p>

    <p>
    <a href="https://{HOST}:8443/reset_password_id/{reset_password_id}">Reset your password</a>
    </p>
    """

    send_mail(
        'Reset your password',
        message,
        'Transcendence',
        [user.email],
        html_message=message,
        fail_silently=True,
    )



### reset_password_id
@ensure_csrf_cookie
def reset_password_id(request, reset_password_id):
    if request.method == 'GET':
        return render(request, 'base.html')

    if request.method == 'POST':
        data = json.loads(request.body)
        new_password = data.get('password')

        if not new_password:
            return JsonResponse({"success": False, "message": "Password cannot be empty"}, status=400)
        try:
            user = CustomUser.objects.get(reset_password_id=reset_password_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid reset password ID"}, status=401)

        user.reset_password_id = ''
        user.set_password(new_password)
        user.save()
        send_password_reset_email(user, request)
        return JsonResponse({"success": True, "message": "Successful password reset"}, status=200)

def send_password_reset_email(user, request):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    message = f"""
    <p>Hello <b>{user.username}</b>,</p>
    <h3>Information:</h3>
    <p>
    - <b>Date</b>: {date}<br>
    - <b>Time</b>: {time}<br>
    - <b>IP address</b>: {request.META.get('REMOTE_ADDR')}
    </p>
    """

    send_mail(
        'Successful password reset',
        message,
        'Transcendence',
        [user.email],
        html_message=message,
        fail_silently=True,
    )


### profile
@ensure_csrf_cookie
def profile(request, username):
    if request.method == 'GET':
        return render(request, 'base.html')

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "The user is not authenticated"}, status=401)
        elif (request.user.username != username):
            return JsonResponse({"success": False, "message": "You are not allowed to modify this profile"}, status=401)

        # Get the data
        data = json.loads(request.body)
        new_username = data.get('new_username')
        new_description = data.get('new_description')
        photo = data.get('photo')
        new_email = data.get('new_email')
        new_password = data.get('new_password')
        emailAlerts = data.get('emailAlerts')

        # Validate the email alerts
        if emailAlerts is not None:
            if emailAlerts not in [True, False]:
                return JsonResponse({"success": False, "message": "Invalid email alerts value"}, status=401)
            else:
                request.user.emailAlerts = emailAlerts
                request.user.save()

        # Check if the username is valid
        check_username_valid(new_username, request)

        # Check if the description is valid
        check_description_valid(new_description, request)

        # Check if the photo is valid
        if photo:
            # Delete the old photo
            if request.user.photo and request.user.photo.path != 'static/users/img/default.png':
                default_storage.delete(request.user.photo.path)

            # Decode the Base64 photo
            try:
                photo_data = base64.b64decode(photo)
                photo_image = Image.open(BytesIO(photo_data))
            except Exception as e:
                return JsonResponse({"success": False, "message": "Invalid image file"}, status=401)

            # Determine the image file type
            image_type = imghdr.what(None, photo_data)
            if image_type is None:
                return JsonResponse({"success": False, "message": "Invalid image file"}, status=401)

            # Save the new photo
            photo_temp = BytesIO()
            photo_image.save(photo_temp, format=image_type.upper())
            photo_temp.seek(0)
            request.user.photo.save(f"{request.user.email}.{image_type}", File(photo_temp), save=True)
            request.user.save()

        # Check if the email is valid
        try:
            old_email = request.user.email
            if new_email == request.user.email:
                pass
            elif not new_email:
                return JsonResponse({"success": False, "email": "This email is empty"}, status=401)
            elif not len(new_email):
                return JsonResponse({"success": False, "email": "This email is empty"}, status=401)
            elif not validate_email(new_email):
                return JsonResponse({"success": False, "email": "Invalid email format"}, status=401)
            elif CustomUser.objects.filter(email=new_email).exists():
                return JsonResponse({"success": False, "email": "This email is already taken"}, status=401)
            else:
                # Change the status to offline
                request.user.set_status("offline")

                request.user.email = new_email
                request.user.save()

        except ValidationError:
                return JsonResponse({"success": False, "email": "Invalid email format"}, status=401)

        # Check if the password is valid
        check_password_valid(new_password, request)

        # Send an email to the user
        send_email_to_user(new_email, old_email, request, new_password)

        return JsonResponse({"success": True, "message": "Successful profile update"}, status=200)
    else:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

def is_authenticated(request, username):
    """
    Checks if the user is authenticated and if the username matches the requested username.
    """
    if not request.user.is_authenticated:
        return False
    if request.user.username != username:
        return False
    return True


def validate_email_alerts(user, email_alerts):
    if email_alerts is None:
        return True

    if email_alerts not in [True, False]:
        return False

    user.email_alerts = email_alerts
    user.save()
    return True

def handle_photo_upload(user, photo):
    if user.photo and user.photo.path != 'static/users/img/default.jpg':
        default_storage.delete(user.photo.path)

    try:
        photo_data = base64.b64decode(photo)
        photo_image = Image.open(BytesIO(photo_data))
    except Exception:
        return False

    image_type = imghdr.what(None, photo_data)
    if image_type is None:
        return False

    photo_temp = BytesIO()
    photo_image.save(photo_temp, format=image_type.upper())
    photo_temp.seek(0)
    user.photo.save(f"{user.email}.{image_type}", File(photo_temp), save=True)
    user.save()
    return True

def handle_email_change(user, new_email):
    if new_email == user.email or not new_email or not len(new_email):
        return True

    if not validate_email(new_email):
        return False

    if CustomUser.objects.filter(email=new_email).exists():
        return False

    user.set_status("offline")
    user.email = new_email
    user.save()
    return True


def	check_description_valid(new_description, request):
	if new_description:
		if len(new_description) > 150:
			return JsonResponse({"success": False, "description": "Description too long (150 characters max)"}, status=401)
		elif containBadwords(new_description):
			return JsonResponse({"success": False, "description": "This description contains inappropriate words"}, status=401)
		else:
			request.user.description = new_description
			request.user.save()
	else:
		request.user.description = ''
		request.user.save()


def check_username_valid(new_username, request):
    if new_username == request.user.username:
        pass
    else:
        if len(new_username) < 4:
            response = {"success": False, "username": "This username is too short (4 characters minimum)"}
        elif len(new_username) > 20:
            response = {"success": False, "username": "This username is too long (20 characters maximum)"}
        elif containBadwords(new_username):
            response = {"success": False, "username": "This username contains inappropriate words"}
        elif ' ' in new_username:
            response = {"success": False, "username": "This username cannot contain space"}
        elif not re.match('^[a-zA-Z0-9-]*$', new_username):
            response = {"success": False, "username": "This username cannot contain special characters"}
        elif CustomUser.objects.filter(username=new_username).exists():
            response = {"success": False, "username": "This username is already taken"}
        else:
            request.user.username = new_username
            request.user.save()
            return

        return JsonResponse(response, status=401)



def	check_password_valid(new_password, request):
	if not new_password:
		pass
	if not len(new_password):
		pass
	else:
		# Change the status to offline
		request.user.set_status("offline")

		request.user.set_password(new_password)
		request.user.save()


def send_email_to_user(new_email, old_email, request, new_password):
	if new_email != request.user.email or new_password:
		now = datetime.now()
		date = now.strftime("%Y-%m-%d")
		time = now.strftime("%H:%M:%S")

		message = f"""
		<p>Hello <b>{request.user.username}</b>,</p>
		"""

		if old_email != request.user.email:
			message += f"""
			<p>Your email has been successfully changed from <b>{old_email}</b> to <b>{new_email}</b>.</p>
			"""
		if new_password:
			message += f"""
			<p>Your password has been successfully changed.</p>
			"""

		message += f"""
		<p>If you received this email by mistake, please ignore it.</p>

		<h3>Information:</h3>
		<p>
		- <b>Date</b>: {date}<br>
		- <b>Time</b>: {time}<br>
		- <b>IP address</b>: {request.META.get('REMOTE_ADDR')}
		</p>
		"""

		send_mail(
			'Successful profile update',
			message,
			'Transcendence',
			[old_email, request.user.email] if old_email != request.user.email else [request.user.email],
			html_message=message,
			fail_silently=True,
		)


### check_authorize
def	check_authorize(request):
	if request.method == 'GET' and 'code' in request.GET:
		code = request.GET['code']
	else :
		return redirect('auth42')

	response_token = handle_42_callback(request, code)
	if response_token is None:
		return redirect('token42')

	response_data = make_api_request_with_token(API_USER, response_token)
	if response_data is None:
		return redirect('down42')

	return connect_42_user(request, response_data)



### connect_42_user
def connect_42_user(request, response_data):
    user, error_message = authenticate_42_user(response_data)

    if error_message:
        return redirect('error_page', error_message=error_message)

    if user and not user.is42:
        return redirect('used42')

    if user:
        user.set_status("online")
        login(request, user)
        send_login_email(request, user)

    else:
        user = create_new_42_user(response_data)
        login(request, user)
        join_general_channel(user)
        send_welcome_email(user)

    return redirect('pong')


def authenticate_42_user(response_data):
	User = get_user_model()

	email = response_data.get('email')
	username = response_data.get('login')

	if not email or not username:
		return None, "Invalid response data"

	user = get_user_by_email(email, User)

	if user:
		if not check_password(user, username):
			return None, "Invalid credentials"
		return user, None
	return None, None


def create_new_42_user(response_data):
    email = response_data['email']
    username = response_data['login']
    photo_url = response_data['image']['link']
    is_official = email in os.environ.get('OFFICIAL_EMAILS', '').split(',')

    player = Player.objects.create(currentGameID=None)
    user = CustomUser.objects.create(
        username=username,
        email=email,
        player=player,
        is42=True,
        isOfficial=is_official,
    )
    user.photo.save(f"{email}.jpg", get_photo_file(photo_url))
    user.save()

    return user

def get_photo_file(photo_url):
    with urllib.request.urlopen(photo_url) as url:
        with Image.open(BytesIO(url.read())) as img:
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            return ContentFile(img_io.getvalue())

def join_general_channel(user):
    try:
        channel = Channel.objects.get(room_id="general")
        channel.users.add(user)
    except Channel.DoesNotExist:
        channel = Channel.objects.create(name="General", room_id="general")
        channel.users.set([user])
        channel.save()

def send_login_email(request, user):
    if user.emailAlerts:
        send_email(
            user.email,
            'New connection to your account',
            get_login_email_body(request, user),
        )

def send_welcome_email(user):
    if user.emailAlerts:
        send_email(
            user.email,
            'Welcome to Transcendence',
            get_welcome_email_body(user),
        )

def get_login_email_body(request, user):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    return f"""
    <p>Hello <b>{user.username}</b>,</p>

    <h3>Information:</h3>
    <p>
    - <b>Date</b>: {date}<br>
    - <b>Time</b>: {time}<br>
    - <b>IP address</b>: {request.META.get('REMOTE_ADDR')}
    </p>
    """

def get_welcome_email_body(user):
    return f"""
    <p>Hello <b>{user.username}</b>,</p>
    """

def get_user_by_email(email, User):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None

def check_password(user, password):
    return user.username == password

def send_email(recipient, subject, body):
    send_mail(
        subject,
        body,
        'Transcendence',
        [recipient],
        html_message=body,
        fail_silently=True,
    )


def make_api_request_with_token(api_url, token):
	headers = {
		'Authorization': f'Bearer {token}',
	}
	try:
		response = requests.get(api_url, headers=headers)
		return response.json() if response.content == 200 else None
	except requests.RequestException as e:
		return None


def handle_42_callback(request, code):
    port = '8443' if request.scheme == 'https' else '8000'
    host = request.get_host().split(':')[0]
    redirect_uri = f"{request.scheme}://{host}:{port}/check_authorize/"
    token_url = "https://api.intra.42.fr/oauth/token"
    token_params = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri
    }

    response = requests.post(token_url, data=token_params)

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        return None


def authenticate_custom_user(email, password):
	User = get_user_model()
	try:
		user = User.objects.get(email=email)
		return user if user.check_password(password) else 'passwordError'
	except User.DoesNotExist:
		return 'emailError'


def notifications(request):
	if request.method == 'GET':
		return render(request, 'base.html')

def friends(request):
	if request.method == 'GET':
		return render(request, 'base.html')


