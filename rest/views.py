from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest.models import BlogPost, PostCategory, ApiToken
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from rest.forms import UserForm
from django import shortcuts
from datetime import datetime, timedelta
import pytz
import re


class RestApi:
    @csrf_exempt
    def api(request):
        req_token = str(request.META['HTTP_AUTHORIZATION']).split(' ')[1]
        if req_token is not None:
            res_token = ApiToken.objects.filter(token_content=req_token)
            if res_token.first() is not None:
                token_expired = res_token.first().token_expired
                iran = pytz.timezone('Iran')
                if token_expired > datetime.now(iran):
                    if request.method == 'GET':
                        first_item = request.GET.get('first_item')
                        last_item = request.GET.get('last_item')
                        try:
                            item_delta = int(last_item) - int(first_item)
                            first_numb = int(first_item)
                            last_numb = int(last_item)
                        except Exception as e:
                            return JsonResponse({"Error": e})
                        post_id = request.GET.get('post_id')
                        if item_delta < 5:
                            if post_id is not None:
                                client = res_token.first().token_clientId
                                post_query = BlogPost.objects.get(id=post_id)
                                if post_query.post_author == client or post_query.post_privacy == "public":
                                    my_queryset = BlogPost.objects.get(id=post_id)
                                    data = {'post_title': my_queryset.post_title,
                                            'post_content': my_queryset.post_content,
                                            'post_id': my_queryset.id,
                                            'post_author': my_queryset.post_author.username,
                                            'post_category': my_queryset.post_category.category_name
                                            }
                                    response = JsonResponse(data)
                                    return response
                                else:
                                    data = {'Error message:': 'you\'re not able to see this post'}
                                    return JsonResponse(data)
                            else:
                                client_id = res_token.first().token_clientId
                                post_query = BlogPost.objects.filter(
                                    Q(post_privacy='public') |
                                    Q(post_author=client_id)
                                 )[first_numb:last_numb]
                                data = [{'post_title': a.post_title,
                                         'post_content': a.post_content,
                                         'post_author': a.post_author.username,
                                         'post_id': a.pk,
                                         'post_privacy': str(a.post_privacy),
                                         'post_category': a.post_category.category_name
                                         } for a in post_query]
                                return JsonResponse({'data': data})
                        else:
                            data = {'Error message:': 'You can\'t request more than 5 items'}
                            return JsonResponse(data)
                    elif request.method == 'POST':
                        title = request.POST['post_title']
                        content = request.POST['post_content']
                        author = request.POST['post_author']
                        category = request.POST['post_category']
                        post_author = User.objects.get(username=author)
                        post_category = PostCategory.objects.get(id=category)
                        new_post = BlogPost.objects.create(post_title=title, post_content=content, post_author=post_author,
                                                           post_category=post_category)
                        new_post.save()
                        data = {'result': 'OK'}
                        return JsonResponse(data)
                    elif request.method == 'PUT':
                        post_id = request.GET.get('post_id')
                        post = BlogPost.objects.get(id=post_id)
                        if request.GET.get('post_title') is not None:
                            post.post_title = request.GET.get('post_title')
                        elif request.GET.get('post_content') is not None:
                            post.post_content = request.GET.get('post_content')
                        elif request.GET.get('post_author') is not None:
                            post_author = User.objects.get(username=request.GET.get('post_author'))
                            post.post_author = post_author
                        elif request.GET.get('post_category') is not None:
                            post_category = PostCategory.objects.get(category_name=request.GET.get('post_category'))
                            post.post_category = post_category
                        post.save()
                        data = {'result': 'OK'}
                        return JsonResponse(data)
                    elif request.method == 'DELETE':
                        post_id = request.GET.get('post_id')
                        post = BlogPost.objects.get(id=post_id)
                        post.delete()
                        data = {'result': 'OK'}
                        return JsonResponse(data)
                else:
                    data = {'Error message:': 'Your token has been expired, you must login again for new token :) '}
                    return JsonResponse(data)
            else:
                data = {'Error message:': 'not available Token'}
                return JsonResponse(data)
        else:
            data = {'result': 'please send your token with your request'}
            return JsonResponse(data)


class UserActivity:
    def register(request):
        if request.method == 'POST':
            user_data = UserForm(request.POST, prefix='user')
            if user_data.is_valid():
                if re.match(r'[A-Za-z0-9]{6,}', user_data.cleaned_data['password']):
                    user_data.save()
                    user = User.objects.get(username=user_data['username'].value())
                    d = timedelta(minutes=5)
                    iran = pytz.timezone('Iran')
                    expire_date = datetime.now(iran) + d
                    my_token = default_token_generator.make_token(user)
                    token = ApiToken(token_content=my_token,
                                     token_expired=expire_date,
                                     token_clientId=user)
                    token.save()
                    return HttpResponse(token.token_content)
                else:
                    user_data.add_error('password', 'your password must required combination '
                                                    'of A-Z, a-z, 0-9 and at '
                                                    'least 6 characters')
        else:
            user_data = UserForm(prefix='user')
        return shortcuts.render(request, "rest/register.html", {"form": user_data})

    def login(request):
        if request.method == 'POST':
            # user_data = UserForm(request.POST)
            username = request.POST['username']
            password = request.POST['password']
            user = User.objects.get(username=username, password=password)
            if user is not None:
                return JsonResponse({'data': 'Token'})
            else:
                return HttpResponse('Return an \'invalid login\' error message.')
        else:
            user_data = UserForm()
            return shortcuts.render(request, "rest/register.html", {"form": user_data})






