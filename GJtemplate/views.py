
from pathlib import Path
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render 
@require_http_methods(["GET"])
def home(request):
    """Serve the single-page app template."""
    return render(request, "tracker_app/home.html")