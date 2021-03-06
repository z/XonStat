import pyramid_jinja2
import sqlahelper
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from xonstat.models import initialize_db
from xonstat.views import * 

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # setup the database engine
    engine = engine_from_config(settings, 'sqlalchemy.')
    sqlahelper.add_engine(engine)

    # initialize database structures
    initialize_db(engine)

    config = Configurator(settings=settings)

    config.add_renderer('.jinja2', pyramid_jinja2.renderer_factory)

    config.add_static_view('static', 'xonstat:static')

    # ROOT ROUTE
    config.add_route(name="main_index", pattern="/", view=main_index,
            renderer='main_index.mako') 

    # PLAYER ROUTES
    config.add_route(name="player_game_index_default", 
            pattern="/player/{player_id:\d+}/games", 
            view=player_game_index, renderer='player_game_index.mako') 

    config.add_route(name="player_game_index", 
            pattern="/player/{player_id:\d+}/games/page/{page:\d+}", 
            view=player_game_index, renderer='player_game_index.mako') 

    config.add_route(name="player_index_paged", 
            pattern="/players/page/{page:\d+}", view=player_index, 
            renderer='player_index.mako') 

    config.add_route(name="player_index", pattern="/players", view=player_index, 
            renderer='player_index.mako') 

    config.add_route(name="player_info", pattern="/player/{id:\d+}", view=player_info, 
            renderer='player_info.mako') 

    # GAME ROUTES
    config.add_route(name="game_index", pattern="/games", view=game_index, 
            renderer='game_index.mako') 

    config.add_route(name="game_index_paged", pattern="/games/page/{page:\d+}", 
            view=game_index, renderer='game_index.mako') 

    config.add_route(name="game_info", pattern="/game/{id:\d+}", view=game_info, 
            renderer='game_info.mako') 

    # SERVER ROUTES
    config.add_route(name="server_index_paged", 
            pattern="/servers/page/{page:\d+}", view=server_index, 
            renderer='server_index.mako') 

    config.add_route(name="server_index", pattern="/servers", view=server_index, 
            renderer='server_index.mako') 

    config.add_route(name="server_game_index", 
            pattern="/server/{server_id:\d+}/games/page/{page:\d+}", 
            view=server_game_index, renderer='server_game_index.mako') 

    config.add_route(name="server_info", pattern="/server/{id:\d+}", view=server_info, 
            renderer='server_info.mako') 

    # MAP ROUTES
    config.add_route(name="map_index_paged", 
            pattern="/maps/page/{page:\d+}", view=map_index, 
            renderer='map_index.mako') 

    config.add_route(name="map_index", pattern="/maps", view=map_index, 
            renderer='map_index.mako') 

    config.add_route(name="map_info", pattern="/map/{id:\d+}", view=map_info, 
            renderer='map_info.mako') 

    config.add_route(name="stats_submit", pattern="stats/submit", 
            view=stats_submit, renderer='index.jinja2') 

    return config.make_wsgi_app()
