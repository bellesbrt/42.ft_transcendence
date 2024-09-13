from django.shortcuts import render

def ranking(request, sortedBy):
	return render(request, 'base.html') if request.method == 'GET' else None
