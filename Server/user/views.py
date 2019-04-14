import re
import json
import socket

from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout, login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.core import signing
from django.core.paginator import Paginator

from user.models import UserProfile, UserLog, UserInventory
from umbrella.models import Umbrella, UmbrellaShelf, UmbrellaShelf2Position


"""功能性代码"""
User = get_user_model()


def send_email_to_verify_user(user):
    from_who = settings.EMAIL_HOST_USER  # 发件人  已经写在 配置中了 直接型配置中获取
    to_who = user.email  # 收件人  是一个列表
    subject = '校园雨伞租赁系统的账号确认邮件'  # 发送的主题
    # 发送的消息
    message = '请尽快确认您的账号信息，若您未在本站注册账号，则请忽略此邮件'  # 发送普通的消息使用的时候message
    meg_html = '<a href="http://127.0.0.1:8000/user_register/?u={}" target="_blank">点击跳转</a>'\
        .format(signing.dumps({'email': user.email}))  # 发送的是一个html消息 需要指定
    if send_mail(subject, message, from_who, [to_who], html_message=meg_html):
        return True
    else:
        return False


def index(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'admin_user_panel.html')
        else:
            context_data = {'instruction': request.session.get('index_warning', ''),
                           'user': request.user}
            if request.session.get('index_warning', ''):
                del request.session['index_warning']
            return render(request, 'common_user_panel.html',context=context_data)
    else:
        return redirect('user_login')


def login_view(request):
    context = {
        'instruction': '请登录'
    }
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            if user.is_active:
                login(request, user=user)
                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
                return redirect('index')
            else:
                context['instruction'] = '请激活后再使用'
                return render(request, 'login.html', context=context)
        else:
            context['instruction'] = '用户名或密码错误'
            return render(request, 'login.html', context=context)
    else:
        return render(request, 'login.html', context=context)


@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return redirect('index')


@login_required(login_url='/login/')
def user_change_password(request):
    return render(request, 'user_change_password.html')


