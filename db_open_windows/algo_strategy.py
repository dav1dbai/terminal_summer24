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

        # ADDED HERE TO SEND MOBILE UNITS AFTER WALLS BUILT
        self.PREV_WALLS_BUILT = False
        self.PUSH_NEXT = True

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
        self.opponent_spawns = []
        self.predicted_opponent_spawns = []
        # self.opponent_MP = 0
        self.opponent_freq = []
        self.current_turn = 0
        self.logged = True

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
        self.logged = True
        # # <<<< DEFENSE PRIORITY LIST >>>>
        # # 1. (re)build basic structs
        # self.starter_defenses(game_state)
        # # 2. (re)build extended structs
        # self.build_up_defenses(game_state)
        # # 3. (if resources) confuse opponents given prediction
        # build_walls = self.predict_opponent_attack(game_state)
        # if build_walls and game_state.get_resources(0)[0] > 12:
        #     self.build_blocking_walls(game_state)
        # self.PREV_WALLS_BUILT = build_walls
        # # 4. add vertical turrets in the middle
        # self.end_game_defenses(game_state)
        
        # if game_state.turn_number % 3 == 0:    # WORK HERE if build walls, push right after
        #     if not self.PREV_WALLS_BUILT or self.PUSH_NEXT:
        #         if game_state.turn_number % 2 == 0:
        #             game_state.attempt_spawn(SCOUT, [13, 0], 1000)
        #         else:
        #             game_state.attempt_spawn(SCOUT, [14, 0], 1000)
        #         self.PUSH_NEXT = False
        #     else:
        #         self.PUSH_NEXT = True

        #flow
        #rebuild turrets > this is priority
        #restore walls
        #determine next attack, and mark walls for deletion
        #if remaining points, add reinforcement turrets


    def predict_opponent_attack(self, game_state):
        #get latest spawn info
        if self.opponent_spawns:
            last_spawns = self.opponent_spawns[-1]
            # just check scouts for now
            scouts_list = last_spawns.get('scouts')
            # can adjust threshold for trigger later
            self.opponent_freq.append(len(scouts_list))
        else:
            self.opponent_freq.append(0)
        gamelib.debug_write(self.opponent_freq)
        
        spawn_turns = [i for i, spawn in enumerate(self.opponent_freq) if spawn > 0]
        #gamelib.debug_write(spawn_turns)
        if len(spawn_turns) > 1:
            intervals = [spawn_turns[i+1] - spawn_turns[i] for i in range(len(spawn_turns)-1)]
            avg_interval = sum(intervals) / len(intervals)
            next_spawn_turn = spawn_turns[-1] + round(avg_interval)
            gamelib.debug_write(next_spawn_turn)
            gamelib.debug_write(self.current_turn)
            if self.current_turn + 2 == next_spawn_turn:
                return True
        return False
    
    
    def calculate_pred_spawns(self, game_state):  
        # calculate opponent theoretical spawns, for last game (before deploy phase of turn that this is for)
        opponent_all_edges = game_state.game_map.get_edge_locations(0) + game_state.game_map.get_edge_locations(1)
        #gamelib.debug_write(opponent_all_edges)
        opponent_potential_spawns = self.filter_blocked_locations(opponent_all_edges, game_state)
        # get n best possible spawns
        opponent_best_spawns = []
        for i in range(2):
            location = self.least_damage_spawn_location_enemy(game_state,opponent_potential_spawns)
            opponent_best_spawns.append(location)
            opponent_potential_spawns.remove(location)
        self.predicted_opponent_spawns.append(opponent_best_spawns)

       #once per turn
        gamelib.debug_write("predicted opponent spawns")
        gamelib.debug_write(self.predicted_opponent_spawns)
        gamelib.debug_write("actual opponent spawns")
        gamelib.debug_write(self.opponent_spawns)
    
    def build_blocking_walls(self, game_state):
        gamelib.debug_write("building blocking walls")
        wall_locs = [[0,13],[27,13],[1,13],[26,13],[2,13],[25,13],[3,13],[24,13]]   # could be improved, if turrets > 1 only need 3 each side
        game_state.attempt_spawn(WALL, wall_locs)
        game_state.attempt_remove(wall_locs)
    
    def starter_defenses(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
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

    # def upgrade_defences(self,game_state):
    #     turret_locs = [[3, 12], [11, 12], [24, 12], [5, 12], [16, 12], [9, 12], [18, 12], [22, 12]]
    #     for turr in turret_locs:
    #         gamelib.debug_write(game_state.get_resources)
    #         if game_state.get_resources(0)[0] < 16:
    #             break
    #         game_state.attempt_spawn(TURRET, [turr])
    #         game_state.attempt_upgrade([turr])
    
    def build_up_defenses(self, game_state):
        turret_locs = [[3, 12], [24, 12], [5, 12], [9, 12], [18, 12], [22, 12]]
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

    def end_game_defenses(self, game_state):
        turret_locs = [[9, 11], [18, 11], [4, 11], [23, 11]]

        game_state.attempt_spawn(TURRET, turret_locs)
        game_state.attempt_upgrade(turret_locs)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]
    
    def least_damage_spawn_location_enemy(self,game_state,location_options):
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of ally turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

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
        turninfo = state["turnInfo"]
        # check deploy phase to identify spawn locations
        if self.logged:
            opponent_stats = state["p2Units"]
            opponent_units = {
                "scouts": opponent_stats[3],
                "demolishers" : opponent_stats[4],
                "interceptors": opponent_stats[5],
            }
            #gamelib.debug_write("turn {}".format(turnInfo[1]))
            #gamelib.debug_write("actual opponent spawns")
            self.opponent_spawns.append(opponent_units)

            self.current_turn = turninfo[1]

            self.logged = False
        
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                #gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                #gamelib.debug_write("All locations: {}".format(self.scored_on_locations))    


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()