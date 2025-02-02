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
        
        
        self.strategy(game_state)
        if game_state.turn_number > 1:
            sim = gamelib.Simulation(game_state)
            edges = game_state.game_map.get_edges()
            spawnable_edges = self.filter_blocked_locations(edges[2]+edges[3], game_state)
            location, structure_damage, damage_taken, damage_to_opponent = sim.best_attack_path(spawnable_edges, int(game_state.get_resources(0)[1]), self.config["unitInformation"][3]["shorthand"], 0)
            if self.to_attack(game_state,structure_damage,damage_to_opponent, int(game_state.get_resources(0)[1])):
                game_state.attempt_spawn(SCOUT, location, int(game_state.get_resources(0)[1]))
            
            interceptor_loc = self.interceptor_defense(game_state)
            if interceptor_loc:
                game_state.attempt_spawn(SCOUT, location, int(game_state.get_resources(0)[1]))
                gamelib.debug_write(f"interceptor: {interceptor_loc}")

        gamelib.debug_write(f"build stack: {game_state._build_stack}")

        

        game_state.submit_turn()

    def to_attack(self, game_state, structure_damage, damage_to_opponent, points):
        if damage_to_opponent>=game_state.enemy_health or damage_to_opponent>=points*0.4 or points>=11:
            return True
        return False

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def strategy(self, game_state):
        """
        """
        
        
        self.start_defenses(game_state)
        self.build_up_defenses(game_state)



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
            game_state.attempt_spawn(TURRET, [pair[0], pair[1]])
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

    def interceptor_defense(self, game_state):
        
        # get all possible enemy spawn locs
        enemy_spawns = []
        enemy_spawns.extend(game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT))
        enemy_spawns.extend(game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT))
        enemy_spawns = self.filter_blocked_locations(enemy_spawns, game_state)

        
        # find most likely spawn loc + path
        likely_location = self.least_damage_spawn_location_enemy(game_state, enemy_spawns)
        enemy_end_path = game_state.find_path_to_edge(likely_location)
        
        x_list = [p[0] for p in enemy_end_path if p[1] in [8, 9, 10, 11, 12]]
        y_list = [p[1] for p in enemy_end_path if p[1] in [8, 9, 10, 11, 12]]

        if not x_list:
            return None     # no intersection path possible
         
        # avg the x, y traversal where interceptor can (probably) fight off
        avg_x = sum(x_list)//len(x_list)
        avg_y = sum(y_list)//len(y_list)
        gamelib.debug_write(f"avg_x, avg_y: {avg_x}, {avg_y}")

        # find start for interceptor to reach avg x, avg y
        hypothetical_path_to_enemy = game_state.find_path_to_edge([avg_x, avg_y])

        gamelib.debug_write(f"add inter. at[0]: {hypothetical_path_to_enemy[0]}") 
        
        return hypothetical_path_to_enemy[0]
    
    def least_damage_spawn_location_enemy(self,game_state,location_options):
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path:
                for path_location in path:
                    # Get number of ally turrets that can attack each location and multiply by turret damage
                    damage += sum([unit.damage_i for unit in game_state.get_attackers(path_location, 1)])
                    # damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]


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
