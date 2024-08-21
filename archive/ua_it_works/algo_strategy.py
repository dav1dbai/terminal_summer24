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
        self.friend_side = []
        self.enemy_side = []
        start,end = 13, 14
        for i in range (14):
            for j in range(start, end+1):
                self.friend_side.append([i,j])
            start-=1
            end+=1
        
        


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
        
        
        if game_state.turn_number > 1:
            sim = gamelib.Simulation(game_state)
            edges = game_state.game_map.get_edges()
            spawnable_edges = self.filter_blocked_locations(edges[2]+edges[3], game_state)
            location, structure_damage, damage_taken, damage_to_opponent = sim.best_attack_path(spawnable_edges, int(game_state.get_resources(0)[1]), self.config["unitInformation"][3]["shorthand"], 0)
            if self.to_attack(game_state,structure_damage, structure_damage, damage_to_opponent, int(game_state.get_resources(0)[1])):
                game_state.attempt_spawn(SCOUT, location, int(game_state.get_resources(0)[1]))
                
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        

        self.basic_layering(game_state)
        gamelib.debug_write(f"build stack: {game_state._build_stack}")    

        game_state.submit_turn()

    def to_attack(self, game_state, structure_damage, damage_to_opponent, points):
        if damage_to_opponent>=game_state.enemy_health or damage_to_opponent>=points*0.35 or points>=11:
            return True
        return False

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def basic_layering(self, game_state):
        turret_locations = [[4,12],[23,12],[10,12], [17,12]]
        wall_locations = [[0,13],[27,13],[23,13],[4,13]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_spawn(WALL, wall_locations)
        game_state.attempt_upgrade(turret_locations)
        game_state.attempt_upgrade(wall_locations)
        walls_2 = [[17,13],[10,13]]
        game_state.attempt_spawn(WALL, walls_2)

        for location in self.scored_on_locations:
            game_state.attempt_spawn(TURRET, [location[0], location[1]])
        supports = [[13,0], [14,0], [13,1], [14,1]]
        game_state.attempt_spawn(SUPPORT, supports)
        turrets_2 = [[2,12], [9,12], [18,12],[26,12]]
        
        game_state.attempt_upgrade(supports)
        for location in self.scored_on_locations:
            game_state.attempt_upgrade([location[0], location[1]])
        
        




    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

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
