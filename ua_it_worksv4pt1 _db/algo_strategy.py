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
        
        
        # OFFENSE
        attack = False
        supp_location = []

        if game_state.turn_number > 1:
            sim = gamelib.Simulation(game_state)
            edges = game_state.game_map.get_edges()
            spawnable_edges = self.filter_blocked_locations(edges[2]+edges[3], game_state)
            location, structure_damage, damage_taken, damage_to_opponent = sim.best_attack_path(spawnable_edges, int(game_state.get_resources(0)[1]), self.config["unitInformation"][3]["shorthand"], 0)
            if self.to_attack(game_state,structure_damage,damage_to_opponent, int(game_state.get_resources(0)[1])):
                resources_avail = int(game_state.get_resources(0)[1])
                game_state.attempt_spawn(SCOUT, location, resources_avail) 
                attack = True
                supp_location = location
        else:
            game_state.attempt_spawn(SCOUT, [[27,13]], 10)
            game_state.attempt_spawn(SUPPORT, [[26,12]])
            game_state.attempt_remove([[26,12]])
        # DEFENSE STRATEGY
        self.strategy(game_state, attack, supp_location)
        gamelib.debug_write(f"build stack: {game_state._build_stack}")
        self.scored_on_locations = []
        game_state.submit_turn()

    def to_attack(self, game_state, structure_damage, damage_to_opponent, points):
        # check win condition,
        if damage_to_opponent>=game_state.enemy_health or damage_to_opponent>=points*0.325 or points>=14:       # PLAY AROUND WITH THIS OFFENSE
            return True
        return False

    def add_support(self, game_state, loc):
        
        # @DAVID
        # IMPROVE SO THAT if above 7 y, just upgrade one turret instead of having two
        support_loc = None
        for i in range(-2, 2, 1):
            for j in range(-2, 2, 1):
                support_loc = [loc[0] - i, loc[1] - j]
                if not game_state.contains_stationary_unit(support_loc):
                    break

        game_state.attempt_spawn(SUPPORT, support_loc)
        # only if above y=7: game_state.attempt_upgrade(support_loc)
        game_state.attempt_remove(support_loc)

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def strategy(self, game_state, attack, location):
        """
        """
        
        # @DAVID these are NOT reactive
        # self.start_defenses(game_state)
        self.improved_defense(game_state, attack, location)

        # @DAVID reactive defenses
        self.reactive_defenses(game_state)

        # @DAVID building upon
        self.build_up_defenses(game_state)

        
    def improved_defense(self, game_state, attack, location):
        # clusters
        left = [[4, 13], [5, 13], [3, 13], [6, 13]]
        middle = [[13, 13], [13, 12], [14, 13], [14, 12]]
        right = [[23, 13], [22, 13], [24, 13], [25, 13]]

        priority_one = []
        priority_one.extend(left[:2])
        priority_one.extend(middle[:1])
        priority_one.extend(right[:2])

        game_state.attempt_spawn(TURRET, priority_one)
        game_state.attempt_upgrade(priority_one)

        # test pushing support here
        if attack:
            # ADDS SUPPORT FOR OFFENSE
            self.add_support(game_state, location)
            # add second support
            if game_state.turn_number > 15:
                self.add_support(game_state, location)
                
        priority_two = []
        priority_two.extend([middle[1], left[2], right[2], middle[2], middle[3], left[3], right[3]])
        
        game_state.attempt_spawn(TURRET, priority_two)
        game_state.attempt_upgrade(priority_two)



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
        wall_locs = [[4, 13], [17, 13]]

        game_state.attempt_spawn(TURRET, turret_locs)
        game_state.attempt_upgrade(turret_locs)
        
        game_state.attempt_spawn(WALL, wall_locs)
        game_state.attempt_upgrade(wall_locs)
        

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

    def reactive_defenses(self, game_state):
        
        gamelib.debug_write("reactive defenses")
        for location in self.scored_on_locations:
            if game_state.get_resource(SP) < 3:
                break
            for i in range(5):
                if game_state.attempt_spawn(TURRET,location):
                    break
                elif location[0] < 13 and location[0] >= 0:
                    location[0] += 1
                elif location[0] <= 27 and location[0] >= 13:
                    location[0] -= 1
                else:
                    break   
            game_state.attempt_upgrade(location)
        
        # get all possible enemy spawn locs
        enemy_spawns = []
        enemy_spawns.extend(game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT))
        enemy_spawns.extend(game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT))
        enemy_spawns = self.filter_blocked_locations(enemy_spawns, game_state)

        
        # find most likely spawn loc + path
        likely_location = self.least_damage_spawn_location_enemy(game_state, enemy_spawns)
        enemy_end_path = game_state.find_path_to_edge(likely_location)
        
        # find x_avg that intersects with y=12 (our turret row)
        x_list = [p[0] for p in enemy_end_path if p[1] == 12]

        if not x_list:
            return None     # no intersection path possible, no turret to place
         
        # avg the x, y traversal where interceptor can (probably) fight off
        avg_x = sum(x_list)//len(x_list)

        gamelib.debug_write([avg_x,12])
        # @DAVID try to build turret spawner preference on the side of avg_x
        for i in range(5):
            gamelib.debug_write("attempting spawn for predicted attac")
            if game_state.attempt_spawn(TURRET,[avg_x,12]):
                break
            elif avg_x < 13 and avg_x > 0:
                avg_x -= 1
            elif avg_x <= 27 and avg_x >= 13:
                avg_x += 1
            else:
                break
        
        return True # or smth idk 

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