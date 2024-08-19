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
        self.primary_turrets = [[4, 12], [9, 12], [17, 12], [23, 12]]
        self.secondary_turrets = [[5,12],[5,13],[16,13],[16,12]]

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
        self.scored_on_locations = []

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

        self.strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def strategy(self, game_state):
        """
        """
        
        
        self.start_defenses(game_state)
        self.build_up_defenses(game_state)


        # spawn left, right
        if (game_state.turn_number - 1) % 3 == 0:
            if game_state.turn_number % 2 == 0:
                game_state.attempt_spawn(SCOUT, [[14,0]], 1000)
            else:
                game_state.attempt_spawn(SCOUT, [[13,0]], 1000)


    def start_defenses(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        turret_locs = [[4, 12], [10, 12], [17, 12], [23, 12]]
        support_locs = [[13, 2]]
        wall_locs = [[4, 13], [17, 13]]

        game_state.attempt_spawn(TURRET, turret_locs)
        game_state.attempt_upgrade(turret_locs)
        
        game_state.attempt_spawn(WALL, wall_locs)
        game_state.attempt_upgrade(wall_locs)
        
        game_state.attempt_spawn(SUPPORT, support_locs)

        wall_after = [[10, 13], [23, 13]]
        game_state.attempt_spawn(WALL, wall_after)
        game_state.attempt_upgrade(wall_after)

    def build_up_defenses(self, game_state):
        turret_locs = [[3, 12], [11, 12], [24, 12], [5, 12], [16, 12], [9, 12], [18, 12], [22, 12]]
        wall_locs = [[3, 13], [24, 13], [9, 13], [18, 13]]

        wall_count = 0
        for turr in turret_locs:
            game_state.attempt_spawn(TURRET, [turr])
            game_state.attempt_upgrade([turr])

            if wall_count < len(wall_locs)-1 and wall_locs[wall_count][0] == turr[0]:
                game_state.attempt_spawn(WALL, [wall_locs[wall_count]])
                game_state.attempt_upgrade([wall_locs[wall_count]])
                wall_count += 1
        
        left_edge_walls = [[0,13], [1,13], [2,13]]
        right_edge_walls = [[27,13], [26,13], [25,13]]

        for pair in zip(left_edge_walls, right_edge_walls):
            game_state.attempt_spawn(WALL, [pair[0], pair[1]])
            game_state.attempt_upgrade([pair[0], pair[1]])



    def build_support_cannon(self, game_state):
        '''
        Build support diagonal to buff mobile units
        '''
        for x in range(13,24):
            y = x - 12
            game_state.attempt_spawn(SUPPORT, [x, y])

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
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()