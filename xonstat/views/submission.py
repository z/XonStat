import datetime
import logging
import re
import time
from pyramid.response import Response
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from xonstat.models import *

log = logging.getLogger(__name__)


def get_or_create_server(session=None, name=None):
    """
    Find a server by name or create one if not found. Parameters:

    session - SQLAlchemy database session factory
    name - server name of the server to be found or created
    """
    try:
        # find one by that name, if it exists
        server = session.query(Server).filter_by(name=name).one()
        log.debug("Found server id {0} with name {1}.".format(
            server.server_id, server.name))
    except NoResultFound, e:
        server = Server(name=name)
        session.add(server)
        session.flush()
        log.debug("Created server id {0} with name {1}".format(
            server.server_id, server.name))
    except MultipleResultsFound, e:
        # multiple found, so use the first one but warn
        log.debug(e)
        servers = session.query(Server).filter_by(name=name).order_by(
                Server.server_id).all()
        server = servers[0]
        log.debug("Created server id {0} with name {1} but found \
                multiple".format(
            server.server_id, server.name))

    return server

def get_or_create_map(session=None, name=None):
    """
    Find a map by name or create one if not found. Parameters:

    session - SQLAlchemy database session factory
    name - map name of the map to be found or created
    """
    try:
        # find one by the name, if it exists
        gmap = session.query(Map).filter_by(name=name).one()
        log.debug("Found map id {0} with name {1}.".format(gmap.map_id, 
            gmap.name))
    except NoResultFound, e:
        gmap = Map(name=name)
        session.add(gmap)
        session.flush()
        log.debug("Created map id {0} with name {1}.".format(gmap.map_id,
            gmap.name))
    except MultipleResultsFound, e:
        # multiple found, so use the first one but warn
        log.debug(e)
        gmaps = session.query(Map).filter_by(name=name).order_by(
                Map.map_id).all()
        gmap = gmaps[0]
        log.debug("Found map id {0} with name {1} but found \
                multiple.".format(gmap.map_id, gmap.name))

    return gmap


def create_game(session=None, start_dt=None, game_type_cd=None, 
        server_id=None, map_id=None, winner=None):
    """
    Creates a game. Parameters:

    session - SQLAlchemy database session factory
    start_dt - when the game started (datetime object)
    game_type_cd - the game type of the game being played
    server_id - server identifier of the server hosting the game
    map_id - map on which the game was played
    winner - the team id of the team that won
    """

    game = Game(start_dt=start_dt, game_type_cd=game_type_cd,
                server_id=server_id, map_id=map_id, winner=winner)
    session.add(game)
    session.flush()
    log.debug("Created game id {0} on server {1}, map {2} at time \
            {3} and on map {4}".format(game.game_id, 
                server_id, map_id, start_dt, map_id))

    return game


def get_or_create_player(session=None, hashkey=None, nick=None):
    """
    Finds a player by hashkey or creates a new one (along with a
    corresponding hashkey entry. Parameters:

    session - SQLAlchemy database session factory
    hashkey - hashkey of the player to be found or created
    nick - nick of the player (in case of a first time create)
    """
    # if we have a bot
    if re.search('^bot#\d+$', hashkey):
        player = session.query(Player).filter_by(player_id=1).one()
    # if we have an untracked player
    elif re.search('^player#\d+$', hashkey):
        player = session.query(Player).filter_by(player_id=2).one()
    # else it is a tracked player
    else:
        # see if the player is already in the database
        # if not, create one and the hashkey along with it
        try:
            hashkey = session.query(Hashkey).filter_by(
                    hashkey=hashkey).one()
            player = session.query(Player).filter_by(
                    player_id=hashkey.player_id).one()
            log.debug("Found existing player {0} with hashkey {1}.".format(
                player.player_id, hashkey.hashkey))
        except:
            player = Player()

            if nick:
                player.nick = nick

            session.add(player)
            session.flush()
            hashkey = Hashkey(player_id=player.player_id, hashkey=hashkey)
            session.add(hashkey)
            log.debug("Created player {0} with hashkey {1}.".format(
                player.player_id, hashkey.hashkey))

    return player

