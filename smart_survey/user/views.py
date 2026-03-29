from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm
from surveys.views import home
from django_ratelimit.decorators import ratelimit
from .utils.ratelimit import user_or_ip
@ratelimit(key=user_or_ip, rate="50/m", block=True)
def registration(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(home)

    else:
        form = UserRegisterForm()

    return render(request, 'account/registration.html', {'form': form})