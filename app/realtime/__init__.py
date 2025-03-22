from flask import Blueprint

realtime = Blueprint('realtime', __name__)

from . import events 