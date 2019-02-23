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
        sent_token = request.META.get('HTTP_AUTHORIZATION')
        if sent_token is not None:
            req_token = sent_token.split(' ')[1]
            res_token = ApiToken.objects.get(token_content=req_token)

            if res_token is not None:
                token_expired = res_token.token_expired
                if datetime.strptime(str(token_expired)[:19], "%Y-%m-%d %H:%M:%S") > datetime.now():
                    time_difference = timedelta(minutes=5)
                    token_expired += time_difference
                    res_token.token_expired = token_expired
                    res_token.save()
                    if request.method == 'GET':
                        post_id = request.GET.get('post_id')
                        if post_id is not None:
                            user = res_token.token_user
                            post_query = BlogPost.objects.get(id=post_id)
                            if post_query.post_author == user or post_query.post_privacy == "public":
                                data = {'post_title': post_query.post_title,
                                        'post_content': post_query.post_content,
                                        'post_id': post_query.id,
                                        'post_author': post_query.post_author.username,
                                        'post_category': post_query.post_category.category_name
                                        }
                                response = JsonResponse(data)
                                return response
                            else:
                                data = {'Error message:': 'you\'re not able to see this post'}
                                return JsonResponse(data)
                        else:
                            try:
                                first_item = request.GET.get('first_item')
                                last_item = request.GET.get('last_item')
                                first_numb = int(first_item)
                                last_numb = int(last_item)
                                item_delta = last_numb - first_numb

                                if item_delta < 5:
                                    user = res_token.token_user
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

                            except Exception as e:
                                return JsonResponse({"Error": str(e)})
                    elif request.method == 'POST':
                        title = request.POST.get('post_title')
                        content = request.POST.get('post_content')
                        author = request.POST.get('post_author')
                        category = request.POST.get('post_category')
                        if (title and content and author and category) is not None:
                            post_author = User.objects.filter(username=author)
                            if post_author.first():
                                post_category = PostCategory.objects.filter(id=category)
                                if post_category.first():
                                    new_post = BlogPost.objects.create(
                                        post_title=title,
                                        post_content=content,
                                        post_author=post_author.first(),
                                        post_category=post_category.first()
                                    )
                                    new_post.save()
                                    data = {'result': 'OK',
                                            'post-title': title,
                                            'post-content': content,
                                            'post-author': author,
                                            'post-category': post_category.first().category_title
                                            }
                                    return JsonResponse(data)
                                else:
                                    data = {'result': 'insert a valid category(id)'}
                                    return JsonResponse(data)
                            else:
                                data = {'result': 'insert a valid author(user)'}
                                return JsonResponse(data)
                        else:
                            data = {'result': 'insert title, content, author and category id of the post'}
                            return JsonResponse(data)
                    elif request.method == 'PUT':
                        post_id = request.GET.get('post_id')
                        if post_id:
                            post = BlogPost.objects.get(id=post_id)
                            if request.GET.get('post_title') is not None:
                                post.post_title = request.GET.get('post_title')
                                post.save()
                            elif request.GET.get('post_content') is not None:
                                post.post_content = request.GET.get('post_content')
                                post.save()
                            elif request.GET.get('post_author') is not None:
                                post_author = User.objects.get(username=request.GET.get('post_author'))
                                post.post_author = post_author
                                post.save()
                            elif request.GET.get('post_category') is not None:
                                post_category = PostCategory.objects.get(category_name=request.GET.get('post_category'))
                                post.post_category = post_category
                                post.save()
                            else:
                                data = {'result': 'insert your editing field'}
                                return JsonResponse(data)

                            data = {'result': 'The \' ' + str(post.id) + '-' + post.post_title + '\' ' +
                                    'post has been changed successfully. '}
                            return JsonResponse(data)
                        else:
                            data = {'result': 'insert a valid post id'}
                            return JsonResponse(data)
                    elif request.method == 'DELETE':
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
                else:
                    data = {'Error message:': 'Your token has been expired, you must login again for new access token.'}
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
                if Utilities.RegEx.check_username_matching(username):
                    if Utilities.RegEx.check_password_matching(password):
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
                        user_form.add_error('password', 'your username can only include '
                                                        'A-Z, a-z, 0-9 and /_/-'
                                                        'and least 6 characters')
                else:
                    user_form.add_error('username', 'your username can only include '
                                                    'A-Z, a-z, 0-9 and /_/-'
                                                    'and least 3 characters')
        else:
            user_form = UserForm()
            token_form = TokenForm()
        return shortcuts.render(request, UserActivity._template_register, {
            'user_form': user_form,
            'token_form': token_form
        })

    def login(request):

        if request.method == 'POST':
            user_form = UserForm(request.POST)
            token_form = TokenForm(request.POST)
            client_id = request.POST['token_clientId']
            password = request.POST['password']
            username = request.POST['username']

            if Utilities.RegEx.check_password_matching(password):

                if Utilities.RegEx.check_username_matching(username):
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
                    user_form.add_error('username', 'your username can only include '
                                                    'A-Z, a-z, 0-9 and /_/-'
                                                    'and least 3 characters')
            else:
                user_form.add_error('password', 'your password can only include '
                                                'A-Z, a-z, 0-9 and /@/./_/+/-/'
                                                'and least 6 characters')
        else:
            user_form = UserForm
            token_form = TokenForm
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
            if matching:
                matching_len = len(str(matching)) - 4
                if matching_len == len(user_password):
                    return True
                else:
                    return False
            else:
                return False

        def check_username_matching(username):
            regex = '[A-Za-z0-9+.@_-]{3,}'
            user_name = str(username)
            matching = re.findall(regex, user_name)
            if matching:
                matching_len = len(str(matching)) - 4
                if matching_len == len(user_name):
                    return True
                else:
                    return False
            else:
                return False







