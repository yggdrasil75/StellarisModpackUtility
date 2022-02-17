# @author: FirePrince
# @version: 3.3.b
# @revision: 2022/02/08
# @thanks: OldEnt for detailed rundowns.
# @forum: https://forum.paradoxplaza.com/forum/threads/1491289/
# @ToDo: full path mod folder

# ============== Import libs ===============
import os  # io for high level usage
import glob
import re

# from pathlib import Path
# import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# ============== Initialize global parameter/variables ===============
only_warning = False # True/False optional (if True, implies code_cosmetic = False)
code_cosmetic = False # True/False optional (only if only_warning = False)
only_actual = True # speedup search (from previous relevant) to actual version

stellaris_version = '3.3.0'
mod_outpath = ''

# mod_path = os.path.dirname(os.getcwd())
mod_path = os.path.expanduser('~') + '/Documents/Paradox Interactive/Stellaris/mod'

# if not sys.version_info.major == 3 and sys.version_info.minor >= 6:
#     print("Python 3.6 or higher is required.")
#     print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
#     sys.exit(1)

# For performance reason option
# 3.3 TODO soldier_job_check_trigger
if only_actual:
    removedTargets = [
        # "",
        ("common\\buildings", r"\sbuilding(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow)\s*="), # replaced buildings ai
        [r"\bnum_\w+\s*[<=>]+\s*[a-z]+[\s}]", 'no scope alone'], #  [^\d{$@] too rare (could also be auto fixed)
        [r"\n\s+NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}", 'can be merged to NOR if not in an OR'], #  [^\d{$@] too rare (could also be auto fixed)
    ]
    targets3 = {
        r"\s+building(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow)\s*=\s*(?:yes|no)\n?": ("common\\buildings", ''),
        r"\bGFX_ship_part_auto_repair": (["common\\component_sets", "common\\component_templates"], 'GFX_ship_part_ship_part_nanite_repair_system'), # because icons.gfx
        r"\bcountry_election_influence_cost_mult": ("common\\governments", 'country_election_cost_mult'),
        r"\bhas_civic\s*=\s*civic_reanimated_armies": 'is_reanimator = yes',
        # r"^(?:\t\t| {4,8})value\s*=": ("common\\ethics", 'base ='), maybe too cheap
    }
    targets4 = {
        r"(?:random_weight|pop_attraction(_tag)?|country_attraction)\s+value\s*=": [r"\bvalue\b", ("common\\ethics", 'base')],
        #r"\n\s+NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}": [r"([\t ]+)NO[TR]\s*=\s*\{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR]\s*=\s*\{\s*([^{}#\r\n]+)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"], not valid if in OR
        r"\bany_\w+\s*=\s*\{[^{}]+?\bcount\s*[<=>]+\s*[^{}\s]+\s+[^{}]*\}": [r"\bany_(\w+)\s*=\s*\{\s*(?:([^{}]+?)\s+(\bcount\s*[<=>]+\s*[^{}\s]+)|(\bcount\s*[<=>]+\s*[^{}\s]+)\s+([^{}]*))\s+\}", r"count_\1 = { limit = { \2\5 } \3\4 }"], # too rare!? only simple supported TODO
    }
