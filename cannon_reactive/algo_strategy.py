import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = set()
        self.primary_turrets = [[4, 12], [9, 12], [17, 12], [23, 12]]
        self.secondary_turrets = [[5,12],[5,13],[16,13],[16,12]]
        self.game_map = gamelib.GameMap(self.config)

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place/restore basic defenses
        self.build_defences(game_state)

        # then, use points to add defenses where scored on
        self.build_reactive_defense(game_state)

        if game_state.turn_number % 2 == 0:
            gamelib.debug_write(game_state.MP)
            game_state.attempt_spawn(SCOUT, [13, 0], 1000)
            return

        #build support cannon
        self.build_support_cannon(game_state)
        #use residual points to upgrade defenses, increase support cannon
        self.upgrade_defenses(game_state)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        game_state.attempt_spawn(TURRET, self.primary_turrets)
        
        game_state.attempt_upgrade(self.primary_turrets)

    
    def build_reactive_defense(self, game_state):
        '''
        Build defenses where enemy scored
        '''
        for location in self.scored_on_locations:
            location = list(location)
            if self.game_map.in_arena_bounds(location):
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)
                gamelib.debug_write("spawning turret at location")
            elif game_state.contains_stationary_unit(location):
                location[1]+=1
                game_state.attempt_spawn(TURRET, location)
                

    def build_support_cannon(self, game_state):
        '''
        Build support tower to buff mobile units
        '''
        for y in range(2,6):
            game_state.attempt_spawn(SUPPORT, [13, y])
            game_state.attempt_spawn(SUPPORT, [14, y])

    def upgrade_defenses(self, game_state):
        #add secondar turrets
        game_state.attempt_spawn(TURRET, self.secondary_turrets)
        game_state.attempt_upgrade(self.secondary_turrets)
        #reinforce support cannon
        for x in range(13,24):
            y = x - 11
            game_state.attempt_spawn(SUPPORT, [x, y])

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = tuple(breach[0])
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.add(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()