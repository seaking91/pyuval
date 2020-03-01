#!/usr/bin/python3

from flask import Blueprint, request, make_response
from .pyuval import OTPValidator
import sys

bp = Blueprint('pyval', __name__)

@bp.route('/', methods=['GET'])
def index():
    return make_response('Not Found!', 404)

@bp.route('/wsapi/1.0/verify', methods=['GET'])
def versionOne():
    return make_response("Only Version 2 is supported", 404)

@bp.route('/wsapi/2.0/verify', methods=['GET'])
def verify():
    origin = request.remote_addr
    xForwardedFor = request.headers.get('x-forwarded-for')
    if xForwardedFor:
        origin += ' [{}]'.format(xForwardedFor)
    otpValidator = OTPValidator(source=origin, **request.args)
    response = make_response(otpValidator.validateOTP(), 200)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response
