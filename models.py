#!/usr/bin/env python 
# -*- coding: utf-8 -*-


from flask.ext.mongoengine import MongoEngine

db = MongoEngine()

class MongoUser(db.Document):

    meta = {'allow_inheritance': True}

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

    @classmethod
    def get(cls, email):
        try:
            return cls.objects.get(email=email)
        except:
            return cls(email=email).save()

class Battle(db.Document):
    dragon = db.StringField(max_length=50)
    ppl = db.StringField(max_length=50)
    started = db.BooleanField(default=False)
    finish = db.BooleanField(default=False)