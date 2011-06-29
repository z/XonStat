import sqlalchemy
from sqlalchemy.orm import mapper
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from xonstat.util import strip_colors, html_colors, pretty_date

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

# define objects for all tables
class Player(object):

    def nick_html_colors(self):
        return html_colors(self.nick)

    def nick_strip_colors(self):
        return strip_colors(self.nick)

    def __repr__(self):
        return "<Player(%s, %s, %s, %s)>" % (self.player_id, self.nick, 
                self.create_dt, self.location)


class Mutator(object):
    def __repr__(self):
        return "<Mutator(%s, %s, %s, %s)>" % (self.mutator_cd, self.name, 
                self.descr, self.active_ind)


class GameType(object):
    def __repr__(self):
        return "<GameType(%s, %s, %s)>" % (self.game_type_cd, self.descr, 
                self.active_ind)


class Weapon(object):
    def __repr__(self):
        return "<Weapon(%s, %s, %s)>" % (self.weapon_cd, self.descr, 
                self.active_ind)


class Server(object):
    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return "<Server(%s, %s, %s)>" % (self.server_id, self.name, 
                self.ip_addr)


class Map(object):
    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return "<Map(%s, %s, %s)>" % (self.map_id, self.name, self.version)


class MapGameType(object):
    def __repr__(self):
        return "<MapGameType(%s, %s)>" % (self.map_id, self.game_type_cd)


class Game(object):
    def __init__(self, start_dt=None, game_type_cd=None, 
            server_id=None, map_id=None, winner=None):
        self.start_dt = start_dt
        self.game_type_cd = game_type_cd
        self.server_id = server_id
        self.map_id = map_id
        self.winner = winner

    def __repr__(self):
        return "<Game(%s, %s, %s, %s)>" % (self.game_id, self.start_dt, 
                self.game_type_cd, self.server_id)

    def fuzzy_date(self):
        return pretty_date(self.start_dt)


class PlayerGameStat(object):
    def __init__(self, create_dt=None):
        self.create_dt = create_dt

    def __repr__(self):
        return "<PlayerGameStat(%s, %s, %s, %s)>" \
        % (self.player_id, self.game_id, self.create_dt, self.stat_type)

    def nick_stripped(self):
        return strip_colors(self.nick)

    def nick_html_colors(self):
        return html_colors(self.nick)

    def team_html_color(self):
        # blue
        if self.team == 5:
            return "blue"
        # red
        if self.team == 14:
            return "red"
        if self.team == 13:
            return "yellow"
        if self.team == 10:
            return "pink"


class GameMutator(object):
    def __repr__(self):
        return "<GameMutator(%s, %s)>" % (self.game_id, self.mutator_cd)

class Achievement(object):
    def __repr__(self):
        return "<Achievement(%s, %s, %s)>" % (self.achievement_cd, self.descr,
                self.limit)


class PlayerAchievement(object):
    def __repr__(self):
        return "<PlayerAchievement(%s, %s)>" % (self.player_id, self.achievement_cd)


class PlayerWeaponStat(object):
    def __repr__(self):
        return "<PlayerWeaponStat(%s, %s, %s)>" % (self.player_weapon_stats_id,
                self.player_id, self.game_id)


class Hashkey(object):
    def __init__(self, player_id=None, hashkey=None):
        self.player_id = player_id
        self.hashkey = hashkey

    def __repr__(self):
        return "<Hashkey(%s, %s)>" % (self.player_id, self.hashkey)


def initialize_db(engine=None):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    MetaData = sqlalchemy.MetaData(bind=engine, reflect=True)

    # assign all those tables to an object
    achievements_table = MetaData.tables['achievements']
    cd_achievement_table = MetaData.tables['cd_achievement']
    cd_game_type_table = MetaData.tables['cd_game_type']
    cd_mutator_table = MetaData.tables['cd_mutator']
    cd_weapon_table = MetaData.tables['cd_weapon']
    db_version_table = MetaData.tables['db_version']
    game_mutators_table = MetaData.tables['game_mutators']
    games_table = MetaData.tables['games']
    hashkeys_table = MetaData.tables['hashkeys']
    map_game_types_table = MetaData.tables['map_game_types']
    maps_table = MetaData.tables['maps']
    player_game_stats_table = MetaData.tables['player_game_stats']
    players_table = MetaData.tables['players']
    player_weapon_stats_table = MetaData.tables['player_weapon_stats']
    servers_table = MetaData.tables['servers']

    # now map the tables and the objects together
    mapper(PlayerAchievement, achievements_table)
    mapper(Achievement, cd_achievement_table)
    mapper(GameType, cd_game_type_table)
    mapper(Mutator, cd_mutator_table)
    mapper(Weapon, cd_weapon_table)
    mapper(GameMutator, game_mutators_table)
    mapper(Game, games_table)
    mapper(Hashkey, hashkeys_table)
    mapper(MapGameType, map_game_types_table)
    mapper(Map, maps_table)
    mapper(PlayerGameStat, player_game_stats_table)
    mapper(Player, players_table)
    mapper(PlayerWeaponStat, player_weapon_stats_table)
    mapper(Server, servers_table)
