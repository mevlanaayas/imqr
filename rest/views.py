# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import os
import uuid

import jwt
from MyQR import myqr
from PIL import Image
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from imgqr import settings
from rest.models import QR


def index(request):
    client_cookie = request.COOKIES.get("client")
    set_cookie = False

    try:
        decode = jwt.decode(client_cookie, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decode["userId"]
    except Exception as _:
        logging.error("invalid token or no token at all. new token will be generated")
        set_cookie = True
        user_id = str(uuid.uuid4())

    context = {
        'user': user_id,
        'qr_uploaded': QR.objects.filter(user__exact=user_id).count(),
        'total_views': QR.objects.aggregate(Sum('view_count')).get('view_count__sum') or 0,
        'unique_users': QR.objects.values('user').distinct().count()
    }

    http_response = render(request, 'rest/index.html', context)
    if set_cookie:
        client_cookie = jwt.encode({"userId": user_id}, settings.SECRET_KEY, algorithm="HS256")
        http_response.set_cookie(key="client", value=client_cookie, httponly=True,
                                 expires=datetime.datetime(2080, 1, 1))
    return http_response


def library(request):
    client_cookie = request.COOKIES.get("client")

    try:
        decode = jwt.decode(client_cookie, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decode["userId"]
    except Exception as _:
        logging.error("invalid token or no token at all. redirect to index page")
        return HttpResponseRedirect(reverse('rest:index'))

    query_set = QR.objects.filter(user__exact=user_id)

    image_list = {}
    for q in query_set:
        with open(q.url, "rb") as image_file:
            image_list[q.qr] = base64.b64encode(image_file.read()).decode('utf-8')

    context = {
        'qr_uploaded': query_set.count(),
        'image_list': image_list
    }

    return render(request, 'rest/library.html', context)


def detail(request, file_id):
    client_cookie = request.COOKIES.get("client")
    user_id = ""
    count = 0
    try:
        decode = jwt.decode(client_cookie, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decode["userId"]
    except Exception as _:
        pass
    owner = False
    qr = QR.objects.filter(qr=file_id)
    if qr.count() > 0:
        qr = qr.first()
        qr.view_count += 1
        qr.save()
        if user_id == str(qr.user):
            owner = True

    with open(qr.url, "rb") as image_file:
        image = base64.b64encode(image_file.read()).decode('utf-8')

    if user_id != "":
        count = QR.objects.filter(user=user_id).count()

    return render(request, 'rest/detail.html',
                  {'file_id': file_id, 'owner': owner, 'image': image, 'count': count, 'view_count': qr.view_count})


def upload(request):
    if request.method != "POST":
        return HttpResponse("Unsupported method %s" % request.method)

    client_cookie = request.COOKIES.get("client")

    try:
        decode = jwt.decode(client_cookie, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decode["userId"]
    except Exception as _:
        logging.error("invalid token or no token at all. redirect to index page")
        return HttpResponseRedirect(reverse('rest:index'))

    data = request.POST["data"]
    image = request.FILES.get("image")

    qr, content_type = create(image, data)
    QR.objects.create(user=user_id, qr=qr, content_type=content_type, view_count=0)

    return HttpResponseRedirect(reverse('rest:library'))


def delete(request, file_id):
    if request.method != "GET":
        return HttpResponse("Unsupported method %s" % request.method)

    client_cookie = request.COOKIES.get("client")

    try:
        decode = jwt.decode(client_cookie, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decode["userId"]
    except Exception as _:
        logging.error("invalid token or no token at all. redirect to index page")
        return HttpResponseRedirect(reverse('rest:index'))

    qr = QR.objects.filter(qr=file_id, user=user_id)
    if qr.count() == 1:
        os.remove(qr.url)
        qr.delete()
        return HttpResponseRedirect(reverse('rest:index'))
    else:
        logging.error("error while deleting qr. redirect to index page")
        return HttpResponseRedirect(reverse('rest:index'))


def create(image, data):
    img = Image.open(image)
    split = image.name.split(".")
    content_type = "png"

    if len(split) > 1:
        if content_type in ['gif']:
            content_type = split[1]

    file_id = str(uuid.uuid4())
    temp_filename = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, '%s.%s' % (file_id, content_type))
    img.save(temp_filename)

    load_filename = temp_filename
    temp_save_filename = 'qrized_%s.%s' % (file_id, content_type)
    save_filename = os.path.join(settings.FILE_UPLOAD_TEMP_DIR, temp_save_filename)
    create_qr(load_filename, save_filename, data)

    os.remove(load_filename)
    return file_id, content_type


def create_qr(load_filename="0.png", save_filename="qr.png", data=None):
    myqr.run(
        str(data),
        version=settings.QR_CODE_DETAIL_VERSION,
        level='H',
        picture=load_filename,
        colorized=True,
        contrast=1.0,
        brightness=1.0,
        save_name=save_filename,
        save_dir=os.getcwd()
    )
