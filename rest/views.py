import json

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest.models import BlogPost, PostCategory, ApiToken
from django.contrib.auth.models import User
from django.contrib.auth.tokens import salted_hmac
from rest.forms import UserForm, TokenForm
from django import shortcuts
from datetime import datetime, timedelta
from django.utils import timezone
import re


class RestApi:
    @csrf_exempt
    def api(request):
        token_availability = RestApi.check_token_availability(request)
        result = token_availability['result']
        status = token_availability['status']
        if result is True:
            token_id = token_availability['available_token']
            if request.method == 'GET':
                return RestApi.get(request, token_id)

            elif request.method == 'POST':
                return RestApi.post(request, token_id)

            elif request.method == 'PUT':
                return RestApi.put(request)

            elif request.method == 'DELETE':
                return RestApi.delete(request)
            else:
                return JsonResponse({'result': 'you can\'t send this type of request'})
        else:
            return JsonResponse({'result': result}, status=status)

    def get(request, token_id):
        post_id = request.GET.get('post_id')
        available_token = ApiToken.objects.get(id=token_id)
        if post_id:
            user = available_token.token_user
            post_query = BlogPost.objects.filter(id=post_id)
            if post_query.first():
                if post_query.first().post_author == user or \
                        post_query.first().post_privacy == 'public':
                    data = {'post_title': post_query.first().post_title,
                            'post_content': post_query.first().post_content,
                            'post_id': post_query.first().id,
                            'post_author': post_query.first().post_author.username,
                            'post_category': post_query.first().post_category.category_name,
                            'post_privacy': post_query.first().post_privacy
                            }
                    response = JsonResponse(data, status=200)
                    return response
                else:
                    data = {'Error message:': 'you\'re not able to see this post'}
                    return JsonResponse(data, status=403)
            else:
                data = {'Error message:': 'this post is not valid'}
                return JsonResponse(data, status=404)
        else:
            first_item = request.GET.get('first_item') or None
            last_item = request.GET.get('last_item') or None
            if first_item and last_item:
                try:
                    first_numb = int(first_item)
                    last_numb = int(last_item)

                except Exception as e:
                    return JsonResponse({'result': str(e)}, status=400)
            else:
                first_numb = 1
                last_numb = 5

            item_delta = last_numb - first_numb
            if item_delta < 5:
                user = available_token.token_user
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
                return JsonResponse({'data': data}, status=200)
            else:
                data = {'Error message:': 'You can\'t request more than 5 items'}
                return JsonResponse(data, status=400)

    def post(request, token_id):
        available_token = ApiToken.objects.get(id=token_id)
        user = available_token.token_user
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        title = body['post_title']
        content = body['post_content']
        category = body['post_category']
        privacy = body['post_privacy']
        post_privacy = 'public'
        if (title and content and category and privacy) is not None:
            post_author = user
            if post_author:
                post_category = PostCategory.objects.filter(id=category)
                if post_category.first():
                    if privacy == 'Private' or privacy == 'private':
                        post_privacy = 'private'
                    new_post = BlogPost.objects.create(
                        post_title=title,
                        post_content=content,
                        post_author=post_author,
                        post_category=post_category.first(),
                        post_privacy=post_privacy
                    )
                    new_post.save()
                    data = {'result': 'OK',
                            'post-id': new_post.id,
                            'post-title': title,
                            'post-content': content,
                            'post-category': post_category.first().category_title,
                            'post-privacy': post_privacy
                            }
                    return JsonResponse(data, status=200)
                else:
                    data = {'result': 'insert a valid category(id)'}
                    return JsonResponse(data, status=404)
            else:
                data = {'result': 'insert a valid author(user)'}
                return JsonResponse(data, status=404)
        else:
            data = {'result': 'insert title, content, author and category id of the post'}
            return JsonResponse(data, status=400)

    def put(request):
        post_id = request.GET.get('post_id')
        if post_id:
            post = BlogPost.objects.filter(id=post_id)
            if post.first():
                current_post = BlogPost.objects.get(id=post_id)
                if request.GET.get('post_title') is not None:
                    current_post.post_title = request.GET.get('post_title')
                    current_post.save()

                elif request.GET.get('post_content') is not None:
                    current_post.post_content = request.GET.get('post_content')
                    current_post.save()

                elif request.GET.get('post_category') is not None:
                    post_category = PostCategory.objects.filter(id=request.GET.get('post_category'))
                    if post_category.first():
                        current_post.post_category = post_category.first()
                        current_post.save()
                    else:
                        data = {'result': 'insert available category'}
                        return JsonResponse(data)
                else:
                    data = {'result': 'insert your editing field'}
                    return JsonResponse(data, status=400)

                data = {'result': 'The \' ' + str(current_post.id) + '-' + current_post.post_title + '\' ' +
                                  'post has been changed successfully. '}
                return JsonResponse(data, status=200)
            else:
                data = {'result': 'Insert a valid post id!'}
                return JsonResponse(data, status=404)
        else:
            data = {'result': 'insert a post id'}
            return JsonResponse(data, status=400)

    def delete(request):
        post_id = request.GET.get('post_id')
        if post_id:
            post = BlogPost.objects.filter(id=post_id).first()
            if post:
                deleted_id = post.id
                post.delete()
                data = {'result': 'The \' ' + str(deleted_id) + ' \'' +
                                  ' post has been deleted successfully. '}
                return JsonResponse(data)
            else:
                data = {'result': 'insert a valid post id'}
                return JsonResponse(data)
        else:
            data = {'result': 'insert a post id'}
            return JsonResponse(data)

    def check_token_availability(request):
        sent_token = request.META.get('HTTP_AUTHORIZATION')
        if sent_token is not None:
            req_token = sent_token.split(' ')[1]
            res_token = ApiToken.objects.filter(token_content=req_token)
            if res_token.first():
                available_token = res_token.first()
                token_expired = available_token.token_expired
                if datetime.strptime(str(token_expired)[:19], "%Y-%m-%d %H:%M:%S") > datetime.now():
                    time_difference = timedelta(minutes=5)
                    token_expired += time_difference
                    available_token.token_expired = token_expired
                    available_token.save()
                    data = {'result': True, 'available_token': available_token.id, 'status': 200}
                    return data
                else:
                    data = {'result': 'Your token has been expired, '
                                      'you must login again for new access token.', 'status': 400}
                    return data
            else:
                data = {'result': 'not available Token', 'status': 404}
                return data
        else:
            data = {'result': 'please send your token with your request', 'status': 401}
            return data

    @csrf_exempt
    def categories(request):
        if request.method == 'GET':
            token_availability = RestApi.check_token_availability(request)
            result = token_availability['result']
            if result is True:
                category_query = PostCategory.objects.all()
                data = [{
                    'category_title': cat.category_name,
                    'category_id': cat.id
                } for cat in category_query]
                return JsonResponse({'data': data})
            else:
                return JsonResponse({'result': result})
        else:
            return JsonResponse({'result': 'you can\'t send this type of request'})


