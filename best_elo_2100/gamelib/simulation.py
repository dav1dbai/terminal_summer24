import math
import json
import sys

import copy

import gamelib
from .game_map import GameMap
from .navigation import ShortestPathFinder
from .game_state import GameState
from .unit import GameUnit

class Simulation():

    def __init__(self, game_state):
        self.orig_game = game_state
        self.copy_game = GameState(self.orig_game.config, self.orig_game.serialized_string)
        self.supports = set()
        self.opponent_build_stack = []

        
    def update_placements(self):

        UPGRADE = self.orig_game.config["unitInformation"][7]["shorthand"]
        for name, x, y in self.orig_game._build_stack:
            if name == UPGRADE:
                self.copy_game.game_map[[x,y]][0].upgrade()
            else:
                self.copy_game.game_map.add_unit(name, [x,y], 0)


    def best_attack_path(self, location_options, amount_of_troops, mobile_unit, player_index):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        gamelib.debug_write(f"PREDS: {self._build_stack_calc()}")
        gamelib.debug_write(f"OPP BUILD STACK: {self.opponent_build_stack}")
        
        paths = [self.simulate_path(location, amount_of_troops, mobile_unit, player_index) for location in self.get_attack_options(self.copy_game, player_index)]

        return sorted(paths, key=lambda x: (x[2], -x[1]))[0]
        
    def simulate_path(self, location, amount_of_troops, unit_type, player_index):
        self.update_placements()
        path_finder = ShortestPathFinder()
        path_finder.initialize_map(self.copy_game)
        target_edge = self.copy_game.get_target_edge(location)
        end_points = self.copy_game.game_map.get_edge_locations(target_edge)
        path_finder.ideal_endpoints = path_finder._idealness_search(location, end_points)
        path_finder._validate(path_finder.ideal_endpoints, end_points)

        for _ in range(amount_of_troops):
            self.copy_game.game_map.add_unit(unit_type, location, player_index)
        current = location
        self.supports = set()

        damage_given, damage_taken, previous_move_direction = 0, 0, 0

        while (not path_finder.game_map[current[0]][current[1]].pathlength == 0) and len(self.copy_game.game_map[current])>0:
            next_move = path_finder._choose_next_move(current, previous_move_direction, end_points)
            if current[0] == next_move[0]:
                previous_move_direction = path_finder.VERTICAL
            else:
                previous_move_direction = path_finder.HORIZONTAL
            # change 1 here:
            self.move_units(current, next_move)
            current = next_move
            
            turn = self.damage_calculations(current, 0, path_finder, location, end_points)
            damage_given += turn['target_damage']
            damage_taken += turn['net_damage']


        damage_to_opponent_health = len(self.copy_game.game_map[current])
        self.copy_game = GameState(self.orig_game.config, self.orig_game.serialized_string)
        
        return (location, damage_given, damage_taken, damage_to_opponent_health)
        

    def move_units(self, location_1, location_2):
        for unit in tuple(self.copy_game.game_map[location_1]):
            self.copy_game.game_map[location_2].append(unit)
            self.copy_game.game_map[location_1].pop(0)
            unit.x,unit.y = location_2[0], location_2[1]

    def damage_calculations(self, location, player_index, nav, spawn_location, end_points):
        supports = self.copy_game.get_shielders(location, player_index)
        attackers = self.copy_game.get_attackers(location, player_index)
        net_damage = 0 
        for support in supports:
            if (support.x, support.y) not in self.supports:
                for unit in self.copy_game.game_map[location]:
                    unit.health+=(support.shieldPerUnit + support.shieldBonusPerY*support.y)
                    net_damage -= (support.shieldPerUnit + support.shieldBonusPerY*support.y)
                self.supports.add((support.x, support.y))

        total_damage = sum([unit.damage_i for unit in attackers])
        net_damage+=total_damage

        target = self.copy_game.get_target(self.copy_game.game_map[location][0])
        target_damage = self.copy_game.game_map[location][0].damage_f * len(self.copy_game.game_map[location])

        
        while target and target_damage>0:
            # change 2 here:
            if target.health > target_damage:
                target.health-=target_damage
                target_damage = 0
            else:
                target_damage -= target.health
                self.copy_game.game_map[[target.x, target.y]].pop()
                target = self.copy_game.get_target(self.copy_game.game_map[location][0])
            # COMMENTED OUT HERE
            # nav.ideal_endpoints = nav._idealness_search(spawn_location, end_points)
            # nav._validate(nav.ideal_endpoints, end_points)

        # change 3: moved after while above
        while total_damage>0 and len(self.copy_game.game_map[location])>0:
            if self.copy_game.game_map[location][-1].health>total_damage:
                self.copy_game.game_map[location][-1].health -= total_damage
                break
            else:
                total_damage -= self.copy_game.game_map[location][-1].health
                self.copy_game.game_map[location].pop()

        
        return {'net_damage': net_damage, 'target_damage': target_damage}

    


    def get_attack_options(self,game_state, player_index):
        """returns locations where mobile units can be
        spawned for given player"""
        edges = game_state.game_map.get_edges()
        if player_index == 1:
            spawn_locations = edges[0]+edges[1]
        else:
            spawn_locations = edges[2]+ edges[3]
        return self.filter_blocked_locations(spawn_locations, self.copy_game)

    def get_opponent_edges(self,game_state, player_index):
        """returns locations where mobile units can be
        spawned for given player"""
        edges = game_state.game_map.get_edges()
        if player_index == 0:
            spawn_locations = edges[0]+edges[1]
        else:
            spawn_locations = edges[2]+ edges[3]
        return self.filter_blocked_locations(spawn_locations, self.copy_game)

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


    def _build_stack_calc(self):
        """
        Return: Updates opponent build stack and returns expected locations of units and what they are.
        
        Examples:
            example self.opponent_build_stack:
                [[0, [4, 14], False],
                [2, [2, 14], True],
                [2, [2, 15], False],
                [2, [3, 14], True],
                [2, [3, 15], True],
                [2, [0, 14], True]]
                # unittype, [x, y], is_upgraded
                # 0=wall, 1=support, 2=turret

            return:
                [[2, [2, 14], True]]
        """
        
        # >>>> Updating Build Stack <<<<<
        game_string = json.loads(self.orig_game.serialized_string)

        p2units = game_string["p2Units"]
        current_units_list = []
        for index_type, struct in enumerate(p2units[:3]):
            for s in struct:
                out = []
                out.append(index_type) # 0=wall, 1=support, 2=turret
                out.append([s[0], s[1]])
                
                # this may be a bug!! index out of errror
                out.append(out[1] in p2units[6]) #6=upgraded locs
                current_units_list.append(out)

        for s in current_units_list:
            if s not in self.opponent_build_stack:
                self.opponent_build_stack.append(s)

        # >>>> Getting Turn Death Stack <<<<<
        turn_death_list = []
        for d in game_string["events"]["death"]:    # check game string for death events
            loc = d[0]
            unittype = d[1]
            intentional_removal = d[-1]
            if not intentional_removal and unittype < 3 and [unittype, loc] not in turn_death_list: # 0, 1, 2
                turn_death_list.append([unittype, loc])

        death = game_string["events"]["death"]
        gamelib.debug_write(f"game_string: {death}")

        # >>>> Predicting <<<<<
        resources_available = int(self.orig_game.get_resources(1)[1])
        preds = []
            
        for build in self.opponent_build_stack:
            
            # if [unittype, location] is in death stack, that will likely be placed!
            if [build[0], build[1]] in turn_death_list:
                cost = 0

                if build[0] == 0:   # wall
                    if build[2] and resources_available > 4: 
                        cost += 4   # upgraded wall
                        preds.append(build)
                    elif resources_available > 2:
                        preds.append(build)
                
                elif build[0] == 1: # support
                    if build[2] and resources_available > 8:
                        cost += 8   # upgraded support
                        preds.append(build)
                    elif resources_available > 4:
                        cost += 4
                        preds.append(build)
                
                else: #turret
                    if build[2] and resources_available > 8:
                        cost += 8
                        preds.append(build)
                    elif resources_available > 3:
                        cost += 3
                        preds.append(build)
                
                resources_available -= cost # REMOVE cost from resources available
            
                turn_death_list.remove([build[0], build[1]])

            if resources_available < 2 or not(turn_death_list):
                break

        return preds