def create_player_game_stat(session=None, player=None, 
        game=None, player_events=None):
    """
    Creates game statistics for a given player in a given game. Parameters:

    session - SQLAlchemy session factory
    player - Player record of the player who owns the stats
    game - Game record for the game to which the stats pertain
    player_events - dictionary for the actual stats that need to be transformed
    """

    # in here setup default values (e.g. if game type is CTF then
    # set kills=0, score=0, captures=0, pickups=0, fckills=0, etc
    # TODO: use game's create date here instead of now()
    pgstat = PlayerGameStat(create_dt=datetime.datetime.now())

    # set player id from player record
    pgstat.player_id = player.player_id

    #set game id from game record
    pgstat.game_id = game.game_id

    # all games have a score
    pgstat.score = 0

    if game.game_type_cd == 'dm':
        pgstat.kills = 0
        pgstat.deaths = 0
        pgstat.suicides = 0
    elif game.game_type_cd == 'ctf':
        pgstat.kills = 0
        pgstat.captures = 0
        pgstat.pickups = 0
        pgstat.drops = 0
        pgstat.returns = 0
        pgstat.carrier_frags = 0

    for (key,value) in player_events.items():
        if key == 'n': pgstat.nick = value
        if key == 't': pgstat.team = value
        if key == 'rank': pgstat.rank = value
        if key == 'alivetime': 
            pgstat.alivetime = datetime.timedelta(seconds=int(round(float(value))))
        if key == 'scoreboard-drops': pgstat.drops = value
        if key == 'scoreboard-returns': pgstat.returns = value
        if key == 'scoreboard-fckills': pgstat.carrier_frags = value
        if key == 'scoreboard-pickups': pgstat.pickups = value
        if key == 'scoreboard-caps': pgstat.captures = value
        if key == 'scoreboard-score': pgstat.score = value
        if key == 'scoreboard-deaths': pgstat.deaths = value
        if key == 'scoreboard-kills': pgstat.kills = value
        if key == 'scoreboard-suicides': pgstat.suicides = value

    # check to see if we had a name, and if 
    # not use the name from the player id
    if pgstat.nick == None:
        pgstat.nick = player.nick

    session.add(pgstat)
    session.flush()

    return pgstat


def create_player_weapon_stats(session=None, player=None, 
        game=None, pgstat=None, player_events=None):
    """
    Creates accuracy records for each weapon used by a given player in a
    given game. Parameters:

    session - SQLAlchemy session factory object
    player - Player record who owns the weapon stats
    game - Game record in which the stats were created
    pgstat - Corresponding PlayerGameStat record for these weapon stats
    player_events - dictionary containing the raw weapon values that need to be
        transformed
    """
    pwstats = []

    for (key,value) in player_events.items():
        matched = re.search("acc-(.*?)-cnt-fired", key)
        if matched:
            weapon_cd = matched.group(1)
            pwstat = PlayerWeaponStat()
            pwstat.player_id = player.player_id
            pwstat.game_id = game.game_id
            pwstat.player_game_stat_id = pgstat.player_game_stat_id
            pwstat.weapon_cd = weapon_cd

            if 'n' in player_events:
                pwstat.nick = player_events['n']
            else:
                pwstat.nick = player_events['P']

            if 'acc-' + weapon_cd + '-cnt-fired' in player_events:
                pwstat.fired = int(round(float(
                        player_events['acc-' + weapon_cd + '-cnt-fired'])))
            if 'acc-' + weapon_cd + '-fired' in player_events:
                pwstat.max = int(round(float(
                        player_events['acc-' + weapon_cd + '-fired'])))
            if 'acc-' + weapon_cd + '-cnt-hit' in player_events:
                pwstat.hit = int(round(float(
                        player_events['acc-' + weapon_cd + '-cnt-hit'])))
            if 'acc-' + weapon_cd + '-hit' in player_events:
                pwstat.actual = int(round(float(
                        player_events['acc-' + weapon_cd + '-hit'])))
            if 'acc-' + weapon_cd + '-frags' in player_events:
                pwstat.frags = int(round(float(
                        player_events['acc-' + weapon_cd + '-frags'])))

            session.add(pwstat)
            pwstats.append(pwstat)

    return pwstats