class UserActivity:

    _template_login = 'rest/login.html'
    _template_register = 'rest/register.html'

    def register(request):

        if request.method == 'POST':
            user_form = UserForm(request.POST)
            username = request.POST['username']
            password = request.POST['password']
            username_checking = Utilities.RegEx.check_username_matching(username)
            password_checking = Utilities.RegEx.check_password_matching(password)

            if user_form.is_valid():
                if username_checking is True:
                    if password_checking is True:
                        user_form.save()
                        user = User.objects.get(username=username)
                        time_difference = timedelta(minutes=5)
                        expire_date = timezone.now() + time_difference

                        """TODO : check why token/user _form doesn't have
                         cleaned_data without breakpoint but it has with it...!"""

                        my_token = salted_hmac(user, datetime.now()).hexdigest()
                        token = ApiToken(token_content=my_token,
                                         token_expired=expire_date,
                                         token_user=user)
                        token.save()
                        return JsonResponse({
                             'token: ': token.token_content,
                             'expired: ':  token.token_expired,
                        })
                    else:
                        user_form.add_error('password', password_checking['Err'])
                else:
                    user_form.add_error('username', username_checking['Err'])
        else:
            user_form = UserForm()
        return shortcuts.render(request, UserActivity._template_register, {
            'user_form': user_form,
        })

    def login(request):

        if request.method == 'POST':
            user_form = UserForm(request.POST)
            token_form = TokenForm(request.POST)
            client_id = request.POST['token_clientId']
            password = request.POST['password']
            username = request.POST['username']
            password_checking = Utilities.RegEx.check_password_matching(password)
            username_checking = Utilities.RegEx.check_username_matching(username)
            if username_checking is True:

                if password_checking is True:
                    user = User.objects.filter(Q(username=username) & Q(password=password))

                    if user.first() is not None:
                        time_difference = timedelta(minutes=5)
                        expire_date = timezone.now() + time_difference
                        my_token = str(salted_hmac(datetime.now(), user.first()).hexdigest())
                        token = ApiToken(token_content=my_token,
                                         token_expired=expire_date,
                                         token_clientId=client_id,
                                         token_user=user.first())
                        token.save()
                        return JsonResponse({'token': token.token_content,
                                             'expired': token.token_expired,
                                             'clientId': token.token_clientId})
                    else:
                        return JsonResponse({'Error': 'this user is not available'})
                else:
                    user_form.add_error('password', password_checking['Err'])
            else:
                user_form.add_error('username', username_checking['Err'])
        else:
            user_form = UserForm()
            token_form = TokenForm()
        return shortcuts.render(request, UserActivity._template_login, {
            'user_form': user_form,
            'token_form': token_form
        })


class Utilities:

    class RegEx:

        def check_password_matching(password):
            regex = '[A-Za-z0-9@.+_-]{6,}'
            user_password = str(password)
            matching = re.findall(regex, user_password)
            matching_len = len(str(matching)) - 4
            if matching_len == len(user_password):
                return True
            else:
                data = {'Err': 'your password can only include '
                               'A-Z, a-z, 0-9 and /@/./_/+/-/'
                               'and it must be at least 6 characters'
                        }
                return data

        def check_username_matching(username):
            regex = '[A-Za-z0-9+.@_-]{3,}'
            user_name = str(username)
            matching = re.findall(regex, user_name)
            matching_len = len(str(matching)) - 4
            if matching_len == len(user_name):
                return True
            else:
                data = {'Err': 'your username can only include '
                               'A-Z, a-z, 0-9 and /@/./_/+/-/'
                               'and it must be at least 3 characters'}
                return data






