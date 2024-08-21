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

        
        
    def best_attack_path(self, location_options, amount_of_troops, mobile_unit, player_index):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        gamelib.debug_write('getting best attack path')
        paths = [self.simulate_path(location, amount_of_troops, mobile_unit, player_index) for location in self.get_attack_options(self.copy_game, player_index)]
        # location = [13,0]
        # paths = [self.simulate_path(location, amount_of_troops, mobile_unit, player_index)]

        return sorted(paths, key = lambda x: (x[-1], x[0]))[-1][0]
        
    def simulate_path(self, location, amount_of_troops, unit_type, player_index):
        
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

        damage_afflicted, damage_inflicted, previous_move_direction = 0, 0, 0

        while not(path_finder.game_map[current[0]][current[1]].pathlength == 0) and len(self.copy_game.game_map[current])>0:

            turn = self.damage_calculations(current, 0, path_finder, location, end_points)
            damage_afflicted += turn['target_damage']
            damage_inflicted += turn['net_damage']
            if len(self.copy_game.game_map[current])>0:
                
                next_move = path_finder._choose_next_move(current, previous_move_direction, end_points)
                if current[0] == next_move[0]:
                    previous_move_direction = path_finder.VERTICAL
                else:
                    previous_move_direction = path_finder.HORIZONTAL
                self.move_units(current, next_move)
                current = next_move
        
        if len(self.copy_game.game_map[current])>0:
            turn = self.damage_calculations(current, 0, path_finder, location, end_points)
            damage_afflicted += turn['target_damage']
            damage_inflicted += turn['net_damage']

        damage_to_opponent_health = len(self.copy_game.game_map[current])
        self.copy_game = GameState(self.orig_game.config, self.orig_game.serialized_string)
        
        return (location, damage_afflicted, damage_inflicted, damage_to_opponent_health)
        

    def move_units(self, location_1, location_2):
        for unit in tuple(self.copy_game.game_map[location_1]):
            self.copy_game.game_map[location_2].append(unit)
            self.copy_game.game_map[location_1].pop(0)

    def damage_calculations(self, location, player_index, nav, spawn_location, end_points):
        print(f"running damage calcs on loc: {spawn_location}")
        print(len(self.copy_game.game_map[location]))
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

        while total_damage>0 and len(self.copy_game.game_map[location])>0:
            if self.copy_game.game_map[location][-1].health>total_damage:
                self.copy_game.game_map[location][-1].health -= total_damage
                break
            else:
                total_damage -= self.copy_game.game_map[location][-1].health
                self.copy_game.game_map[location].pop()
        if target:
            target.health-=target_damage
            if target.health<=0:
                self.copy_game.game_map[[target.x,target.y]].pop()
                nav.ideal_endpoints = nav._idealness_search(spawn_location, end_points)
                nav._validate(nav.ideal_endpoints, end_points)

        
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