else:
    # >= 3.0.*
    removedTargets = [
        """== 3.1 Quick stats ==
        6 effects removed/renamed.
        8 triggers removed/renamed.
        426 modifiers removed/renamed.
        1 scope removed.
        """
        # This are only warnings, commands which cannot be easily replaced.
        # Format: tuple is with folder (folder, regexp/list); list is with a specific message [regexp, msg]
        # 3.2
        r"\sslot\s*=\s*0", # \sset_starbase_module\s*=\s*\{ now starts with 1
        [r"[^# \t]\s+is_planet_class\s*=\s*pc_ringworld_habitable", 'could possibly be replaced with "is_ringworld = yes"'], # ,
        # r"\sadd_tech_progress_effect\s*=\s*", # replaced with add_tech_progress
        # r"\sgive_scaled_tech_bonus_effect\s*=\s*", # replaced with add_monthly_resource_mult
        ("common\\districts", r"\sdistricts_build_district\b"), # scripted trigger
        ("common\\pop_jobs", r"\s(drone|worker|specialist|ruler)_job_check_trigger\b"), # scripted trigger

        # 3.1
        [r"\b(any|every|random)_(research|mining)_station\b", 'use just mining_station/research_station instead'], # = 2 trigger & 4 effects
        [r"\sobservation_outpost\s*=\s*\{\s*limit", 'is now a scope (from planet) rather than a trigger/effect'],
        r"\spop_can_live_on_planet\b", # r"\1can_live_on_planet", needs planet target
        r"\scount_armies\b", # (scope split: depending on planet/country)
        (["common\\bombardment_stances", "common\\ship_sizes"], [r"^\s+icon_frame\s*=\s*\d+", '"icon_frame" now only used for starbases']), # [6-9]  # Value of 2 or more means it shows up on the galaxy map, 1-5 denote which icon it uses on starbase sprite sheets (e.g. gfx/interface/icons/starbase_ship_sizes.dds)

        # PRE TEST
        # r"\sspaceport\W", # scope replace?
        # r"\shas_any_tradition_unlocked\W", # replace?
        # r"\smodifier\s*=\s*\{\s*mult", # => factor
        # r"\s+count_diplo_ties",
        # r"\s+has_non_swapped_tradition",
        # r"\s+has_swapped_tradition",
        r"\swhich\s*=\s*\"?\w+\"?\s+value\s*[<=>]\s*\{\s*scope\s*=", # var from 3.0
        # re.compile(r"\s+which\s*=\s*\"?\w+\"?\s+value\s*[<=>]\s*(prev|from|root|event_target:[^\.\s]+)+\s*\}", re.I), # var from 3.0

        # < 3.0
        r"\sproduced_energy\b",
        r"\s(ship|army|colony|station)_maintenance\b",
        r"\s(construction|trade|federation)_expenses\b",
        r"\shas_(population|migration)_control\s*=\s*(yes|no)",
        r"\s(any|every|random)_planet\b", # split in owner and galaxy and system scope
        r"\s(any|every|random)_ship\b", # split in owner and galaxy and system scope
        # < 2.0
        r"\scan_support_spaceport\s*=\s*(yes|no)",
        # 3.3
        ("common\\buildings", r"\sbuilding(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow)\s*="), # replaced buildings ai
        # [r"\bnum_\w+\s*[<=>]+\s*[a-z]+[\s}]", 'no scope alone'], #  [^\d{$@] too rare
    ]

    # targets2 = {
    #     r"MACHINE_species_trait_points_add = \d" : ["MACHINE_species_trait_points_add ="," ROBOT_species_trait_points_add = ",""],
    #     r"job_replicator_add = \d":["if = {limit = {has_authority = auth_machine_intelligence} job_replicator_add = ", "} if = {limit = {has_country_flag = synthetic_empire} job_roboticist_add = ","}"]
    # }

    targets3 = {
        ### >= 3.0.* (only one-liner)
        r"\b(first_contact_)attack_not_allowed": r"\1cautious",
        r"\bsurveyed\s*=\s*\{": r"set_surveyed = {",
        r"(\s+)set_surveyed\s*=\s*(yes|no)": r"\1surveyed = \2",
        r"has_completed_special_project\s+": "has_completed_special_project_in_log ",
        r"has_failed_special_project\s+": "has_failed_special_project_in_log ",
        r"species\s*=\s*last_created(\s)": r"species = last_created_species\1",
        r"owner\s*=\s*last_created(\s)": r"owner = last_created_country\1",
        r"(\s(?:any|every|random))_pop\s*=": r"\1_owned_pop =",
        r"(\s(?:any|every|random))_planet\s*=": r"\1_system_planet =", # _galaxy_planet
        r"(\s(?:any|every|random))_ship\s*=": r"\1_fleet_in_system =", # _galaxy_fleet
        r"(\s(?:any|every|random|count))_sector\s*=": r"\1_owned_sector =", # _galaxy_sector
        r"(\s(?:any|every|random))_war_(attacker|defender)\s*=": r"\1_\2 =",
        r"(\s(?:any|every|random|count))_recruited_leader\s*=": r"\1_owned_leader =",
        r"count_planets\s*": "count_system_planet  ", # count_galaxy_planet
        r"count_ships\s*": "count_fleet_in_system ", # count_galaxy_fleet
        r"count(_owned)?_pops\s*": "count_owned_pop ",
        r"count_(owned|fleet)_ships\s*": "count_owned_ship ", # 2.7
        # "any_ship_in_system": "any_fleet_in_system", # works only sure for single size fleets
        r"spawn_megastructure\s*=\s*\{([^{}#]+)location\s*=": r"spawn_megastructure = {\1planet =",
        r"\s+planet\s*=\s*(solar_system|planet)[\s\n\r]*": "",  # REMOVE
        r"any_system_within_border\s*=\s*\{\s*any_system_planet\s*=": "any_planet_within_border =",
        r"is_country_type\s*=\s*default\s+has_monthly_income\s*=\s*\{\s*resource = (\w+) value <=? \d": r"no_resource_for_component = { RESOURCE = \1",
        r"([^\._])(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*([\w\._:]+)\s*\}": r"\1is_owned_by = \2",
        r"(\s+)is_(?:country|same_value)\s*=\s*([\w\._:]+\.(?:space_)?owner)": r"\1is_same_empire = \2",
        r"(\s+)exists\s*=\s*(solar_system|planet)\.(?:space_)?owner": r"\1has_owner = yes",
        # code opts/cosmetic only
        r"(\s+)NOT\s*=\s*\{\s*([^\s]+)\s*=\s*yes\s*\}": r"\1\2 = no",
        r"(\s+)any_system_planet\s*=\s*\{\s*is_capital\s*=\s*(yes|no)\s*\}": r"\1is_capital_system = \2",
        r"(\s+has_(?:population|migration)_control)\s*=\s*(yes|no)": r"\1 = { value = \2 country = prev.owner }", # NOT SURE

        ## Since Megacorp removed: change_species_characteristics was false documented until 3.2
        r"[\s#]+(pops_can_(be_colonizers|migrate|reproduce|join_factions|be_slaves)|can_generate_leaders|pops_have_happiness|pops_auto_growth|pop_maintenance)\s*=\s*(yes|no)\s*": "",
        ### somewhat older
        r"(\s+)ship_upkeep_mult\s*=": r"\1ships_upkeep_mult =",
        r"\b(contact_rule\s*=\s*)script_only": ("common\\country_types", r"\1on_action_only"),
        r"\b(any|every|random)_(research|mining)_station\b": r"\2_station",
        r"(\s+)add_(energy|unity|food|minerals|influence|alloys|consumer_goods|exotic_gases|volatile_motes|rare_crystals|sr_living_metal|sr_dark_matter|sr_zro|(?:physics|society|engineering(?:_research)))\s*=\s*(\d+|@\w+)": r"\1add_resource = { \2 = \3 }",
        ### > 3.1.* beta
        r"(\s+set_)(primitive)\s*=\s*yes": r"\1country_type = \2",
        # r"(\s+)count_armies": r"\1count_owned_army", # count_planet_army (scope split: depending on planet/country)
        # r"(\s+)(icon_frame\s*=\s*[0-5])": "", # remove
        r"text_icon\s*=\s*military_size_space_creature": ("common\\ship_sizes", "icon = ship_size_space_monster"),
        # conflict used for starbase
        # r"icon_frame\s*=\s*2": ("common\\ship_sizes", lambda p: p.group(1)+"icon = }[p.group(2)]),
        r"text_icon\s*=\s*military_size_": ("common\\ship_sizes", "icon = ship_size_military_"),
        # r"\s+icon_frame\s*=\s*\d": (["common\\bombardment_stances", "common\\ship_sizes"], ""), used for starbase
        r"^\s+robotic\s*=\s*(yes|no)[ \t]*\n": ("common\\species_classes", ""),
        r"^(\s+icon)_frame\s*=\s*([1-9][0-4]?)":
            ("common\\armies", lambda p:
             p.group(1) + " = GFX_army_type_" + {
                 "1": "defensive",
                 "2": "assault",
                 "3": "rebel",
                 "4": "robot",
                 "5": "primitive",
                 "6": "gene_warrior",
                 "7": "clone",
                 "8": "xenomorph",
                 "9": "psionic",
                 "10": "slave",
                 "11": "machine_assault",
                 "12": "machine_defensive",
                 "13": "undead",
                 "14": "imperial"
             }[p.group(2)]),
        r"^(\s+icon)_frame\s*=\s*(\d+)":
            ("common\\planet_classes", lambda p:
             p.group(1) + " = GFX_planet_type_" + {
                 "1": "desert",
                 "2": "arid",
                 "3": "tundra",
                 "4": "continental",
                 "5": "tropical",
                 "6": "ocean",
                 "7": "arctic",
                 "8": "gaia",
                 "9": "barren_cold",
                 "10": "barren",
                 "11": "toxic",
                 "12": "molten",
                 "13": "frozen",
                 "14": "gas_giant",
                 "15": "machine",
                 "16": "hive",
                 "17": "nuked",
                 "18": "asteroid",
                 "19": "alpine",
                 "20": "savannah",
                 "21": "ringworld",
                 "22": "habitat",
                 "23": "shrouded",
                 "25": "city",
                 "26": "m_star",
                 "27": "f_g_star",
                 "28": "k_star",
                 "29": "a_b_star",
                 "30": "pulsar",
                 "31": "neutron_star",
                 "32": "black_hole"
             }[p.group(2)]),
        r"^(\s+icon)\s*=\s*(\d+)":
            ("common\\colony_types", lambda p:
             p.group(1)+" = GFX_colony_type_"+{
                 "1": "urban",
                 "2": "mine",
                 "3": "farm",
                 "4": "generator",
                 "5": "foundry",
                 "6": "factory",
                 "7": "refinery",
                 "8": "research",
                 "9": "fortress",
                 "10": "capital",
                 "11": "normal_colony",
                 "12": "habitat",
                 "13": "rural",
                 "14": "resort",
                 "15": "penal",
                 "16": "primitive",
                 "17": "dying",
                 "18": "workers",
                 "19": "habitat_energy",
                 "20": "habitat_leisure",
                 "21": "habitat_trade",
                 "22": "habitat_research",
                 "23": "habitat_mining",
                 "24": "habitat_fortress",
                 "25": "habitat_foundry",
                 "26": "habitat_factory",
                 "27": "habitat_refinery",
                 "28": "bureaucratic",
                 "29": "picker",
                 "30": "fringe",
                 "31": "industrial"
             }[p.group(2)]),
        r"(\s+modifier)\s*=\s*\{\s*mult": r"\1 = { factor",
        # r"(\s+)pop_can_live_on_planet": r"\1can_live_on_planet", needs planet target
        r"\bcount_diplo_ties":          "count_relation",
        r"\bhas_non_swapped_tradition": "has_active_tradition",
        r"\bhas_swapped_tradition":     "has_active_tradition",
        r"\bis_for_colonizeable":       "is_for_colonizable",
        r"\bcolonizeable_planet":       "colonizable_planet",
        ### 3.2
        # r"\bis_planet_class\s*=\s*pc_ringworld_habitable": "is_ringworld = yes",
        r"\s+free_guarantee_days\s*=\s*\d+":  "",
        r"\badd_tech_progress_effect":  "add_tech_progress",
        r"\bgive_scaled_tech_bonus_effect": "add_monthly_resource_mult",
        r"\bclear_uncharted_space\s*=\s*\{\s*from\s*=\s*([^\n{}# ])\s*\}": r"clear_uncharted_space = \1",
        r"\bhomeworld\s*=\s*": ("common\\governments\\civics", r"starting_colony = "),
        r"^((?:\t|    )parent\s*=\s*planet_jobs)\b": ("common\\economic_categories", r"\1_productive"),
        r"^(\t|    )energy\s*=\s*(\d+|@\w+)": ("common\\terraform", r"\1resources = {\n\1\1category = terraforming\n\1\1cost = { energy = \2 }\n\1}"),
        ### 3.3
        r"\s+building(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow)\s*=\s*(?:yes|no)\n?": ("common\\buildings", ''),
    }


    targets4 = {
        # 3.0.* (multiline)
        # key (pre match without group): arr (search, replace) or str (if no group)
        r"\s+random_system_planet\s*=\s*\{\s*limit\s*=\s*\{\s*is_star\s*=\s*yes\s*\}": [r"(\s+)random_system_planet\s*=\s*\{\s*limit\s*=\s*\{\s*is_star\s*=\s*yes\s*\}", r"\1star = {"],
        r"\bcreate_leader\s*=\s*\{[^{}]+?\s+type\s*=\s*\w+": [r"(create_leader\s*=\s*\{[^{}]+?\s+)type\s*=\s*(\w+)", r"\1class = \2"],
        r"NO[RT]\s*=\s*\{\s*has_ethic\s*=\s*\"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic\s*=\s*\"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+\}": [r"NO[RT]\s*=\s*\{\s*has_ethic\s*=\s*\"?ethic_(?:(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic\s*=\s*\"?ethic_(?:(?:\1|\2)|fanatic_(?:\1|\2))\"?\s+\}", r"is_\1\2 = no"],
        r"(?:\s+OR\s*=\s*\{)?\s*has_ethic\s*=\s*\"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic\s*=\s*\"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s*\}?": [r"(\s+OR\s*=\s*\{)?(\s*?\n?\s*?)?(?(1)\t?)has_ethic\s*=\s*\"?ethic_(?:(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s*?has_ethic\s*=\s*\"?ethic_(?:(?:\4|\3)|fanatic_(?:\4|\3))\"?\s*?(?(1)\})", r"\2is_\3\4 = yes"], # r"\4is_ethics_aligned = { ARG1 = \2\3 }",
        ### Boolean operator merge
        # NAND <=> OR = { NOT
        r"\s+OR\s*=\s*\{(?:\s*NOT\s*=\s*\{[^{}#]*?\})+\s*\}[ \t]*\n": [r"^(\s+)OR\s*=\s*\{\s*?\n(?:(\s+)NOT\s*=\s*\{\s*)?([^{}#]*?)\s*\}(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?", r"\1NAND = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15"], # up to 7 items (sub-trigger)
        # NOR <=> AND = { NOT
        r"\s+AND\s*=\s*\{\s+(?:\s+NOT\s*=\s*\{\s*(?:[^{}#]+|\w+\s*=\s*{[^{}#]+\s*\})\s*\}){2,}\s*\}": [r"^(\s+)AND\s*=\s*\{\s*?\n(?:(\s+)NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?", r"\1NOR = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15"], # up to 7 items (sub-trigger)
        # NOR <=> (AND) = { NOT
        r"(?<![ \t]OR)\s+=\s*\{\s+(?:[^{}#\n]+\n)*(?:\s+NO[RT]\s*=\s*\{\s*[^{}#]+?\s*\}){2,}": [r"(\t*)NO[RT]\s*=\s*\{\s*([^{}#]+?)\s*\}\s*NO[RT]\s*=\s*\{\s*([^{}#]+?)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"], # only 2 items (sub-trigger) (?<!\sOR) Negative Lookbehind
        # NAND <=> NOT = { AND
        r"\s+NO[RT]\s*=\s*\{\s*AND\s*=\s*\{[^{}#]*?\}\s*\}": [r"(\t*)NO[RT]\s*=\s*\{\s*AND\s*=\s*\{[ \t]*\n(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?\s*\}[ \t]*\n", r"\1NAND = {\n\2\3\4\5"], # only 4 items (sub-trigger)
        # NOR <=> NOT = { OR
        r"\s+NO[RT]\s*=\s*\{\s*?OR\s*=\s*\{\s*(?:\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+?){2,}\}\s*\}": [r"(\t*)NO[RT]\s*=\s*\{\s*?OR\s*=\s*\{(\s+)(\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+)(\s*\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+\s*=\s*(?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?\s*\}\s+", r"\1NOR = {\2\3\4\5\6\7"], # only right indent for 5 items (sub-trigger)
        ### End boolean operator merge
        r"\sany_country\s*=\s*\{[^{}#]*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default)": [r"(\s)any_country\s*=\s*(\{[^{}#]*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default))", r"\1any_playable_country = \2"],
        r"\s(?:every|random|count)_country\s*=\s*\{[^{}#]*limit\s*=\s*\{\s*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default|has_special_project)": [r"(\s(?:every|random|count))_country\s*=\s*(\{[^{}#]*limit\s*=\s*\{\s*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default|has_special_project))", r"\1_playable_country = \2"],
        r"\{\s+(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*[\w\._:]+\s*\}\s*\}": [r"\{\s+(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*([\w\._:]+)\s*\}\s*\}", r"{ is_owned_by = \1 }"],
        r"NO[RT]\s*=\s*\{\s*is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s*\}": "is_fallen_empire = no",
        r"\s+(?:OR\s*=\s*\{)?\s{4,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s+\}?": [r"(\s+)(OR\s*=\s*\{)?\s{4,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)(?(1)\1\})", r"\1is_fallen_empire = yes"],
        r"NO[RT]\s*=\s*\{\s*is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = no",
        r"OR\s*=\s*\{\s*is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = yes",
        r"NO[RT]\s*=\s*\{\s*(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+\}": "is_synthetic_empire = no",
        r"OR\s*=\s*\{\s*(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+\}": "is_synthetic_empire = yes",
        r"NO[RT]\s*=\s*\{\s*has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*\}": "is_homicidal = no",
        r"(?:OR\s*=\s*\{\s*)?has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*\}?": [r"(OR\s*=\s*\{\s*)?has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic\s*=\s*\"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?(?(1)\s*\})", "is_homicidal = yes"],
        r"NOT\s*=\s*\{\s*check_variable\s*=\s*\{\s*which\s*=\s*\"?\w+\"?\s+value\s*=\s*[^{}#\s=]\s*\}\s*\}": [r"NOT\s*=\s*\{\s*(check_variable\s*=\s*\{\s*which\s*=\s*\"?\w+\"?\s+value)\s*=\s*([^{}#\s=])\s*\}\s*\}", r"\1 != \2 }"],
        # r"change_species_characteristics\s*=\s*\{\s*?[^{}\n]*?
        r"[\s#]+new_pop_resource_requirement\s*=\s*\{[^{}]+\}\s*": [r"([\s#]+new_pop_resource_requirement\s*=\s*\{[^{}]+\}[ \t]*)", ""],
        # needs now dot scope

        # >=3.1
        #but not used for starbases
        r"\bis_space_station\s*=\s*no\s*icon_frame\s*=\s*\d+":
            [r"(is_space_station\s*=\s*no\s*)icon_frame\s*=\s*([1-9][0-2]?)",
             ("common\\ship_sizes", lambda p:
              p.group(1) + "icon = ship_size_" + {
                  "1": "military_1",
                  "2": "military_1",
                  "3": "military_2",
                  "4": "military_4",
                  "5": "military_8",
                  "6": "military_16",
                  "7": "military_32",
                  "8": "science",
                  "9": "constructor",
                  "10": "colonizer",
                  "11": "transport",
                  "12": "space_monster"
              }[p.group(2)])],
        r"\{\s*which\s*=\s*\"?\w+\"?\s+value\s*[<=>]+\s*(?:prev|from|root|event_target:[^\.\s])+\s*\}": [r"(\s*which\s*=\s*\"?(\w+)\"?\s+value\s*[<=>]+\s*(prev|from|root|event_target:[^\.\s])+)", r"\1.\2"],
        r"\bset_variable\s*=\s*\{\s*which\s*=\s*\"?\w+\"?\s+value\s*=\s*(?:event_target:[^\d:{}#\s=\.]+|(prev\.?|from\.?|root|this|megastructure|planet|country|owner|space_owner|ship|pop|fleet|galactic_object|leader|army|ambient_object|species|pop_faction|war|federation|starbase|deposit|sector|archaeological_site|first_contact|spy_network|espionage_operation|espionage_asset)+)\s*\}": [r"set_variable\s*=\s*\{\s*which\s*=\s*\"?(\w+)\"?\s+value\s*=\s*(event_target:\w+|\w+)\s*\}", r"set_variable = { which = \1 value = \2.\1 }"],
        r"\s+spawn_megastructure\s*=\s*\{[^{}#]+": [r"(\s+)location\s*=\s*([\w\._:]+)", r"\1coords_from = \2"],
        # >= 3.2
        r"\bNO[RT]\s*=\s*\{\s*is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s+is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s*\}": [r"\bNO[RT]\s*=\s*\{\s*is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s+is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s*\}", r"is_artificial = no"],
        r"\bis_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s+is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\b": [r"\bis_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\s+is_planet_class\s*=\s*(?:pc_ringworld_habitable|pc_habitat)\b", r"is_artificial = yes"],
        r"\n\s+possible\s*=\s*\{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)(?:drone|worker|specialist|ruler)_job_check_trigger\s*=\s*yes\s*": [r"(\s+)(possible\s*=\s*\{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?))(drone|worker|specialist|ruler)_job_check_trigger\s*=\s*yes\s*", ("common\\pop_jobs", r"\1possible_precalc = can_fill_\4_job\1\2")], # only with 6 possible prior lines
        r"[^b]\n\s+possible\s*=\s*\{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)complex_specialist_job_check_trigger\s*=\s*yes\s*": [r"(\s+)(possible\s*=\s*\{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)complex_specialist_job_check_trigger\s*=\s*yes\s*)", ("common\\pop_jobs", r"\1possible_precalc = can_fill_specialist_job\1\2")], # only with 6 possible prior lines
        # >3.2
        r"\bany_\w+\s*=\s*\{[^{}]+?\bcount\s*[<=>]+\s*[^{}\s]+\s+[^{}]*\}": [r"\bany_(\w+)\s*=\s*\{\s*(?:([^{}]+?)\s+(\bcount\s*[<=>]+\s*[^{}\s]+)|(\bcount\s*[<=>]+\s*[^{}\s]+)\s+([^{}]*))\s+\}", r"count_\1 = { limit = { \2\5 } \3\4 }"], # too rare!? only simple supported TODO
    }

