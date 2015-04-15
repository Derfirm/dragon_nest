#!/usr/bin/env python 
# -*- coding: utf-8 -*-


from flask.ext.mongoengine import MongoEngine

db = MongoEngine()

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Document):
    email = db.StringField(required=True)
    nickname = db.StringField(max_length=50, unique = True)

    def __repr__(self):
        return '<User %r>' % (self.nickname)
        
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)