def parse_body(request):
    """
    Parses the POST request body for a stats submission
    """
    # storage vars for the request body
    game_meta = {}
    player_events = {}
    current_team = None
    players = []
    
    log.debug(request.body)

    for line in request.body.split('\n'):
        try:
            (key, value) = line.strip().split(' ', 1)
    
            if key in 'V' 'T' 'G' 'M' 'S' 'C' 'R' 'W':
                game_meta[key] = value

            if key == 'P':
                # if we were working on a player record already, append
                # it and work on a new one (only set team info)
                if len(player_events) != 0:
                    players.append(player_events)
                    player_events = {}
    
                player_events[key] = value

            if key == 'e':
                (subkey, subvalue) = value.split(' ', 1)
                player_events[subkey] = subvalue
            if key == 'n':
                player_events[key] = value
            if key == 't':
                player_events[key] = value
        except:
            # no key/value pair - move on to the next line
            pass
    
    # add the last player we were working on
    if len(player_events) > 0:
        players.append(player_events)

    return (game_meta, players)


def create_player_stats(session=None, player=None, game=None, 
        player_events=None):
    """
    Creates player game and weapon stats according to what type of player
    """
    if 'joins' in player_events and 'matches' in player_events\
            and 'scoreboardvalid' in player_events:
                pgstat = create_player_game_stat(session=session, 
                        player=player, game=game, player_events=player_events)
                if not re.search('^bot#\d+$', player_events['P']):
                        create_player_weapon_stats(session=session, 
                            player=player, game=game, pgstat=pgstat,
                            player_events=player_events)
    

def stats_submit(request):
    """
    Entry handler for POST stats submissions.
    """
    try:
        session = DBSession()

        (game_meta, players) = parse_body(request)  
    
        # verify required metadata is present
        if 'T' not in game_meta or\
            'G' not in game_meta or\
            'M' not in game_meta or\
            'S' not in game_meta:
            log.debug("Required game meta fields (T, G, M, or S) missing. "\
                    "Can't continue.")
            raise Exception("Required game meta fields (T, G, M, or S) missing.")
    
        has_real_players = False
        for player_events in players:
            if not player_events['P'].startswith('bot'):
                if 'joins' in player_events and 'matches' in player_events\
                    and 'scoreboardvalid' in player_events:
                    has_real_players = True

        if not has_real_players:
            raise Exception("No real players found. Stats ignored.")

        server = get_or_create_server(session=session, name=game_meta['S'])
        gmap = get_or_create_map(session=session, name=game_meta['M'])

        if 'W' in game_meta:
            winner = game_meta['W']
        else:
            winner = None

        game = create_game(session=session, 
                start_dt=datetime.datetime(
                    *time.gmtime(float(game_meta['T']))[:6]), 
                server_id=server.server_id, game_type_cd=game_meta['G'], 
                map_id=gmap.map_id, winner=winner)
    
        # find or create a record for each player
        # and add stats for each if they were present at the end
        # of the game
        for player_events in players:
            if 'n' in player_events:
                nick = player_events['n']
            else:
                nick = None

            player = get_or_create_player(session=session, 
                    hashkey=player_events['P'], nick=nick)
            log.debug('Creating stats for %s' % player_events['P'])
            create_player_stats(session=session, player=player, game=game, 
                    player_events=player_events)
    
        session.commit()
        log.debug('Success! Stats recorded.')
        return Response('200 OK')
    except Exception as e:
        session.rollback()
        raise e
