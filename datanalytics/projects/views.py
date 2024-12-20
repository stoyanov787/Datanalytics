from django.shortcuts import render
from django.http import HttpResponse
from .forms import ParamForm

def param(request):
    print(request.user)
    if request.user.is_authenticated:
        context = {}
        context['form'] = ParamForm(request=request)
        return render(request, 'param.html', context)
    else:
        return HttpResponse("You are not logged in")

