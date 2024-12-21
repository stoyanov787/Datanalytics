from django.shortcuts import render
from django.http import HttpResponse
from .forms import ParamForm

def param(request):
    if request.user.is_authenticated:
        context = {}
        context['form'] = ParamForm(request=request)
        return render(request, 'param.html', context)
    else:
        return HttpResponse("You are not logged in")
    
def observation_date_column_choice(request):
    form = ParamForm(request=request)
    return HttpResponse(form["t1df"])


