from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
import os
import random

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shop.forms import ReviewForm, SignupForm, SigninForm
from shop.models import Cart, Product, Category, Cart, CartItem, Order, OrderItem, Review
from shop.serializer import ProductSerializer

from recommendation.recommendation import clustering, get_popular_products, collborative_filtering

import pandas as pd

def get_from_clustering(description):
    all_products = Product.objects.all().order_by('-rating').values()
    all_products_dataframe = pd.DataFrame(list(all_products))

    similar_products = clustering(description, all_products_dataframe)

    return similar_products



def get_from_category(category):
    products_of_same_category = Product.objects.filter(category=category).order_by('-rating')[:4].values()
    return products_of_same_category

def get_from_past_purchases(user):
    all_ratings = Review.objects.all().values('rate', 'user', 'product')
    past_purchases = Review.objects.filter(user=user).order_by('-created')[:5]
    all_recommendations = []

    all_ratings_df = pd.DataFrame(list(all_ratings))
    print(all_ratings_df.head())

    for past_purchase in past_purchases:
        recommendation = collborative_filtering(all_ratings_df, past_purchase.product.id)
        all_recommendations = all_recommendations  + recommendation 
    
    return all_recommendations





def home(request):
   # if request.META['HTTP_HOST'] != "ecommerce.hem.xyz.np":
    #     return redirect("http://ecommerce.hem.xyz.np")
    # base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    

    # df = pd.read_csv(base_dir + '/shop/cleaned_product_data.csv')

    # categories = df['Product Category']
    
    # for row in categories.unique():
    #     Category.objects.create(name = row)

    # for index, row in df.iterrows():
    #     category = Category.objects.get(name = row['Product Category'])
    #     Product.objects.create(
    #         name = row['Product Name'],
    #         image = row['Product Image Url'],
    #         description = row['Product Description'],
    #         price = row['Product Price'],
    #         category = category,
    #         rating = row['Product Rating']
    #     )

    # user_df = pd.read_csv(base_dir + '/recommendation/users.csv')


    # for index, row in user_df.iterrows():
    #     user, created = User.objects.get_or_create(
    #         username = row['username'],
    #         email = row['email'],
    #         password  = row['password']
    #     )

    #     product_count = Product.objects.all().count()

    #     random_list = [random.randint(0,product_count-1) for i in range(3)]

    #     for i in random_list:
    #         product = Product.objects.get(id=str(i))
    #         rating = random.randint(0, 10)
    #         review = Review.objects.create(
    #             product = product,
    #             user = user,
    #             rate = rating,
    #             review = ''
    #         ) 


    # products = Product.objects.filter(active=True)

    # for product in products:
    #     reviews = Review.objects.filter(product = product)

    #     total_rating = 0
    #     total_rater = 0
    #     for review in reviews:
    #         total_rating +=  review.rate
    #         total_rater += 1
        
    #     if total_rater != 0:
    #         rating = total_rating / total_rater

    #         Product.objects.filter(id=product.id).update(rating=rating)


    products = Product.objects.filter(active=True)
    categories = Category.objects.filter(active=True)

    product_paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page = product_paginator.get_page(page_number)

    context = {"products": page, "categories": categories}
    return render(request, "shop/home.html", context)


def search(request):
    q = request.GET["q"]
    products = Product.objects.filter(active=True, name__icontains=q)
    categories = Category.objects.filter(active=True)
    context = {"products": products,
               "categories": categories,
               "title": q + " - search"}
    return render(request, "shop/list.html", context)


def categories(request, slug):
    cat = Category.objects.get(slug=slug)
    products = Product.objects.filter(active=True, category=cat)
    categories = Category.objects.filter(active=True)

    product_paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page = product_paginator.get_page(page_number)

    context = {"products":page, "categories":categories, "title":cat.name + " - Categories"}
    return render(request, "shop/list.html", context)

def recommended_for_you(request):
    recommened = get_from_past_purchases(request.user)

    products = []

    for i in recommened:
        product = Product.objects.get(id=str(i))
        print(product.name)
        products.append(product)

    context = {"product" : products,
                "recommended": True,
               "title": 'Recommended for you'}
    return render(request, 'shop/list.html', context)


def detail(request, slug):
    product = Product.objects.get(active=True, slug=slug)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            
            product = review.product
            reviews = Review.objects.filter(product = product).count()

            product_rating = product.rating
            rating = (product_rating * reviews) + (review.rate)
            rating = rating / (reviews + 1)

            review.save()
            Product.objects.filter(id = review.product.id).update(rating = rating)
          
            messages.success(request, "Review saved")
            return redirect('/'+ slug)
        else:
            messages.error(request, "Invalid form")
    else:
        form = ReviewForm()

    # product recommendation
    most_popular = get_from_category(product.category)
    similar_products = get_from_clustering(product.description)

    

    similar_products_list = []

    for i in similar_products:
        product = Product.objects.get(id=i)
        similar_products_list.append(product)

    categories = Category.objects.filter(active=True)

    reviews = Review.objects.filter(product=product)[:5]
    context = {"product" : product,
               "categories":categories,
               "most_popular": most_popular,
               "reviews": reviews,
               "similar_products": similar_products_list,
               "form": form}
    return render(request, "shop/detail.html", context)


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, "User saved")
            return redirect("shop:signin")
        else:
            messages.error(request, "Error in form")
    else:
        form = SignupForm()
    context = {"form": form}
    return render(request, "shop/signup.html", context)


def signin(request):
    if request.method=="POST":
        form = SigninForm(request.POST)
        # username = req.POST["username"]
        # password = req.POST["password"]
        username = form["username"].value()
        password = form["password"].value()
        user = authenticate(request, username=username,  password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Successfully logged in")
            return redirect("shop:home")
        else:
            messages.error(request, "Invalid Username or Password")
    else:
        form = SigninForm()
    context = {"form": form}
    return render(request, "shop/signin.html", context)


def signout(request):
    logout(request)
    return redirect("shop:signin")


def cart(request, slug):
 
    if request.user.is_authenticated:
        product = Product.objects.get(slug=slug)
        obj, created = Cart.objects.get_or_create(user = request.user)
        cartItemObj, cartItemCreated = CartItem.objects.get_or_create(product=product, cart=obj)
        
        if cartItemCreated:
            messages.error(request, "Already added to cart")
        return redirect("shop:detail", slug)
    return redirect('/signin')
    

def mycart(request):
    sess = request.session.get("data", {"items":[]})
    products = Product.objects.filter(active=True, slug__in=sess["items"])
    categories = Category.objects.filter(active=True)
    context = {"products": products,
               "categories": categories,
               "title": "My Cart"}
    return render(request, "shop/list.html", context)


def checkout(request):
    request.session.pop('data', None)
    return redirect("/")

@api_view(['GET'])
def api_products(request):
    query = request.GET.get("q", "")
    products = Product.objects.filter(Q(name__contains=query) | Q(description__contains=query))
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


