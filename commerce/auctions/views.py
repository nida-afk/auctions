from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment


def index(request):
    al = Listing.objects.all().filter(active= True)
    return render(request, 'auctions/index.html', {'al': al})

def all(request):
    al = Listing.objects.all()
    return render(request, 'auctions/all.html', {'al': al})




def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == 'GET':
        return render(request, 'auctions/create_listing.html')
    elif request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        sbid = request.POST['sbid']
        image_url = request.POST.get('image_url', '')
        category = request.POST.get('category', '')

        nl = Listing(title=title, description=description, sbid=sbid, image_url=image_url, category=category, user = request.user)
        nl.save()

        return HttpResponseRedirect(reverse('index'))



# Listing Page

def listing_page(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    cp = listing.sbid
    high = Bid.objects.filter(listing=listing).order_by('-amount').first()

    if high:
        cp = high.amount

    if request.user.is_authenticated:
        user = request.user
        w = listing.watchlist.filter(id=user.id).exists()

        if request.method == "POST" and "watchlist_action" in request.POST:
            if w:
                user.watchlist.remove(listing)
            else:
                user.watchlist.add(listing)
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))

        if request.method == "POST" and "ba" in request.POST:
            ba = request.POST.get("ba")
            if ba:
                if float(ba) >= float(listing.sbid) and (not high or float(ba) > high.amount):
                    new_bid = Bid(listing=listing, user=user, amount=ba)
                    new_bid.save()

                    return HttpResponseRedirect(reverse("listing", args=[listing_id]))
                else:
                    return render(request, "auctions/listing.html", {"listing": listing, "message": "Invalid bid amount."})

        if user == listing.user:
            if request.method == "POST" and "close" in request.POST:
                high = Bid.objects.filter(listing=listing).order_by('-amount').first()
                if high:
                    listing.winner = high.user
                    listing.active = False

                    listing.save()
                return HttpResponseRedirect(reverse("listing", args=[listing_id]))

        if listing.winner == user:
            won = True
        else:
            won = False

        if request.method == "POST" and "add" in request.POST:
            ct = request.POST.get("comment_text", "")
            if ct:
                nt = Comment(listing=listing, user=user, text=ct)
                nt.save()
                return HttpResponseRedirect(reverse("listing", args=[listing_id]))

    else:
        w = False
        won = False

    com = Comment.objects.filter(listing=listing)
    listing.sbid= cp
    listing.save()

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "cp": cp,
        "in_watchlist": w,
        "won_auction": won,
        "comments": com
    })


def watchlist(request):
    user = request.user
    wi = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {"wi": wi})

def categories(request):
    categories = Listing.objects.values_list('category', flat=True).distinct()
    return render(request, "auctions/categories.html", {"categories": categories})

def category(request, category_name):
    listings = Listing.objects.filter(category=category_name, active = True)
    return render(request, "auctions/category.html", {"listings": listings})
