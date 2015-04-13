#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

import time
import uuid
from dragon import Dragon
from ppl import Player
from core import Battle
from threading import Thread
import functools
import random

from flask_debugtoolbar import DebugToolbarExtension
from flask_redis import Redis
from flask import request
from flask.ext.login import current_user
from flask import Flask, render_template, session#, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
# app.config['DEBUG_TB_PANELS'] = ['flask.ext.mongoengine.panels.MongoDebugPanel']
socketio = SocketIO(app)

# Redis(app, 'REDIS_LINKS')
# Redis(app, 'REDIS_CONTENT')
redis_store = Redis(app)
# toolbar = DebugToolbarExtension(app)

thread = None
# gl_dragon = None
gl_battle = None

def is_finish(battle):
    if battle and (battle.dragon.health <= 0 or battle.finish):
        return True
    return False

def prepare_battle(battle):
    if battle:
        return battle

    dragon = Dragon('Valakas')
    #ten people figth with them!
    brave_people = [Player() for _ in xrange(10)]
    battle = Battle(dragon, brave_people)
    battle.started = True
    return battle

def background_battle(count, battle):
    dragon = battle.dragon
    ppl = battle.ppl
    for pp in ppl:
        pp.attacks(dragon)
        socketio.emit('battle response',
                      {'data': '{0} attack {1} for {2} damage!'.format(pp.name, dragon.name, pp.attack), 'count': count},
                      namespace='/cave')
    if not ppl:
        battle.finish = True
        return socketio.emit('battle response',
                      {'data': "Dragon kill all heroes!", 'count': count},
                      namespace='/cave')

    if dragon.dragon_attack(0.3):
        target = random.choice(ppl)
        target.health -= dragon.attack

        socketio.emit('battle response',
                      {'data': "Dragon wanna attack!", 'count': count},
                      namespace='/cave')
        socketio.emit('battle response',
                      {'data': "{} attack {} for {} damage!".format(dragon.name, target.name, dragon.attack), 'count': count},
                      namespace='/cave')
        if target.health <= 0:
            battle.ppl = [unit for unit in ppl if unit != target]
            socketio.emit('battle response',
                      {'data': "{} kill {}!".format(dragon.name, target.name), 'count': count},
                      namespace='/cave')
    socketio.emit('battle response',
                      {'data': "Dragon's health is {}".format(max(0, dragon.health)), 'count': count},
                      namespace='/cave')


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        global gl_battle
        if is_finish(gl_battle):
            socketio.emit('my response',
                      {'data': 'Dragon is coming soon, wait untill respawn', 'count': count},
                      namespace='/cave')
            del battle
            gl_battle, gl_dragon = None, None
            time.sleep(20)

        battle = prepare_battle(gl_battle)
        gl_battle = battle
        background_battle(count, battle)
        time.sleep(10)
        count += 1


@app.route('/')
def index():
    # global thread
    # if thread is None:
    #     thread = Thread(target=background_thread)
    #     thread.start()
    return render_template('index.html')

def searching_room(dragon):
    room_key = 'room:{dragon}'.format(dragon=dragon)
    return redis_store.smembers(room_key)


@socketio.on('my event', namespace='/cave')
def cave_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('search', namespace='/cave')
def search_room(message):
    #need user
    # TODO refact
    user_name = 'Andrew'
    dragon = message['dragon']
    check_key = redis_store.get(user_name)
    session['receive_count'] = session.get('receive_count', 0) + 1
    if not check_key:
        rooms = searching_room(dragon)
        if not rooms:
            room_id = str(uuid.uuid4())
            redis_store.sadd('room:{}'.format(dragon),*[room_id])
            redis_store.set(user_name, dragon +":"+ room_id)
        else :
            room_id = random.choice(list(rooms))
        
        test_filter = filter(lambda room: room != room_id, request.namespace.rooms)
        if request.namespace.rooms:
                data = 'leave old rooms before!'
        else:
            join_room(room_id)
            redis_store.sadd('room:{}'.format(dragon),*[room_id])
            redis_store.set(user_name, dragon +":"+ room_id)
            request.namespace.channel = room_id
            data = 'join_room: ' + ', '.join(request.namespace.rooms)
        emit('my response',
             {'data': data, 'count': session['receive_count']})
        print request.namespace.channel
    else:
        _, room_id = check_key.split(":")
        request.namespace.channel = room_id
        if not request.namespace.rooms:
            join_room(room_id)
        emit('my response',
                 {'data': 'in room: ' + ', '.join(request.namespace.rooms), 'count': session['receive_count']})


@socketio.on('sent to room', namespace='/cave')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    if request.namespace.channel:
        emit('my response',
             {'data': message['data'], 'count': session['receive_count']},
             room=request.namespace.channel)
    else:
        emit('my response',
             {'data': 'Not in room', 'count': session['receive_count']},)

@socketio.on('start battle', namespace='/cave')
def join_battle(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    if request.namespace.channel:
        global thread
        if thread is None:
            thread = Thread(target=background_thread)
            thread.start()
        # emit('my response',
        #      {'data': "Let's Battle begin!",
        #       'count': session['receive_count']})


@socketio.on('leave', namespace='/cave')
def leave():
    user_name = 'Andrew'
    check_key = redis_store.get(user_name)
    session['receive_count'] = session.get('receive_count', 0) + 1
    if check_key:
        _, room_id = check_key.split(":")
        leave_room(room_id)
        data = 'leave ' + room_id
        request.namespace.channel = None
        redis_store.delete(user_name)
    else:
        data='not in rooms'
    emit('my response',
         {'data': data, 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/cave')
def cave_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


# @socketio.on('join', namespace='/cave')
# def join(message):
#     join_room(message['room'])
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my response',
#          {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
#           'count': session['receive_count']})


# @socketio.on('close room', namespace='/cave')
# def close(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
#                          'count': session['receive_count']},
#          room=message['room'])
#     close_room(message['room'])


@socketio.on('disconnect request', namespace='/cave')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/cave')
def cave_connect():
    request.namespace.channel = None
    #set online?
    emit('my response', {'data': 'Connected', 'count': 0})

@socketio.on_error('/cave')
def error_handler_namespace(value):
    raise value


@socketio.on('disconnect', namespace='/cave')
def cave_disconnect():
    # set reward
    # can't return again
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
