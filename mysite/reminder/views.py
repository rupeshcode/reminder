from django.shortcuts import render
import datetime, time
#from django.template import RequestContext
from django.contrib.auth import authenticate, login
from threading import Timer
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from reminder.forms import ReminderForm, UserForm, UserProfileForm
from reminder.models import Reminder
from reminder.tasks import send_sms_reminder
# Create your views here.

def homepage(request):
    return render(request,'reminder/home.html',)

def register(request):
    # Like before, get the request's context.
    #context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            #if 'picture' in request.FILES:
            #    profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print (user_form.errors, profile_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
            'reminder/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def user_login(request):
    # Like before, obtain the context for the user's request.
    #context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/reminder')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Reminder App account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request,'reminder/login.html', {})
def reminder_home(request):
    if request.user.is_authenticated():
        if request.method =='POST':

            form = ReminderForm(request.POST)

            if form.is_valid():

                name = request.POST.get('name', '')
                time = request.POST.get('time', '')
                message = request.POST.get('message', '')
                phone_number = request.POST.get('phone_number', '')
                user_obj = Reminder(name=name, time=time, phone_number=phone_number, message=message)
                user_obj.save()
                #sec = (time - datetime.datetime.now()).total_seconds()
                #print(sec)
                # Schedule the Celery task
                send_sms_reminder(time)

                return render(request, 'reminder/reminder.html', {'user_obj': user_obj,'is_registered':True })
        else:
            form = ReminderForm()  # an unboundform

            return render(request, 'reminder/reminder.html', {'form': form})
    else:
        return HttpResponse("You are not logged in.")