if code_cosmetic and not only_warning:
    targets3[r"([\s\.]+(PREV|FROM|ROOT|THIS)+)"] = lambda p: p.group(1).lower() # r"([\s\.]+(PREV|FROM|ROOT|THIS)+)": lambda p: p.group(1).lower(),  ## targets3[re.compile(r"([\s\.]+(PREV|FROM|ROOT|THIS)+)", re.I)] = lambda p: p.group(1).lower()
    targets3[r" {4}"] = r"\t"  # r" {4}": r"\t", # convert space to tabs
    targets3[r"\s*days\s*=\s*-1"] = '' # default not needed anymore
    targets3[r"# {1,3}([a-z])([a-z]+ +[^;:\s#=<>]+)"] = lambda p: "# "+p.group(1).upper() + p.group(2) # format comment
    targets3[r"#([^\-\s#])"] = r"# \1" # r"#([^\s#])": r"# \1", # format comment
    targets3[r"# +([A-Z][^\n=<>{}\[\]# ]+? [\w,\.;\'\/\\+\- ()&]+? \w+ \w+ \w+)$"] = r"# \1." # set comment punctuation mark
    targets3[r"# ([a-z])(\w+ +[^;:\s#=<>]+ [^\n]+?[\.!?])$"] = lambda p: "# "+p.group(1).upper() + p.group(2) # format comment
    # NOT NUM triggers. TODO <> ?
    targets3[r"\bNOT\s*=\s*\{\s*(num_\w+|\w+?(?:_passed))\s*=\s*(\d+)\s*\}"] = r"\1 != \2"
    ## targets3[r"# *([A-Z][\w ={}]+?)\.$"] = r"# \1" # remove comment punctuation mark
    targets4[r"\n{3,}"] = "\n\n" # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    targets4[r"\n\s+\}\s*else"] = [r"\}\s*else", "} else"] # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    # WARNING not valid if in OR: NOR <=> AND = { NOT NOT } , # only 2 items (sub-trigger)  
    targets4[r"\n\s+NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR]\s*=\s*\{\s*[^{}#\n]+\s*\}"] = [r"([\t ]+)NO[TR]\s*=\s*\{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR]\s*=\s*\{\s*([^{}#\r\n]+)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"] 
    targets4[r"\brandom_country\s*=\s*\{\s*limit\s*=\s*\{\s*is_country_type\s*=\s*global_event\s*\}"] = "event_target:global_event_country = {"
    targets4[r"(?:\s+add_resource\s*=\s*\{\s*\w+\s*=\s*[^{}#]+\s*\})+"] = [r"(\s+add_resource\s*=\s*\{)(\s*\w+\s*=\s*[^\s{}#]+)\s*\}\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\}(?(3)\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\})?(?(4)\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\})?(?(5)\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\})?(?(6)\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\})?(?(7)\s+add_resource\s*=\s*\{(\s*\w+\s*=\s*[^\s{}#]+)\s*\})?", r"\1\2\3\4\5\6\7 }"] # 6 items 



