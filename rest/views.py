from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest.models import BlogPost, PostCategory, ApiToken
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator, salted_hmac
from rest.forms import UserForm, TokenForm
from django import shortcuts
from datetime import datetime, timedelta
from django.utils import timezone
import re


class RestApi:
    @csrf_exempt
    def api(request):
        req_token = str(request.META['HTTP_AUTHORIZATION']).split(' ')[1]
        if req_token is not None:
            res_token = ApiToken.objects.filter(token_content=req_token)
            if res_token.first() is not None:
                token_expired = res_token.first().token_expired
                if datetime.strptime(str(token_expired)[:19], "%Y-%m-%d %H:%M:%S") > datetime.now():
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
                                user = res_token.first().token_user
                                post_query = BlogPost.objects.get(id=post_id)
                                if post_query.post_author == user or post_query.post_privacy == "public":
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
                                user = res_token.first().token_user
                                post_query = BlogPost.objects.filter(
                                    Q(post_privacy='public') |
                                    Q(post_author=user)
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
                        new_post = BlogPost.objects.create(
                            post_title=title,
                            post_content=content,
                            post_author=post_author,
                            post_category=post_category
                        )
                        new_post.save()
                        data = {'result': 'OK',
                                'post-title': title,
                                'post-content': content,
                                'post-author': author,
                                'post-category': post_category.category_title
                                }
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
                        data = {'result': 'The \' ' + str(post.id) + '-' + post.post_title + '\' ' +
                                'post has been changed successfully. '}
                        return JsonResponse(data)
                    elif request.method == 'DELETE':
                        post_id = request.GET.get('post_id')
                        post = BlogPost.objects.get(id=post_id)
                        post.delete()
                        data = {'result': 'The \' ' + str(post.id) + 'post has been deleted successfully. '}
                        return JsonResponse(data)
                else:
                    data = {'Error message:': 'Your token has been expired, you must login again for new token.'}
                    return JsonResponse(data)
            else:
                data = {'Error message:': 'not available Token'}
                return JsonResponse(data)
        else:
            data = {'result': 'please send your token with your request'}
            return JsonResponse(data)


class UserActivity:

    _template_login = 'rest/login.html'
    _template_register = 'rest/register.html'

    def register(request):

        if request.method == 'POST':
            user_form = UserForm(request.POST)
            token_form = TokenForm(request.POST)
            username = request.POST['username']
            password = request.POST['password']
            client_id = request.POST['token_clientId']

            if user_form.is_valid():
                if re.match(r'[A-Za-z0-9]{6,}', password):
                    user_form.save()
                    user = User.objects.get(username=username)
                    time_difference = timedelta(minutes=5)
                    expire_date = timezone.now() + time_difference

                    """TODO : check why token/user _form doesn't have
                     cleaned_data without breakpoint but it has with it...!"""

                    my_token = salted_hmac(client_id, user).hexdigest()
                    token = ApiToken(token_content=my_token,
                                     token_expired=expire_date,
                                     token_clientId=client_id,
                                     token_user=user)
                    token.save()
                    return JsonResponse(
                        {'token: ': token.token_content,
                         'expired: ':  token.token_expired,
                         'clientId': token.token_clientId
                         })
                else:
                    user_form.add_error('password', 'your password required combination '
                                                    'of A-Z, a-z, 0-9 and at '
                                                    'least 6 characters')
        else:
            user_form = UserForm(request.POST)
            token_form = TokenForm(request.POST)
        return shortcuts.render(request, UserActivity._template_register, {
            'user_form': user_form,
            'token_form': token_form
        })

    def login(request):

        if request.method == 'POST':
            user_form = UserForm(request.POST)
            token_form = TokenForm(request.POST)
            client_id = request.POST['token_clientId']

            if re.match(r'[A-Za-z0-9]{6,}', request.POST['password']):
                password = request.POST['password']
                print(str(request.POST['username']))
                if re.match(r'[A-Za-z0-9]{3,}', request.POST['username']):
                    username = request.POST['username']
                    user = User.objects.get(Q(username=username) & Q(password=password)) or None

                    if user is not None:
                        time_difference = timedelta(minutes=5)
                        expire_date = timezone.now() + time_difference
                        my_token = str(salted_hmac(datetime.now(), user).hexdigest())
                        token = ApiToken(token_content=my_token,
                                         token_expired=expire_date,
                                         token_clientId=client_id,
                                         token_user=user)
                        token.save()
                        return JsonResponse({'token': token.token_content,
                                             'expired': token.token_expired,
                                             'clientId': token.token_clientId})
                    else:
                        return JsonResponse({'Error': 'this user is not available'})
                else:
                    user_form.add_error('username', 'your username required '
                                                    'A-Z, a-z, 0-9')
            else:
                user_form.add_error('password', 'your password required combination '
                                                'of A-Z, a-z, 0-9 and at '
                                                'least 6 characters')

        else:
            user_form = UserForm
            token_form = TokenForm
        return shortcuts.render(request, UserActivity._template_login, {
            'user_form': user_form,
            'token_form': token_form
        })