def user_register(request):
    context = {
        'instruction': '请注册'
    }
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email', '')
        school = request.POST.get('school', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not email or not school or not password1 or not password2:
            context['instruction'] = '请填写全部字段'
            return render(request, 'register.html', context=context)

        if User.objects.filter(email__exact=email).count() >= 1:
            context['instruction'] = '该账号已被注册'
            return render(request, 'register.html', context=context)

        if password1 != password2:
            context['instruction'] = '两次输入的密码不一致'
            return render(request, 'register.html', context=context)

        try:
            email_ = re.match(r'(.+@.+\..+)', email).group(1)
            if email_:
                pass
            else:
                raise AttributeError
        except AttributeError:
            context['instruction'] = '请检查邮箱格式'
            return render(request, 'register.html', context=context)

        user = User(email=email, school=school)
        user.set_password(password1)
        user.is_active = False
        if send_email_to_verify_user(user):
            context['instruction'] = '请查看您邮箱的收件箱进行后续验证'
            user.save()
            return render(request, 'register.html', context=context)
        else:
            context['instruction'] = '未能正常发送确认邮件，请重新注册或联系管理员'
            return render(request, 'register.html', context=context)
    elif request.method == 'GET':
        if request.GET.get('u', ''):
            user_id = signing.loads(request.GET.get('u', '')).get('email')
            print(signing.loads(request.GET.get('u', '')), signing.loads(request.GET.get('u', '')).get('user_id'))
            if User.objects.filter(email__exact=user_id).count() == 1:
                user = User.objects.get(email=user_id)
                user.is_active = True
                user.save()
                login(request, user)
                return redirect('index')
            else:
                context['instruction'] = '无法识别'
                return render(request, 'register.html', context=context)

    return render(request, 'register.html', context=context)


def server_borrow_umbrella(position_umbrella_shelf_id, position_id):
    client = socket.socket()
    client.settimeout(2)
    client.connect(('localhost', 65431))
    send_string = json.dumps({"shelf_id": position_umbrella_shelf_id, "pos_id": position_id})
    client.sendall(send_string.encode())
    result = json.loads(client.recv(1024).decode())
    client.close()
    return result.get('result', False)


@login_required(login_url='/login/')
def borrow_umbrella(request):
    if not request.user.is_authenticated:
        return redirect('user_login')

    data = {
        'instruction': ''
    }
    if request.user.pledge_money <= 0 or request.user.balance <= 0:
        data['instruction'] = '余额不足或未缴纳押金'
        return render(request, 'borrow.html', data)

    if request.method == 'POST':
        pk = int(request.POST.get('pos_id', '-1'))
        # based on the umbrella shelf position
        if UmbrellaShelf2Position.objects.filter(pk=pk).count() == 1:
            position = UmbrellaShelf2Position.objects.get(pk=pk)
            if position.umbrella is None:
                data['instruction'] = '架子上没伞或伞不可借'
                return render(request, 'borrow.html', data)
            if Umbrella.objects.filter(pk=position.umbrella.pk).count() != 1:
                data['instruction'] = '架子上没伞或伞不可借'
                return render(request, 'borrow.html', data)
            umbrella = Umbrella.objects.get(pk=position.umbrella.pk)
            if position.status == '1' and umbrella.status == '1':
                # from server import borrow_umbrella
                print('用户请求借伞: shelf_id: {} - pos_id: {}'.format(position.umbrella_shelf.id, position.id))
                if server_borrow_umbrella(position.umbrella_shelf.id, position.id):
                    umbrella.status = '0'
                    position.umbrella = None
                    position.status = '0'
                    log = UserLog()
                    log.user = request.user
                    log.action = '1'
                    log.memo = 'borrow umbrella: {}'.format(umbrella.pk)

                    user_inventory = UserInventory()
                    user_inventory.user = request.user
                    user_inventory.umbrella = umbrella

                    user_inventory.save()
                    log.save()
                    position.save()
                    umbrella.save()
                    return redirect('giveback')
                data['instruction'] = 'Oops, 服务器出了点问题，借伞失败'
                return render(request, 'borrow.html', data)
            else:
                data['instruction'] = '架子上没伞或伞不可借'
                return render(request, 'borrow.html', data)
        else:
            data['instruction'] = '伞架位置不存在'
            return render(request, 'borrow.html', data)
    else:
        return render(request, 'borrow.html', context=data)

'''
    if Umbrella.objects.filter(pk=pk).count == 1:
        # if the umbrella exists
        umbrella = Umbrella.objects.get(pk=pk)
        if umbrella.status == '1':
            # if umbrella is free to use
            umbrella.status = '0'
            position = UmbrellaShelf2Position.objects.get(umbrella=umbrella)
            position.umbrella = None
            position.status = '0'

            log = UserLog()
            log.action = '1'
            log.memo = 'borrow umbrella: {}'.format(umbrella.pk)

            user_inventory = UserInventory()
            user_inventory.user = request.user
            user_inventory.umbrella = umbrella

            user_inventory.save()
            log.save()
            position.save()
            umbrella.save()
        else:
            request.session['index_warning'] = '该伞不在架，无法借伞'
            return redirect('index')
    else:
        request.session['index_warning'] = '该伞不存在，无法借伞'
        return redirect('index')
'''


@login_required(login_url='/login/')
def give_back_umbrella(request):
    data = {
        'instruction': '',
        'inventories': None
    }

    if request.GET.get('umbrella_id'):
        if UserInventory.objects.filter(user=request.user, umbrella__pk=int(request.GET.get('umbrella_id'))).count() != 1:
            data['instruction'] = '用户没借过这把伞'
            return render(request, 'giveback.html', data)
        # if UmbrellaShelf2Position.objects.filter(pk=int(request.GET.get('pos_id'))).count() != 1:
        #     data['instruction'] = '伞架不存在'
        #     return render(request, 'giveback.html', data)
        # if UmbrellaShelf2Position.objects.get(pk=int(request.GET.get('pos_id'))).status != '0':
        #     data['instruction'] = '伞架上面已经有伞'
        #     return render(request, 'giveback.html', data)
        if Umbrella.objects.filter(pk=int(request.GET.get('umbrella_id'))).count() == 1:
            umbrella = Umbrella.objects.get(pk=int(request.GET.get('umbrella_id')))
            if umbrella.status == '1': # 在架状态，说明已经归位
                if UserInventory.objects.filter(user=request.user, umbrella__pk=int(request.GET.get('umbrella_id'))).count() == 1:
                    record = UserInventory.objects.get(user=request.user, umbrella__pk=int(request.GET.get('umbrella_id')))
                    user = UserProfile.objects.get(pk=request.user.pk)
                    days = (timezone.now() - record.time).days
                    if days < 1:
                        days = 1
                    print('用户余额：',user.balance, 'days：', days)
                    user.balance -= 1.5*days
                    user.save()
                    log = UserLog(user=user, action='2', memo='give back umbrella: {}'.format(umbrella.pk))
                    log.save()
                    record.delete()
                    data['instruction'] = '还伞成功'
                    data['user'] = user

                    return render(request, 'giveback.html', data)
        data['instruction'] = '还伞失败'
        return render(request, 'giveback.html', data)
    else:
        page = int(request.GET.get('p', '1'))
        inventories = UserInventory.objects.filter(user=request.user).order_by('pk')
        loader = Paginator(inventories, 10)
        data['inventories'] = loader.page(page)
        return render(request, 'giveback.html', data)