def mBox(mtype, text):
    tk.Tk().withdraw()
    style = not mtype and messagebox.showinfo or mtype == 'Abort' and messagebox.showwarning or messagebox.showerror
    style(title=mtype, message=text)


def iBox(title, prefil):  # , master
    answer = filedialog.askdirectory(
        initialdir=prefil,
        title=title,
        # parent=master
    )
    return answer

#============== Set paths ===============
def parse_dir():
    global mod_path, mod_outpath
    files = []
    mod_path = os.path.normpath(mod_path)
    print("Welcome to Stellaris Mod-Updater-%s by F1r3Pr1nc3!" % stellaris_version)

    if not os.path.isdir(mod_path):
        mod_path = os.getcwd()
    mod_path = iBox("Please select a mod folder:", mod_path)
    # mod_path = input('Enter target directory: ')
    # mod_outpath = iBox('Enter out directory (optional):', mod_path)
    # mod_outpath = input('Enter out directory (optional):')
    # mod_outpath = os.path.normpath(mod_outpath)

    if not os.path.isdir(mod_path):
        # except OSError:
        #     print('Unable to locate the mod path %s' % mod_path)
        mBox('Error', 'Unable to locate the mod path %s' % mod_path)
        return False
    if len(mod_outpath) < 1 or not os.path.isdir(mod_outpath) or mod_outpath == mod_path:
        mod_outpath = mod_path
        if only_warning:
            print('Attention: files are ONLY checked!')
        else:
            print('Warning: Mod files will be overwritten!')
    else:
        mod_outpath = os.path.normpath(mod_outpath)

    print("\tLoading folder", mod_path)

    files = glob.glob(mod_path + '/**', recursive=True)  # '\\*.txt'
    # files = glob.glob(mod_path, recursive=True)  # os.path.join( ,'\\*.txt'
    modfix(files)


