from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext import admin
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib import sqlamodel
from flask.ext.admin.contrib.sqlamodel import filters
from flask.ext.admin.contrib.fileadmin import FileAdmin

import os
import os.path as op

import app_config


app = Flask(__name__)

app.config.from_object(app_config.DevConfig)
db = SQLAlchemy(app)


class Civilization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    civ_name = db.Column(db.String(80), unique=True, nullable=False)
    civ_desc = db.Column(db.Text)

    def __unicode__(self):
        return self.civ_name


leader_traits_table = db.Table('leader_traits', db.Model.metadata,
                               db.Column('leader_id', db.Integer, db.ForeignKey('leader.id')),
                               db.Column('trait_id', db.Integer, db.ForeignKey('trait.id'))
                               )

leader_flaws_table = db.Table('leader_flaws', db.Model.metadata,
                              db.Column('leader_id', db.Integer, db.ForeignKey('leader.id')),
                              db.Column('flaw_id', db.Integer, db.ForeignKey('flaw.id'))
                              )


class Leader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    leader_name = db.Column(db.String(120), unique=True, nullable=False)
    leader_desc = db.Column(db.Text)
    traits = db.Column(db.Text)
    flaws = db.Column(db.Text)

    civilization_id = db.Column(db.Integer(), db.ForeignKey(Civilization.id))
    civilization = db.relationship(Civilization, backref='leaders')

    traits = db.relationship('Trait', secondary=leader_traits_table)
    flaws = db.relationship('Flaw', secondary=leader_flaws_table)

    def __unicode__(self):
        return self.leader_name


class Trait(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)

    def __unicode__(self):
        return self.name


class Flaw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)

    def __unicode__(self):
        return self.name


class LeaderList(sqlamodel.ModelView):
    sortable_columns = ('leader_name', 'civilization', 'leader_desc')
    searchable_columns = ('leader_desc', 'leader_name', Civilization.civ_name)
    column_filters = ('civilization', 'leader_name')

    def __init__(self, session):
        super(LeaderList, self).__init__(Leader, session, category='World')


class CivilizationList(sqlamodel.ModelView):
    sortable_columns = ('civ_name', 'civ_desc')
    searchable_columns = ('civ_name', 'civ_desc')
    column_filters = ('civ_name', 'civ_desc')

    def __init__(self, session):
        super(CivilizationList, self).__init__(Civilization, session, category='World')


class ExportView(BaseView):
    @expose('/')
    def index(self):
        return self.render('export.html')


if __name__ == '__main__':
    admin = admin.Admin(app, 'civ-modmaker')

    admin.add_view(LeaderList(db.session))
    admin.add_view(CivilizationList(db.session))
    admin.add_view(sqlamodel.ModelView(Trait, db.session, category='Components', name='Leader Traits'))
    admin.add_view(sqlamodel.ModelView(Flaw, db.session, category='Components', name='Leader Flaws'))
    admin.add_view(ExportView(name='Export', category='Management'))

    path = op.join(op.dirname(__file__), app.config['RESOURCE_DIR'])
    try:
        os.mkdir(path)
    except OSError:
        pass

    admin.add_view(FileAdmin(path, app.config['RESOURCE_DIR'], name='Resources', category='Components'))

    db.create_all()

    app.run('0.0.0.0', 5000)
