# 雨伞租赁系统

[TOC]

## 环境配置

- 下载并安装Python3.6.3<https://www.python.org/downloads/>，注意配置环境变量
- 打开命令行，按照<https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>配置pip源
- 确保MySQL服务打开，修改`UmbrellaRentalSystemWeb/settings.py`文件

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '这里写你的数据库名', # 数据库必须是UTF8编码
        'HOST': '127.0.0.1',
        'USER': '数据库连接用户名',
        'PASSWORD': '密码',
    }
}
```

- 在源码文件夹内打开命令行
  - `pip install requirements.txt`
  - `python manage.py makemigrations user`
  - `python manage.py makemigrations`
  - `python manage.py migrate user`
  - `python manage.py migrate`
  - 创建管理员：`python manage.py createsuperuser`
- 确保电脑连接至路由器
  - 打开多线程服务器：`python server.py`
  - 开启网站服务器：`python manage.py runserver 0.0.0.0:80`
  - 之后就可在`http://127.0.0.1`中打开网站

## 参考库

- Django：<https://www.djangoproject.com>

## JSON数据流API定义

### 伞架连接服务器
伞架向服务器
```json
{
  "heart": false,
  "ack": false,
  "shelf": {
    "id": "<shelf id>",
    "code": "<shelf identify code>"
  },
  "action": {
    "number": -1,
    "pos_id": -1,
    "umbrella_uid": ""
  }
}
```
服务器返回
```json
{
  "heart": false,
  "connection": true,
  "ack": true,
  "action": {
    "number": -1,
    "pos_id": -1,
    "umbrella_id": -1
  }
}
```
### 借伞
服务器发送
```json
{
  "heart": false,
  "connection": true,
  "ack": false,
  "action": {
    "number": 1,
    "pos_id": 6,
    "umbrella_id": 1
  }
}
```

伞架返回值
```json
{
  "heart": false,
  "ack": true,
  "shelf": {
    "id": "<shelf id>",
    "code": "<shelf identify code>"
  },
  "action": {
    "number": 1,
    "pos_id": 6,
    "umbrella_uid": ""
  }
}
```
### 还伞
伞架向服务器发送
```json
{
  "heart": false,
  "ack": false,
  "shelf": {
    "id": "<shelf id>",
    "code": "<shelf identify code>"
  },
  "action": {
    "number": 2,
    "pos_id": 6,
    "umbrella_uid": "umbrella uid>"
  }
}
```
服务器返回
```json
{
  "heart": false,
  "connection": true,
  "ack": true,
  "action": {
    "number": 2,
    "pos_id": 6,
    "umbrella_id": 1
  }
}
```