def modfix(file_list):
    # global mod_path, mod_outpath
    # print(targets3)
    # print("mod_outpath", mod_outpath)
    # print(mod_path)
    subfolder = ''
    for _file in file_list:
        if os.path.isfile(_file) and re.search(r"\.txt$", _file):
            subfolder = os.path.relpath(_file, mod_path)
            file_contents = ""
            print("\tCheck file:", _file)
            with open(_file, 'r', encoding='utf-8', errors='ignore') as txtfile:
                # out = txtfile.read() # full_fille
                # try:
                # print(_file, type(_file))
                # pattern = re.compile(u)
                # print(pattern.search(txtfile))
                # for t, r in targets2.items():
                #     targets = re.findall(t, txtfile)
                #     if len(targets) > 0:
                #         for target in targets:
                #             value = target.split("=")[1]
                #             replacer = ""
                #             for i in range(len(r)):
                #                 replacer += r[i]
                #                 if i < len(r) -1:
                #                     replacer += value
                #             if target in line and replacer not in line:
                #                 line = line.replace(target,replacer)

                file_contents = txtfile.readlines()
                subfolder, basename = os.path.split(subfolder)
                # basename = os.path.basename(_file)
                # txtfile.close()
                out = ""
                changed = False
                for i, line in enumerate(file_contents):
                    if len(line) > 10:
                        # for line in file_contents:
                        # print(line)
                        for rt in removedTargets:
                            msg = ''
                            if isinstance(rt, tuple):
                                # print(type(subfolder), subfolder, rt[0])
                                if subfolder in rt[0]:
                                    rt = rt[1] # , flags=re.I
                                else: rt = False
                            if isinstance(rt, list) and len(rt) > 1:
                                msg = ' (' + rt[1] + ')'
                                rt = rt[0]
                            if rt:
                                rt = re.search(rt, line) # , flags=re.I
                            if rt:
                                print(" WARNING outdated removed syntax%s: %s in line %i file %s\n" % (msg, rt.group(0), i, basename))
                        for pattern, repl in targets3.items():
                            # print(line)
                            # print(pattern, repl)
                            # check valid folder
                            rt = False
                            if isinstance(repl, tuple):
                                folder, repl = repl
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo: rt = True
                                elif subfolder in folder:
                                    rt = True
                                else: rt = False
                            else: rt = True
                            if rt: # , flags=re.I # , count=0, flags=0
                                rt = re.search(pattern, line) # , flags=re.I
                                if rt:
                                    line = re.sub(pattern, repl, line, flags=0) # , flags=re.I
                                    # line = line.replace(t, r)
                                    changed = True
                                    print("\tUpdated file: %s at line %i with %s\n" % (basename, i, line.strip().encode()))
                    out += line

                for pattern, repl in targets4.items():
                    targets = re.findall(pattern, out, flags=re.I)
                    # if targets:
                    if len(targets) > 0:
                        # print(targets, type(targets))
                        for tar in targets:
                            # check valid folder
                            rt = False
                            replace = repl
                            if isinstance(repl, list) and isinstance(repl[1], tuple):
                                folder, repl = repl[1]
                                replace[1] = repl
                                repl = replace
                                # print(type(repl), repl)
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo: rt = True
                                elif subfolder in folder: rt = True
                                else: rt = False
                            else: rt = True
                            if rt:
                                # print(type(repl), tar, type(tar))
                                if isinstance(repl, list):
                                    replace = re.sub(repl[0], repl[1], tar, flags=re.I|re.M|re.A)
                                if isinstance(repl, str) or (not isinstance(tar, tuple) and tar in out and tar != replace):
                                    print("Match:\n", tar)
                                    print("Multiline replace:\n", replace) # repr(
                                    out = out.replace(tar, replace)
                                    changed = True

                if changed and not only_warning:
                    structure = os.path.normpath(os.path.join(mod_outpath, subfolder))
                    out_file = os.path.join(structure, basename)
                    print('\tWrite file:', out_file)
                    if not os.path.exists(structure):
                        os.makedirs(structure)
                        # print('Create folder:', subfolder)
                    open(out_file, "w", encoding='utf-8').write(out)

                # except Exception as e:
                # except OSError as e:
                #     print(e)
                #     print("Unable to open", _file)
            txtfile.close()
        # elif os.path.isdir(_file):
        #     # if .is_dir():
        #     # subfolder = _file.replace(mod_path + os.path.sep, '')
        #     subfolder = os.path.relpath(_file, mod_path)
        #     # print("subfolder:", subfolder)
        #     structure = os.path.join(mod_outpath, subfolder)
        #     if not os.path.isdir(structure):
        #         os.mkdir(structure)
        # else: print("NO TXT?", _file)
    print("\nDone!")

parse_dir()  # mod_path, mod_outpath
# input("\nPRESS ANY KEY TO EXIT!")
