from django.shortcuts import render

def pong(request):
	return render(request, 'base.html') if request.method == 'GET' else None

def ranked(request):
	return render(request, 'base.html') if request.method == 'GET' else None

def practice(request):
	return render(request, 'base.html') if request.method == 'GET' else None

def game(request, gameMode):
	return render(request, 'base.html') if request.method == 'GET' else None

def gameOver(request, gameID):
	return render(request, 'base.html') if request.method == 'GET' else None
