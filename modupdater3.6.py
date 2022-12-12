# @author: FirePrince
# @version: 3.6.1
# @revision: 2022/12/12
# @thanks: OldEnt for detailed rundowns
# @forum: https://forum.paradoxplaza.com/forum/threads/1491289/
# @TODO: full path mod folder
#        replace in *.YML
# @TODO: extended support The Merger of Rules
# ============== Import libs ===============
import os  # io for high level usage
import glob
import re

# from pathlib import Path
# import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
stellaris_version = '3.6.1'

# ============== Initialize global parameter/option variables ===============
# True/False optional 
only_warning = False  # True implies code_cosmetic = False
code_cosmetic = False # True/False optional (only if only_warning = False)
only_actual = False   # True speedup search (from previous relevant) to actual version
also_old = False      # Beta: only some pre 2.3 stuff
debug_mode = False    # for dev print
mergerofrules = False # True Support global compatibility for The Merger of Rules; needs scripted_trigger file or mod
keep_default_country_trigger = False # on playable effect "is_country_type = default"

only_v3_5 = False # Single version
only_v3_4 = False # Single version

mod_outpath = '' # if you don't want to overwrite the original
# mod_path = os.path.dirname(os.getcwd())
mod_path = os.path.expanduser('~') + '/Documents/Paradox Interactive/Stellaris/mod'



# if not sys.version_info.major == 3 and sys.version_info.minor >= 6:
#     print("Python 3.6 or higher is required.")
#     print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
#     sys.exit(1)

# v.3.6
# - .lua replaced by .shader
# v3.4
# - new country_limits - replaced empire_limit
# - new agreement_presets - replaced subjects
# For performance reason option
# v3.3 TODO soldier_job_check_trigger
# ethics    value -> base
# -empire_size_penalty_mult = 1.0
# +empire_size_pops_mult = -0.15
# +empire_size_colonies_mult = 0.5
# -country_admin_cap_add = 15
# +country_unity_produces_mult = 0.05
# 3.0 removed ai_weight for buildings except branch_office_building = yes

resource_items = r"energy|unity|food|minerals|influence|alloys|consumer_goods|exotic_gases|volatile_motes|rare_crystals|sr_living_metal|sr_dark_matter|sr_zro|(?:physics|society|engineering(?:_research))"
exlude_trigger_folder = re.compile(r"^([^_]+)(_(?!trigger)[^/_]+|[^_]*)(?(2)/([^_]+)_[^/_]+)?$") # 2lvl, only 1lvl folder: ^([^_]+)(_(?!trigger)[^_]+|[^_]*)$ only 

if only_actual:
    removedTargets = []
    targets3 = {
        r"\bpop_assembly_speed": "planet_pop_assembly_mult",
        r"\bis_ringworld =": (exlude_trigger_folder, "has_ringworld_output_boost ="),
    }
    targets4 = {
        r"\bis_triggered_only = yes\s+trigger = \{\s+always = no": [r"(\s+)(trigger = \{\s+always = no)", ('events', r'\1is_test_event = yes\1\2')],
        r'slot\s*=\s*\"?(?:SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template\s*=\s*\"?AUTOCANNON_\d\"?': [r'(=\s*\"?(SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template\s*=\s*)\"?(AUTOCANNON_\d)\"?', ('common/global_ship_designs', r'\1"\2_\3"')],
        r"\bhas_(?:population|colonization|migration)_control = \{\s+value =": ["value", 'type'],
        r"(\bOR = \{\s*(has_trait = trait_(?:latent_)?psionic\s+){2}\})": "has_psionic_species_trait = yes",
    }
elif only_v3_5: 
    removedTargets = [
        # v3.5
        # [r"\b(any|every|random|count|ordered)_bordering_country = \{", 'just use xyz_country_neighbor_to_system instead'],
        # [r"\b(restore|store)_galactic_community_leader_backup_data = ", 'now a scripted effect or just use store_country_backup_data instead']
    ]
    targets3 = {
        r"\b(any|every|random|count|ordered)_bordering_country\b": r'\1_country_neighbor_to_system',
        r"\bcountry_(?!base_)(%s)_produces_add\b" % resource_items: r'country_base_\1_produces_add',
        r"\bhair(\s*)=": ("prescripted_countries", r"attachment\1="),
        r"\bship_archeaological_site_clues_add\s*=": r"ship_archaeological_site_clues_add =",
        r"\bfraction(\s*)=\s*\{": ("common/ai_budget", r"weight\1=\1{"),
        r"\bstatic_m([ai])x(\s*)=\s*\{": ("common/ai_budget", r"desired_m\1x\2=\2{"),
        r"^(\s+)([^#]*?\bbuildings_(?:simple_allow|no_\w+) = yes.*)": ("common/buildings", r"\1# \2"), # removed scripted triggers
        # r"(\"NAME_[^-\s\"]+)-([^-\s\"]+)\"": r'\1_\2"', mostly but not generally done
    }
    targets4 = {
        r"\bany_system_planet = \{[^{}#]*(?:has_owner = yes|is_colony = yes|exists = owner)\s+": [r"any_system_planet = (\{[^{}#]*)(?:has_owner = yes|is_colony = yes|exists = owner)\s+", r"any_system_colony = \1"],
        r"\s(?:every|random|count|ordered)_system_planet = \{[^{}#]*limit = \{\s*(?:has_owner = yes|is_colony = yes|exists = owner)\s+": [r"(every|random|count)_system_planet = (\{[^{}#]*limit = \{\s*)(?:has_owner = yes|is_colony = yes|exists = owner)\s+", r"\1_system_colony = \2"],
        r"(\bOR = \{\s+(has_trait = trait_(?:plantoid|lithoid)_budding\s+){2}\})": "has_budding_trait = yes",
        r"_pop = \{\s+unemploy_pop = yes\s+kill_pop = yes": [r"(_pop = \{\s+)unemploy_pop = yes\s+(kill_pop = yes)", r"\1\2"], # ghost pop bug fixed
    }
elif only_v3_4:
    removedTargets = [
        ("common/ship_sizes", [r"^\s+empire_limit = \{", '"empire_limit" has been replaces by "ai_ship_data" and "country_limits"']),
        ("common/country_types", [r"^\s+(?:ship_data|army_data) = { = \{", '"ship_data & army_data" has been replaces by "ai_ship_data" and "country_limits"']),
        r"\b(fire_warning_sign|add_unity_times_empire_size) = yes",
        r"\boverlord_has_(num_constructors|more_than_num_constructors|num_science_ships|more_than_num_science_ships)_in_orbit\b",
    ]
    targets3 = {
        # >= 3.4
        r"\bis_subject_type = vassal": "is_subject = yes",
        r"\bis_subject_type = (\w+)": r"any_agreement = { agreement_preset = preset_\1 }",
        r"\bsubject_type = (\w+)": r"preset = preset_\1",
        r"\badd_100_unity_per_year_passed =": "add_500_unity_per_year_passed =",
        r"\bcount_drones_to_recycle =": "count_robots_to_recycle =",
        r"\bbranch_office_building = yes": ("common/buildings", r"owner_type = corporate"),
        r"\bhas_species_flag = racket_species_flag":  r"exists = event_target:racket_species is_same_species = event_target:racket_species",
        # code opts/cosmetic only
        re.compile(r"\bNOT = \{\s*((?:leader|owner|PREV|FROM|ROOT|THIS|event_target:\w+) = \{)\s*([^\s]+) = yes\s*\}\s*\}", re.I): r"\1 \2 = no }",
    }
    targets4 = {
        # >= 3.4
        r"\n(?:\t| {4})empire_limit = \{\s+base = [\w\W]+\n(?:\t| {4})\}": [r"(\s+)empire_limit = \{(\s+)base = (\d+\s+max = \d+|\d+)[\w\W]+?(?(1)\s+\})\s+\}", ('common/ship_sizes', r'\1ai_ship_data = {\2min = \3\1}')],
        r"\bpotential = \{\s+always = no\s+\}": ["potential", ('common/armies', 'potential_country')],
        #r"(?:\t| {4})potential = \{\s+(?:exists = )?owner[\w\W]+\n(?:\t| {4})\}": [r"potential = \{\s+(?:exists = owner)?(\s+)owner = \{\s+([\w\W]+?)(?(1)\s+\})\s+\}", ("common/armies", r'potential_country = { \2 }')],
        r"\s+construction_block(?:s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no": [r"construction_block(s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no", ("common/megastructures", 'construction_blocks_and_blocked_by = self_type')],
        r"construction_blocks_others = no": ["construction_blocks_others = no", ("common/megastructures", 'construction_blocks_and_blocked_by = none')],
        # r"construction_blocked_by_others = no": ("common/megastructures", 'construction_blocks_and_blocked_by = self_type'),
        r"(?:contact|any_playable)_country\s*=\s*{\s+(?:NOT = \{\s+)?(?:any|count)_owned_(?:fleet|ship) = \{": [r"(any|count)_owned_(fleet|ship) =", r"\1_controlled_\2 ="], # only playable empire!?
        # r"\s+every_owned_fleet = \{\s+limit\b": [r"owned_fleet", r"controlled_fleet"], # only playable empire and not with is_ship_size!?
        # r"\s+(?:any|every|random)_owned_ship = \{": [r"(any|every|random)_owned_ship =", r"\1_controlled_fleet ="], # only playable empire!?
        r"\s+(?:any|every|random)_(?:system|planet) = \{(?:\s+limit = \{)?\s+has_owner = yes\s+is_owned_by": [r"(any|every|random)_(system|planet) =", r"\1_\2_within_border ="],
        r"\b(NO[RT] = \{\s*(has_trait = trait_(?:zombie|nerve_stapled)\s+){2}\}|(NOT = \{\s*has_trait = trait_(?:zombie|nerve_stapled)\s+\}){2})": "can_think = no",
        r"(\bOR = \{\s*(has_trait = trait_(?:zombie|nerve_stapled)\s+){2}\})": "can_think = yes",
        r"(\bOR = \{\s*(species_portrait = human(?:_legacy)?\s+){2}\})": "is_human_species = yes",
        r"\bNO[RT] = \{\s*has_modifier = doomsday_\d[\w\s=]+\}": [r"NO[RT] = \{\s*(has_modifier = doomsday_\d\s+){5}\}", "is_doomsday_planet = no"],
        r"\bOR = \{\s*has_modifier = doomsday_\d[\w\s=]+\}": [r"OR = \{\s*(has_modifier = doomsday_\d\s+){5}\}", "is_doomsday_planet = yes"],
        r"\b(?:species_portrait = human(?:_legacy)?\s+){1,2}": [r"species_portrait = human(?:_legacy)?(\s+)(?:species_portrait = human(?:_legacy)?)?", r"is_human_species = yes\1"],
        r"\bvalue = subject_loyalty_effects\s+\}\s+\}": [r"(subject_loyalty_effects\s+\})(\s+)\}", ('common/agreement_presets', r"\1\2\t{ key = protectorate value = subject_is_not_protectorate }\2}")],
    }

else:
    # >= 3.0.*
    """== 3.1 Quick stats ==
    6 effects removed/renamed.
    8 triggers removed/renamed.
    426 modifiers removed/renamed.
    1 scope removed.
    # >= 3.1.*
    # prikki country removed
    """
    removedTargets = [
        # This are only warnings, commands which cannot be easily replaced.
        # Format: tuple is with folder (folder, regexp/list); list is with a specific message [regexp, msg]
        # 3.2
        r"\sslot = 0", # \sset_starbase_module = \{ now starts with 1
        [r"[^# \t]\s+is_planet_class = pc_ringworld_habitable", 'could possibly be replaced with "is_ringworld = yes"'],
        # r"\sadd_tech_progress_effect = ", # replaced with add_tech_progress
        # r"\sgive_scaled_tech_bonus_effect = ", # replaced with add_monthly_resource_mult
        ("common/districts", r"\sdistricts_build_district\b"), # scripted trigger
        ("common/pop_jobs", r"\s(drone|worker|specialist|ruler)_job_check_trigger\b"), # scripted trigger

        # 3.1
        [r"\b(any|every|random)_(research|mining)_station\b", 'use just mining_station/research_station instead'], # = 2 trigger & 4 effects
        [r"\sobservation_outpost = \{\s*limit", 'is now a scope (from planet) rather than a trigger/effect'],
        r"\spop_can_live_on_planet\b", # r"\1can_live_on_planet", needs planet target
        r"\scount_armies\b", # (scope split: depending on planet/country)
        (["common/bombardment_stances", "common/ship_sizes"], [r"^\s+icon_frame = \d+", '"icon_frame" now only used for starbases']), # [6-9]  # Value of 2 or more means it shows up on the galaxy map, 1-5 denote which icon it uses on starbase sprite sheets (e.g. gfx/interface/icons/starbase_ship_sizes.dds)

        # PRE TEST
        # r"\sspaceport\W", # scope replace?
        # r"\shas_any_tradition_unlocked\W", # replace?
        # r"\smodifier = \{\s*mult", # => factor
        # r"\s+count_diplo_ties",
        # r"\s+has_non_swapped_tradition",
        # r"\s+has_swapped_tradition",
        r"\swhich = \"?\w+\"?\s+value\s*[<=>]\s*\{\s*scope\s*=", # var from 3.0
        # re.compile(r"\s+which = \"?\w+\"?\s+value\s*[<=>]\s*(prev|from|root|event_target:[^\.\s]+)+\s*\}", re.I), # var from 3.0

        # < 3.0
        r"\sproduced_energy\b",
        r"\s(ship|army|colony|station)_maintenance\b",
        r"\s(construction|trade|federation)_expenses\b",
        r"\shas_(population|migration)_control = (yes|no)",
        r"\s(any|every|random)_planet\b", # split in owner and galaxy and system scope
        r"\s(any|every|random)_ship\b", # split in owner and galaxy and system scope
        ("common/buildings", [r"^\s+ai_weight\s*=", 'ai_weight for buildings removed except for branch office']), # replaced buildings ai
        # < 2.0
        r"\scan_support_spaceport = (yes|no)",
        # 3.3
        "tech_repeatable_improved_edict_length",
        r"(^\s+|[^#] )country_admin_cap_(add|mult)",
        ("common/buildings", r"\sbuilding(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow)\s*="), # replaced buildings ai
        [r"\bnum_\w+\s*[<=>]+\s*[a-z]+[\s}]", 'no scope alone'], #  [^\d{$@] too rare (could also be auto fixed)
        [r"\n\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}", 'can be merged to NOR if not in an OR'], #  [^\d{$@] too rare (could also be auto fixed)
        ("common/traits", [r"^\s+modification = (?:no|yes)\s*", '"modification" flag which has been deprecated. Use "species_potential_add", "species_possible_add" and "species_possible_remove" triggers instead.']),
        # 3.4
        ("common/ship_sizes", [r"^\s+empire_limit = \{\s+", '"empire_limit" has been replaces by "ai_ship_data" and "country_limit"']),
        ("common/country_types", [r"^\s+(?:ship_data|army_data) = { = \{", '"ship_data & army_data" has been replaces by "ai_ship_data" and "country_limits"']),
        r"\b(fire_warning_sign|add_unity_times_empire_size) = yes",
        r"\boverlord_has_(num_constructors|more_than_num_constructors|num_science_ships|more_than_num_science_ships)_in_orbit\b",
    ]

    # targets2 = {
    #     r"MACHINE_species_trait_points_add = \d" : ["MACHINE_species_trait_points_add ="," ROBOT_species_trait_points_add = ",""],
    #     r"job_replicator_add = \d":["if = {limit = {has_authority = auth_machine_intelligence} job_replicator_add = ", "} if = {limit = {has_country_flag = synthetic_empire} job_roboticist_add = ","}"]
    # }

    targets3 = {
        r"\bowner\.species\b": "owner_species",
        ### >= 3.0.* (only one-liner)
        r"\b(first_contact_)attack_not_allowed": r"\1cautious",
        r"\bsurveyed = \{": r"set_surveyed = {",
        r"(\s+)set_surveyed = (yes|no)": r"\1surveyed = \2",
        r"has_completed_special_project\s+": "has_completed_special_project_in_log ",
        r"has_failed_special_project\s+": "has_failed_special_project_in_log ",
        r"species = last_created(\s)": r"species = last_created_species\1",
        r"owner = last_created(\s)": r"owner = last_created_country\1",
        r"(\s(?:any|every|random))_pop\s*=": r"\1_owned_pop =",
        r"(\s(?:any|every|random))_planet\s*=": r"\1_galaxy_planet =", #_system_planet
        r"(\s(?:any|every|random))_ship\s*=": r"\1_fleet_in_system =", # _galaxy_fleet
        r"(\s(?:any|every|random|count))_sector\s*=": r"\1_owned_sector =", # _galaxy_sector
        r"(\s(?:any|every|random))_war_(attacker|defender)\s*=": r"\1_\2 =",
        r"(\s(?:any|every|random|count))_recruited_leader\s*=": r"\1_owned_leader =",
        r"count_planets\s*": "count_system_planet  ", # count_galaxy_planet
        r"count_ships\s*": "count_fleet_in_system ", # count_galaxy_fleet
        r"count(_owned)?_pops\s*": "count_owned_pop ",
        r"count_(owned|fleet)_ships\s*": "count_owned_ship ", # 2.7
        # "any_ship_in_system": "any_fleet_in_system", # works only sure for single size fleets
        r"spawn_megastructure = \{([^{}#]+)location\s*=": r"spawn_megastructure = {\1planet =", # s.a. multiline coords_from
        r"\s+planet = (solar_system|planet)[\s\n\r]*": "",  # REMOVE
        r"(\s+)any_system_within_border = \{\s*any_system_planet = (.*?\s*\})\s*\}": r"\1any_planet_within_border = \2", # very rare, maybe put to cosmetic
        r"is_country_type = default\s+has_monthly_income = \{\s*resource = (\w+) value <=? \d": r"no_resource_for_component = { RESOURCE = \1",
        r"([^\._])owner = \{\s*is_same_(?:empire|value) = ([\w\._:]+)\s*\}": r"\1is_owned_by = \2",
        r"(\s+)is_(?:country|same_value) = ([\w\._:]+\.(?:controller|(?:space_)?owner)(?:\.overlord)?(?:[\s}]|$))": r"\1is_same_empire = \2",
        # r"exists = (?:solar_system|planet)\.(?:space_)?owner( |$)": r"has_owner = yes\1", TODO not sure
        # code opts/cosmetic only
        r"\bNOT = \{\s*([^\s]+) = yes\s*\}": r"\1 = no",
        r"\bany_system_planet = \{\s*is_capital = (yes|no)\s*\}": r"is_capital_system = \1",
        r"(\s+has_(?:population|migration)_control) = (yes|no)": r"\1 = { type = \2 country = prev.owner }", # NOT SURE
        re.compile(r"\bNOT = \{\s*((?:leader|owner|PREV|FROM|ROOT|THIS|event_target:\w+) = \{)\s*([^\s]+) = yes\s*\}\s*\}", re.I): r"\1 \2 = no }",

        ## Since Megacorp removed: change_species_characteristics was false documented until 3.2
        r"[\s#]+(pops_can_(be_colonizers|migrate|reproduce|join_factions|be_slaves)|can_generate_leaders|pops_have_happiness|pops_auto_growth|pop_maintenance) = (yes|no)\s*": "",
        ### somewhat older
        r"(\s+)ship_upkeep_mult\s*=": r"\1ships_upkeep_mult =",
        r"\b(contact_rule = )script_only": ("common/country_types", r"\1on_action_only"),
        r"\b(any|every|random)_(research|mining)_station\b": r"\2_station",
        r"(\s+)add_(%s) = (-?@\w+|-?\d+)" % resource_items: r"\1add_resource = { \2 = \3 }",
        ### > 3.1.* beta
        r"(\s+set_)(primitive) = yes": r"\1country_type = \2",
        # r"(\s+)count_armies": r"\1count_owned_army", # count_planet_army (scope split: depending on planet/country)
        # r"(\s+)(icon_frame = [0-5])": "", # remove
        r"text_icon = military_size_space_creature": ("common/ship_sizes", "icon = ship_size_space_monster"),
        # conflict used for starbase
        # r"icon_frame = 2": ("common/ship_sizes", lambda p: p.group(1)+"icon = }[p.group(2)]),
        r"text_icon = military_size_": ("common/ship_sizes", "icon = ship_size_military_"),
        # r"\s+icon_frame = \d": (["common/bombardment_stances", "common/ship_sizes"], ""), used for starbase
        r"^\s+robotic = (yes|no)[ \t]*\n": ("common/species_classes", ""),
        r"^(\s+icon)_frame = ([1-9][0-4]?)":
            ("common/armies", lambda p:
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
        r"^(\s+icon)_frame = (\d+)":
            ("common/planet_classes", lambda p:
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
        r"^(\s+icon) = (\d+)":
            ("common/colony_types", lambda p:
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
        # r"(\s+modifier) = \{\s*mult": r"\1 = { factor", now multiline
        # r"(\s+)pop_can_live_on_planet": r"\1can_live_on_planet", needs planet target
        r"\bcount_diplo_ties":          "count_relation",
        r"\bhas_non_swapped_tradition": "has_active_tradition",
        r"\bhas_swapped_tradition":     "has_active_tradition",
        r"\bis_for_colonizeable":       "is_for_colonizable",
        r"\bcolonizeable_planet":       "colonizable_planet",
        r"\bis_country\b":              "is_same_empire",
        ### 3.2 ###
        # r"\bis_planet_class = pc_ringworld_habitable": "is_ringworld = yes",
        r"\s+free_guarantee_days = \d+":  "",
        r"\badd_tech_progress_effect":  "add_tech_progress",
        r"\bgive_scaled_tech_bonus_effect": "add_monthly_resource_mult",
        r"\bclear_uncharted_space = \{\s*from = ([^\n{}# ])\s*\}": r"clear_uncharted_space = \1",
        r"\bhomeworld = ": ("common/governments/civics", r"starting_colony = "),
        # r"^((?:\t|    )parent = planet_jobs)\b": ("common/economic_categories", r"\1_productive"), TODO
        r"^(\t|    )energy = (\d+|@\w+)": ("common/terraform", r"\1resources = {\n\1\1category = terraforming\n\1\1cost = { energy = \2 }\n\1}"),
        ### 3.3 ###
        r"\s+building(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow) = (?:yes|no)\n?": ("common/buildings", ''),
        r"\bGFX_ship_part_auto_repair": (["common/component_sets", "common/component_templates"], 'GFX_ship_part_ship_part_nanite_repair_system'), # because icons.gfx
        r"\b(country_election_)influence_(cost_mult)": r'\1\2',
        r"\bwould_work_job": ("common/game_rules", 'can_work_specific_job'),
        r"\bhas_civic = civic_reanimated_armies": 'is_reanimator = yes',
        # r"^(?:\t\t| {4,8})value\s*=": ("common/ethics", 'base ='), maybe too cheap
        # r"\bcountry_admin_cap_mult\b": ("common/**", 'empire_size_colonies_mult'),
        # r"\bcountry_admin_cap_add\b": ("common/**", 'country_edict_fund_add'), 
        # r"\bcountry_edict_cap_add\b": ("common/**", 'country_power_projection_influence_produces_add'), 
        r"\bjob_administrator": 'job_politician',
        r"\b(has_any_(?:farming|generator)_district)\b": r'\1_or_building', # 3.3.4 scripted trigger
        r"^\t\tvalue\b": ("common/ethics", 'base'),
        # Replaces only in filename with species
        r"^(\s+)modification = (?:no|yes)\s*?\n": {"species": ("common/traits", r'\1species_potential_add = { always = no }\n' , '')},  # "modification" flag which has been deprecated. Use "species_potential_add", "species_possible_add" and "species_possible_remove" triggers instead.       
        ### >= 3.4 ###
        r"\bis_subject_type = vassal": "is_subject = yes",
        r"\bhas_tributary = yes": "any_agreement = { agreement_preset = preset_tributary }",
        r"\bis_subject_type = (\w+)": r"any_agreement = { agreement_preset = preset_\1 }",
        r"\bsubject_type = (\w+)": r"preset = preset_\1",
        r"\badd_100_unity_per_year_passed =": "add_500_unity_per_year_passed =",
        r"\bcount_drones_to_recycle =": "count_robots_to_recycle =",
        r"\bbranch_office_building = yes": ("common/buildings", r"owner_type = corporate"),
        r"\bhas_species_flag = racket_species_flag":  r"exists = event_target:racket_species is_same_species = event_target:racket_species",
        ### >= 3.5 ###
        r"\b(any|every|random|count|ordered)_bordering_country\b": r'\1_country_neighbor_to_system',
        r"\bcountry_(?!base_)(%s)_produces_add\b" % resource_items: r'country_base_\1_produces_add',
        r"\bhair(\s*)=": ("prescripted_countries", r"attachment\1="),
        r"\bship_archeaological_site_clues_add\s*=": r"ship_archaeological_site_clues_add =",
        r"\bfraction(\s*)=\s*\{": ("common/ai_budget", r"weight\1=\1{"),
        r"\bstatic_m([ai])x(\s*)=\s*\{": ("common/ai_budget", r"desired_m\1x\2=\2{"),
        r"^(\s+)([^#]*?\bbuildings_(?:simple_allow|no_\w+) = yes.*)": ("common/buildings", r"\1# \2"), # removed scripted triggers
        # r"(\"NAME_[^-\s\"]+)-([^-\s\"]+)\"": r'\1_\2"', mostly but not generally done
        ### 3.6
        r"\bpop_assembly_speed": "planet_pop_assembly_mult",
    }

    # re flags=re.I|re.M|re.A
    # key (pre match without group or one group): arr (search, replace) or str (if no group or one group)
    targets4 = {
        ### < 3.0
        r"\s+every_planet_army = \{\s*remove_army = yes\s*\}": [r"every_planet_army = \{\s*remove_army = yes\s*\}", r"remove_all_armies = yes"],
        r"\s(?:any|every|random)_neighbor_system = \{[^{}]+?\s+ignore_hyperlanes = (?:yes|no)\n?": [r"(_neighbor_system)( = \{[^{}]+?)\s+ignore_hyperlanes = (yes|no)\n?",
            lambda p: p.group(1) + p.group(2) if p.group(3) == "no" else p.group(1) + "_euclidean" + p.group(2)],
        ### 3.0.* (multiline)
        # r"\s+random_system_planet = \{\s*limit = \{\s*is_star = yes\s*\}": [r"(\s+)random_system_planet = \{\s*limit = \{\s*is_star = yes\s*\}", r"\1star = {"], # TODO works only on single star systems
        r"\s+random_system_planet = \{\s*limit = \{\s*is_primary_star = yes\s*\}": [r"(\s+)random_system_planet = \{\s*limit = \{\s*is_primary_star = yes\s*\}", r"\1star = {"], # TODO works only on single star systems
        r"\bcreate_leader = \{[^{}]+?\s+type = \w+": [r"(create_leader = \{[^{}]+?\s+)type = (\w+)", r"\1class = \2"],
        r"\bNO[RT] = \{\s*has_ethic = \"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic = \"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+\}": [r"NO[RT] = \{\s*has_ethic = \"?ethic_(?:(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic = \"?ethic_(?:(?:\1|\2)|fanatic_(?:\1|\2))\"?\s+\}", r"is_\1\2 = no"],
        r"\s*?(?:OR = \{)?\s+?has_ethic = \"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s+has_ethic = \"?ethic_(?:(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(?:pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s*\}?": [r"(\bOR = \{)?(\s*?\n*?\s*?)?(?(1)\t?)has_ethic = \"?ethic_(?:(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe)|fanatic_(pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe))\"?\s*?has_ethic = \"?ethic_(?:(?:\4|\3)|fanatic_(?:\4|\3))\"?\s*?(?(1)\})", r"\2is_\3\4 = yes"], # r"\4is_ethics_aligned = { ARG1 = \2\3 }",
        ### Boolean operator merge
        # NAND <=> OR = { NOT
        r"\s+OR = \{(?:\s*NOT = \{[^{}#]*?\})+\s*\}[ \t]*\n": [r"^(\s+)OR = \{\s*?\n(?:(\s+)NOT = \{\s*)?([^{}#]*?)\s*\}(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?", r"\1NAND = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15"], # up to 7 items (sub-trigger)
        # NOR <=> AND = { NOT
        r"\n\s+AND = \{\s(?:\s+NOT = \{\s*(?:[^{}#]+|\w+ = {[^{}#]+\})\s*\}){2,}\s+\}?": [r"(\n\s+)AND = \{\s*?(?:(\n\s+)NOT = \{\s*([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s+\})(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\4(?(4)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\7(?(7)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\10(?(10)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\13(?(13)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\16(?(16)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\19)?)?)?)?)?\1\}", r"\1NOR = {\2\3\5\6\8\9\11\12\14\15\17\18\20\21\1}"], # up to 7 items (sub-trigger)
        # NOR <=> (AND) = { NOT
        r"(?<![ \t]OR)\s+=\s*\{\s(?:[^{}#\n]+\n)*(?:\s+NO[RT] = \{\s*[^{}#]+?\s*\}){2,}": [r"(\n\s+)NO[RT] = \{\1(\s+)([^{}#]+?)\s+\}\s+NO[RT] = \{\s*([^{}#]+?)\s+\}", r"\1NOR = {\1\2\3\1\2\4\1}"], # only 2 items (sub-trigger) (?<!\sOR) Negative Lookbehind
        # NAND <=> NOT = { AND
        r"\n\s+NO[RT] = \{\s*AND = \{[^{}#]*?\}\s*\}": [r"(\t*)NO[RT] = \{\s*AND = \{[ \t]*\n(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?\s*\}[ \t]*\n", r"\1NAND = {\n\2\3\4\5"], # only 4 items (sub-trigger)
        # NOR <=> NOT = { OR
        r"\n\s+NO[RT] = \{\s*?OR = \{\s*(?:\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+?){2,}\}\s*\}": [r"(\t*)NO[RT] = \{\s*?OR = \{(\s+)(\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+)(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?\s*\}\s+", r"\1NOR = {\2\3\4\5\6\7"], # only right indent for 5 items (sub-trigger)
        ### End boolean operator merge
        r"\bany_country = \{[^{}#]*(?:has_event_chain|is_ai = no|is_zofe_compatible = yes|is_country_type = default|has_policy_flag|merg_is_default_empire = yes)": [r"any_country = (\{[^{}#]*(?:has_event_chain|is_ai = no|is_zofe_compatible = yes|is_country_type = default|has_policy_flag|merg_is_default_empire = yes))", r"any_playable_country = \1"],
        r"\s(?:every|random|count)_country = \{[^{}#]*limit = \{\s*(?:has_event_chain|is_ai = no|is_zofe_compatible = yes|is_country_type = default|has_special_project|merg_is_default_empire = yes)": [r"(\s(?:every|random|count))_country = (\{[^{}#]*limit = \{\s*(?:has_event_chain|is_ai = no|is_zofe_compatible = yes|is_country_type = default|has_special_project|merg_is_default_empire = yes))", r"\1_playable_country = \2"],

        r"\{\s+owner = \{\s*is_same_(?:empire|value) = [\w\._:]+\s*\}\s*\}": [r"\{\s+owner = \{\s*is_same_(?:empire|value) = ([\w\._:]+)\s*\}\s*\}", r"{ is_owned_by = \1 }"],
        r"NO[RT] = \{\s*(?:is_country_type = (?:awakened_)?fallen_empire\s+){2}\}": "is_fallen_empire = no",
        r"\n\s+(?:OR = \{)?\s{4,}(?:is_country_type = (?:awakened_)?fallen_empire\s+){2}\}?": [r"(\s+)(OR = \{)?(?(2)\s{4,}|(\s{4,}))is_country_type = (?:awakened_)?fallen_empire\s+is_country_type = (?:awakened_)?fallen_empire(?(2)\1\})", r"\1\3is_fallen_empire = yes"], 
        r"\bNO[RT] = \{\s*is_country_type = (?:default|awakened_fallen_empire)\s+is_country_type = (?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = no",
        r"\bOR = \{\s*is_country_type = (?:default|awakened_fallen_empire)\s+is_country_type = (?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = yes",
        r"\s+(?:OR = \{)?\s+(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+\}?": [r"(\s+)(OR = \{)?(?(2)\s+|(\s+))(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)(?(2)\1\})", r"\1\3is_synthetic_empire = yes"], # \s{4,}
        r"NO[RT] = \{\s*(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = auth_machine_intelligence|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+\}": "is_synthetic_empire = no",
        r"NO[RT] = \{\s*has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*\}": "is_homicidal = no",
        r"(?:OR = \{)\s{4,}?has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s*\}?": [r"(OR = \{\s*)?has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\"?(?(1)\s*\})", "is_homicidal = yes"],
        r"NOT = \{\s*check_variable = \{\s*which = \"?\w+\"?\s+value = [^{}#\s=]\s*\}\s*\}": [r"NOT = \{\s*(check_variable = \{\s*which = \"?\w+\"?\s+value) = ([^{}#\s=])\s*\}\s*\}", r"\1 != \2 }"],
        # r"change_species_characteristics = \{\s*?[^{}\n]*?
        r"[\s#]+new_pop_resource_requirement = \{[^{}]+\}\s*": [r"([\s#]+new_pop_resource_requirement = \{[^{}]+\}[ \t]*)", ""],
        # very rare, maybe put to cosmetic
        r"\s+any_system_within_border = \{\s*any_system_planet = \{\s*(?:\w+ = \{[\w\W]+?\}|[\w\W]+?)\s*\}\s*\}": [r"(\n?\s+)any_system_within_border = \{(\1\s*)any_system_planet = \{\1\s*([\w\W]+?)\s*\}\s*\1\}", r"\1any_planet_within_border = {\2\3\1}"],
        r"\s+any_system = \{\s*any_system_planet = \{\s*(?:\w+ = \{[\w\W]+?\}|[\w\W]+?)\s*\}\s*\}": [r"(\n?\s+)any_system = \{(\1\s*)any_system_planet = \{\1\s*([\w\W]+?)\s*\}\s*\1\}", r"\1any_galaxy_planet = {\2\3\1}"],
        # Near cosmetic
        r"\bcount_starbase_modules = \{\s+type = \w+\s+count\s*>\s*0\s+\}": [r"count_starbase_modules = \{\s+type = (\w+)\s+count\s*>\s*0\s+\}", r'has_starbase_module = \1'],
        r'\b(?:add_modifier = \{\s*modifier|set_timed_\w+ = \{\s*flag) = "?\w+"?\s+days\s*=\s*\d{2,}\s*\}': [
            r'\s+days\s*=\s*(\d{2,})\b',
            lambda p: " years = " + str(int(p.group(1))//360) + ' ' if int(p.group(1)) > 320 and int(p.group(1))%360 < 41 else (" months = " + str(int(p.group(1))//30) if int(p.group(1)) > 28 and int(p.group(1))%30 < 3 else " days = " + p.group(1))
        ],
        r"\brandom_list = \{\s+\d+ = \{\s*(?:(?:[\w:]+ = \{\s+\w+ = \{\n?[^{}#\n]+\}\s*\}|\w+ = \{\n?[^{}#\n]+\}|[^{}#\n]+)\s*\}\s+\d+ = \{\s*\}|\s*\}\s+\d+ = \{\s*(?:[\w:]+\s*=\s*\{\s+\w+\s*=\s*\{\n?[^{}#\n]+\}\s*\}|\w+ = \{\n?[^{}#\n]+\}|[^{}#\n]+)\s*\}\s*)\s*\}": [
            r"\brandom_list = \{\s+(?:(\d+) = \{\s+(\w+ = \{[^{}#\n]+\}|[^{}#\n]+)\s+\}\s+(\d+) = \{\s*\}|(\d+) = \{\s*\}\s+(\d+) = \{\s+(\w+ = \{[^{}#\n]+\}|[^{}#\n]+)\s+\})\s*", # r"random = { chance = \1\5 \2\6 "
            lambda p: "random = { chance = " + str(round((int(p.group(1))/(int(p.group(1))+int(p.group(3))) if p.group(1) and len(p.group(1)) > 0 else int(p.group(5))/(int(p.group(5))+int(p.group(4))))*100)) + ' ' + (p.group(2) or p.group(6)) + ' '
        ],
        ### >=3.1
        #but not used for starbases
        r"\bis_space_station = no\s*icon_frame = \d+":
            [r"(is_space_station = no\s*)icon_frame = ([1-9][0-2]?)",
             ("common/ship_sizes", lambda p:
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
        r"\{\s*which = \"?\w+\"?\s+value\s*[<=>]+\s*(?:prev|from|root|event_target:[^\.\s])+\s*\}": [r"(\s*which = \"?(\w+)\"?\s+value\s*[<=>]+\s*(prev|from|root|event_target:[^\.\s])+)", r"\1.\2"],
        r"\bset_variable = \{\s*which = \"?\w+\"?\s+value = (?:event_target:[^\d:{}#\s=\.]+|(prev\.?|from\.?|root|this|megastructure|planet|country|owner|space_owner|ship|pop|fleet|galactic_object|leader|army|ambient_object|species|pop_faction|war|federation|starbase|deposit|sector|archaeological_site|first_contact|spy_network|espionage_operation|espionage_asset)+)\s*\}": [r"set_variable = \{\s*which = \"?(\w+)\"?\s+value = (event_target:\w+|\w+)\s*\}", r"set_variable = { which = \1 value = \2.\1 }"],
        r"\s+spawn_megastructure = \{[^{}#]+?location = [\w\._:]+": [r"(spawn_megastructure = \{[^{}#]+?)location = ([\w\._:]+)", r"\1coords_from = \2"],
        r"\s+modifier = \{\s*mult\b": [r"\bmult\b", "factor"],
        ### >= 3.2
        r"\bNO[RT] = \{\s*is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex))?\s*\}": [r"\bNO[RT] = \{\s*is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_cybrex))?\s*\}", r"is_artificial = no"],
        r"\n\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex))?\b": [r"\bis_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_cybrex))?\b", r"is_artificial = yes"],
        r"\n\s+possible = \{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)(?:drone|worker|specialist|ruler)_job_check_trigger = yes\s*": [r"(\s+)(possible = \{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?))(drone|worker|specialist|ruler)_job_check_trigger = yes\s*", ("common/pop_jobs", r"\1possible_precalc = can_fill_\4_job\1\2")], # only with 6 possible prior lines
        r"(?:[^b]\n\n|[^b][^b]\n)\s+possible = \{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)complex_specialist_job_check_trigger = yes\s*": [r"\n(\s+)(possible = \{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)complex_specialist_job_check_trigger = yes\s*)", ("common/pop_jobs", r"\1possible_precalc = can_fill_specialist_job\1\2")], # only with 6 possible prior lines
        ### >= 3.3
        r"(?:random_weight|pop_attraction(_tag)?|country_attraction)\s+value\s*=": [r"\bvalue\b", ("common/ethics", 'base')],
        #r"\n\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}": [r"([\t ]+)NO[TR] = \{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR] = \{\s*([^{}#\r\n]+)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"], not valid if in OR
        r"\bany_\w+ = \{[^{}]+?\bcount\s*[<=>]+\s*[^{}\s]+\s+[^{}]*\}": [r"\bany_(\w+) = \{\s*(?:([^{}]+?)\s+(\bcount\s*[<=>]+\s*[^{}\s]+)|(\bcount\s*[<=>]+\s*[^{}\s]+)\s+([^{}]*))\s+\}", r"count_\1 = { limit = { \2\5 } \3\4 }"], # too rare!? only simple supported TODO
        ### >= 3.4
        r"\n(?:\t| {4})empire_limit = \{\s+base = [\w\W]+\n(?:\t| {4})\}": [r"(\s+)empire_limit = \{(\s+)base = (\d+\s+max = \d+|\d+)[\w\W]+?(?(1)\s+\})\s+\}", ('common/ship_sizes', r'\1ai_ship_data = {\2min = \3\1}')],
        r"\bpotential = \{\s+always = no\s+\}": ["potential", ('common/armies', 'potential_country')],
        r"(?:\t| {4})potential = \{\s+(?:exists = )?owner[\w\W]+\n(?:\t| {4})\}": [r"potential = \{\s+(?:exists = owner)?(\s+)owner = \{\s+([\w\W]+?)(?(1)\s+\})\s+\}", ("common/armies", r'potential_country = { \2 }')],
        r"\s+construction_block(?:s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no": [r"construction_block(s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no", ("common/megastructures", 'construction_blocks_and_blocked_by = self_type')],
        r"construction_blocks_others = no": [r"construction_blocks_others = no", ("common/megastructures", 'construction_blocks_and_blocked_by = none')],
        # r"construction_blocked_by_others = no": ("common/megastructures", 'construction_blocks_and_blocked_by = self_type'),
        r"(?:contact|any_playable)_country\s*=\s*{\s+(?:NOT = \{\s+)?(?:any|count)_owned_(?:fleet|ship) = \{": [r"(any|count)_owned_(fleet|ship) =", r"\1_controlled_\2 ="], # only playable empire!?
        r"\s+(?:any|every|random)_(?:system|planet) = \{(?:\s+limit = \{)?\s+has_owner = yes\s+is_owned_by": [r"(any|every|random)_(system|planet) =", r"\1_\2_within_border ="],
        r"\b(NO[RT] = \{\s*(has_trait = trait_(?:zombie|nerve_stapled)\s+){2}\}|(NOT = \{\s*has_trait = trait_(?:zombie|nerve_stapled)\s+\}){2})": "can_think = no",
        r"(\bOR = \{\s*(has_trait = trait_(?:zombie|nerve_stapled)\s+){2}\})": "can_think = yes",
        r"(\bOR = \{\s*(species_portrait = human(?:_legacy)?\s+){2}\})": "is_human_species = yes",
        r"\b(?:species_portrait = human(?:_legacy)?\s+){1,2}": [r"species_portrait = human(?:_legacy)?(\s+)(?:species_portrait = human(?:_legacy)?)?", r"is_human_species = yes\1"],
        r"\bvalue = subject_loyalty_effects\s+\}\s+\}": [r"(subject_loyalty_effects\s+\})(\s+)\}", ('common/agreement_presets', r"\1\2\t{ key = protectorate value = subject_is_not_protectorate }\2}")],
        ### >= 3.5
        r"\bany_system_planet = \{[^{}#]*(?:has_owner = yes|is_colony = yes|exists = owner)\s+": [r"any_system_planet = (\{[^{}#]*)(?:has_owner = yes|is_colony = yes|exists = owner)\s+", r"any_system_colony = \1"],
        r"\s(?:every|random|count|ordered)_system_planet = \{[^{}#]*limit = \{\s*(?:has_owner = yes|is_colony = yes|exists = owner)\s+": [r"(every|random|count)_system_planet = (\{[^{}#]*limit = \{\s*)(?:has_owner = yes|is_colony = yes|exists = owner)\s+", r"\1_system_colony = \2"],
        r"(\bOR = \{\s+(has_trait = trait_(?:plantoid|lithoid)_budding\s+){2}\})": "has_budding_trait = yes",
        r"_pop = \{\s+unemploy_pop = yes\s+kill_pop = yes": [r"(_pop = \{\s+)unemploy_pop = yes\s+(kill_pop = yes)", r"\1\2"], # ghost pop bug fixed
        ### >= 3.6
        r"\bis_triggered_only = yes\s+trigger = \{\s+always = no": [r"(\s+)(trigger = \{\s+always = no)", ('events', r'\1is_test_event = yes\1\2')],
        r'slot\s*=\s*\"?(?:SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template\s*=\s*\"?AUTOCANNON_\d\"?': [r'(=\s*\"?(SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template\s*=\s*)\"?(AUTOCANNON_\d)\"?', ('common/global_ship_designs', r'\1"\2_\3"')],
        r"\bhas_(?:population|colonization|migration)_control = \{\s+value =": ["value", 'type'],
        r"(\bOR = \{\s*(has_trait = trait_(?:latent_)?psionic\s+){2}\})": "has_psionic_species_trait = yes",
    }

if also_old:
    ## 2.0
    # planet trigger fortification_health was removed
    ## 2.2
    targets3[r"\s+(?:outliner_planet_type|tile_set) = \w+\s*"] = ("common/planet_classes", "")
    targets3[r"\b(?:add|set)_blocker = \"?tb_(\w+)\"?"] = r"add_deposit = d_\1" # More concrete? r"add_blocker = { type = d_\1 blocked_deposit = none }" 
    targets3[r"\btb_(\w+)"] = r"d_\1"
    targets3[r"\b(building_capital)(?:_\d)\b"] = r"\1"
    targets3[r"\b(betharian_power_plant)\b"] = r"building_\1"
    targets3[r"\b(building_hydroponics_farm)_[12]\b"] = r"\1"
    targets3[r"\bbuilding_hydroponics_farm_[34]\b"] = r"building_food_processing_facility"
    targets3[r"\bbuilding_hydroponics_farm_[5]\b"] = r"building_food_processing_center"
    targets3[r"\bbuilding_power_plant_[12]\b"] = r"building_energy_grid"
    targets3[r"\bbuilding_power_plant_[345]\b"] = r"building_energy_nexus"
    targets3[r"\bbuilding_mining_network_[12]\b"] = "building_mineral_purification_plant"
    targets3[r"\bbuilding_mining_network_[345]\b"] = "building_mineral_purification_hub"
    targets3[r"(?<!add_resource = \{)(\s+)(%s)\s*([<=>]+\s*-?\s*(?:@\w+|\d+))\1(?!(%s))" % (resource_items, resource_items)] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1has_resource = { type = \2 amount \3 }")
    # not sure because multiline
    # targets3[r"(?<!add_resource = \{)(\s+)(%s)\s*([<=>]+\s*-?\s*(?:@\w+|\d+))" % resource_items] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1has_resource = { type = \2 amount \3 }")
    # tmp fix
    # targets3[r"\bhas_resource = \{ type = (%s) amount( = (?:\d+|@\w+)) \}" % resource_items] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1\2 ")

if not keep_default_country_trigger:
    targets4[r"\s(?:every|random|count|any)_playable_country = \{[^{}#]*(?:limit = \{\s*)?(?:is_country_type = default|CmtTriggerIsPlayableEmpire = yes|is_zofe_compatible = yes|merg_is_default_empire = yes)\s*"] = [r"((?:every|random|count|any)_playable_country = \{[^{}#]*?(?:limit = \{\s*)?)(?:is_country_type = default|CmtTriggerIsPlayableEmpire = yes|is_zofe_compatible = yes|merg_is_default_empire = yes)\s*", r"\1"]

if code_cosmetic and not only_warning:
    triggerScopes = r"limit|trigger|any_\w+|leader|owner|PREV|FROM|ROOT|THIS|event_target:\w+"
    targets3[r"((?:[<=>]\s|\.|PREV|FROM|Prev|From)+(PREV|FROM|ROOT|THIS|Prev|From|Root|This)+)\b"] = lambda p: p.group(1).lower()
    targets3[r" {4}"] = r"\t"  # r" {4}": r"\t", # convert space to tabs
    targets3[r"^(\s+)limit = \{\s*\}"] = r"\1# limit = { }"
    targets3[r'\bhost_has_dlc = "([\s\w]+)"'] = lambda p: p.group(0) if p.group(1) and p.group(1) in {"Anniversary Portraits", "Apocalypse", "Arachnoid Portrait Pack", "Creatures of the Void Portrait Pack", "Megacorp", "Utopia"} else "has_" + {
            "Ancient Relics Story Pack": "ancrel",
            "Aquatics Species Pack": "aquatics",
            "Distant Stars Story Pack": "distar",
            "Federations": "federations_dlc",
            "Humanoids Species Pack": "humanoids",
            "Leviathans Story Pack": "leviathans",
            "Lithoids Species Pack": "lithoids",
            "Necroids Species Pack": "necroids",
            "Nemesis": "nemesis",
            "Overlord": "overlord_dlc",
            "Plantoids Species Pack": "plantoids",
            "Synthetic Dawn Story Pack": "synthethic_dawn",
            "Toxoids Species Pack": "toxoids",
         }[p.group(1)] + " = yes" 
    # targets3[r"\s*days\s*=\s*-1\s*"] = ' ' # still needed to execute immediately
    # targets3[r"# {1,3}([a-z])([a-z]+ +[^;:\s#=<>]+)"] = lambda p: "# "+p.group(1).upper() + p.group(2) # format comment
    targets3[r"#([^\-\s#])"] = r"# \1" # r"#([^\s#])": r"# \1", # format comment
    #  targets3[r"# +([A-Z][^\n=<>{}\[\]# ]+? [\w,\.;\'\//+\- ()&]+? \w+ \w+ \w+)$"] = r"# \1." # set comment punctuation mark
    targets3[r"# ([a-z])(\w+ +[^;:\s#=<>]+ [^\n]+?[\.!?])$"] = lambda p: "# "+p.group(1).upper() + p.group(2) # format comment
    # NOT NUM triggers. TODO <> ?
    targets3[r"\bNOT = \{\s*(num_\w+|\w+?(?:_passed)) = (\d+)\s*\}"] = r"\1 != \2"
    targets3[r"\bfleet = \{\s*(?:destroy|delete)_fleet = this\s*\}"] = r"destroy_fleet = fleet" # TODO may extend
    ## targets3[r"# *([A-Z][\w ={}]+?)\.$"] = r"# \1" # remove comment punctuation mark
    targets4[r"\n{3,}"] = "\n\n" # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    # targets4[r"(?:_system|_planet)? = \{\s+(?:limit = \{})?\bexists = (?:space_)?owner\s+is_owned_by\b"] = [r"exists = (?:space_)?owner(\s+)is_owned_by", r"has_owner = yes\1is_owned_by"] # only for planet galactic_object
    targets4[r'_event = \{\s+id = \"[\w.]+\"'] = [r'\bid = \"([\w.]+)\"', ("events", r"id = \1")] # trim id quote marks

    targets4[r"\n\s+\}\n\s+else"] = [r"\}\s*else", "} else"] # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    # WARNING not valid if in OR: NOR <=> AND = { NOT NOT } , # only 2 items (sub-trigger)
    targets4[r"\n\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}"] = [r"([\t ]+)NO[TR] = \{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR] = \{\s*([^{}#\r\n]+)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"]
    targets4[r"\brandom_country = \{\s*limit = \{\s*is_country_type = global_event\s*\}"] = "event_target:global_event_country = {"
     # unnecessary AND
    targets4[r"\b((?:%s) = \{(\s+)(?:AND|this) = \{(?:\2\t[^\n]+)+\2\}\n)" % triggerScopes] = [r"(%s) = \{\n(\s+)(?:AND|this) = \{\n\t(\2[^\n]+\n)(?(3)\t)(\2[^\n]+\n)?(?(4)\t)(\2[^\n]+\n)?(?(5)\t)(\2[^\n]+\n)?(?(6)\t)(\2[^\n]+\n)?(?(7)\t)(\2[^\n]+\n)?(?(8)\t)(\2[^\n]+\n)?(?(9)\t)(\2[^\n]+\n)?(?(10)\t)(\2[^\n]+\n)?(?(11)\t)(\2[^\n]+\n)?(?(12)\t)(\2[^\n]+\n)?(?(13)\t)(\2[^\n]+\n)?(?(14)\t)(\2[^\n]+\n)?(?(15)\t)(\2[^\n]+\n)?(?(16)\t)(\2[^\n]+\n)?(?(17)\t)(\2[^\n]+\n)?(?(18)\t)(\2[^\n]+\n)?(?(19)\t)(\2[^\n]+\n)?(?(20)\t)(\2[^\n]+\n)?\2\}\n" % triggerScopes, r"\1 = {\n\3\4\5\6\7\8\9\10\11\12\13\14\15\16\17\18\19\20\21"]
    targets4[r"(?:\s+add_resource = \{\s*\w+ = [^{}#]+\s*\})+"] = [r"(\s+add_resource = \{)(\s*\w+ = [^\s{}#]+)\s*\}\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\}(?(3)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(4)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(5)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(6)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(7)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?", r"\1\2\3\4\5\6\7 }"] # 6 items
    ### 3.4
    targets4[r"\bNO[RT] = \{\s*has_modifier = doomsday_\d[\w\s=]+\}"] = [r"NO[RT] = \{\s*(has_modifier = doomsday_\d\s+){5}\}", "is_doomsday_planet = no"]
    targets4[r"\bOR = \{\s*has_modifier = doomsday_\d[\w\s=]+\}"] = [r"OR = \{\s*(has_modifier = doomsday_\d\s+){5}\}", "is_doomsday_planet = yes"]

# BETA WIP still only event folder
# like targets3 but later
if mergerofrules:
    # without is_country_type_with_subjects & without is_fallen_empire = yes
    targets4[r"\b(?:(?:(?:is_country_type = default|merg_is_default_empire = yes)\s+(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes))|(?:(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)\s+(?:is_country_type = default|merg_is_default_empire = yes))|(?:(?:is_country_type = default|merg_is_default_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)\s+(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)))"] = [r"\b((?:is_country_type = default|merg_is_default_empire = yes|is_country_type = fallen_empire|merg_is_fallen_empire = yes|is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)(\s+)){2,}", (exlude_trigger_folder, r"merg_is_standard_empire = yes\2")]
    # with is_country_type_with_subjects & without AFE but with is_fallen_empire 
    targets4[r"\b(?:(?:(?:is_country_type = default|merg_is_default_empire = yes|is_country_type_with_subjects = yes)\s+is_fallen_empire = yes)|(?:is_fallen_empire = yes\s+(?:is_country_type = default|merg_is_default_empire = yes|is_country_type_with_subjects = yes)))"] = [r"\b((?:is_country_type = default|merg_is_default_empire = yes|is_fallen_empire = yes|is_country_type_with_subjects = yes)(\s+)){2,}", (exlude_trigger_folder, r"merg_is_standard_empire = yes\2")]
    targets4[r"\s+(?:OR = \{)?\s+(?:has_country_flag = synthetic_empire\s+owner_species = \{ has_trait = trait_mechanical \}|owner_species = \{ has_trait = trait_mechanical \}\s+has_country_flag = synthetic_empire)\s+\}?"] = [r"(\s+)(OR = \{)?(\s+)(?:has_country_flag = synthetic_empire\s+owner_species = \{ has_trait = trait_mechanical \}|owner_species = \{ has_trait = trait_mechanical \}\s+has_country_flag = synthetic_empire)(?(2)\1\})", (exlude_trigger_folder, r"\1\3is_mechanical_empire = yes")]
    targets4[r"\s+(?:OR = \{)?\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = auth_machine_intelligence)\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = auth_machine_intelligence)\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = auth_machine_intelligence)\s+\}?"] = [r"(\s+)(OR = \{)?(\s+)(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = auth_machine_intelligence|is_machine_empire = yes))\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = auth_machine_intelligence|is_machine_empire = yes))\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = auth_machine_intelligence|is_machine_empire = yes))(?(2)\1\})", (exlude_trigger_folder, r"\1\3is_robot_empire = yes")]
    targets4[r"NO[RT] = \{\s*(?:merg_is_(?:fallen_empire|awakened_fe) = yes\s+){2}\}"] = "is_fallen_empire = no"
    targets4[r"\n\s+(?:OR = \{)?\s+(?:merg_is_(?:fallen_empire|awakened_fe) = yes\s+){2}\}?"] = [r"(\s+)(OR = \{)?(?(2)\s+|(\s+))merg_is_(?:fallen_empire|awakened_fe) = yes\s+merg_is_(?:fallen_empire|awakened_fe) = yes(?(2)\1\})", r"\1\3is_fallen_empire = yes"]
    targets4[r"\bNO[RT] = \{\s*merg_is_(?:default_empire|awakened_fe) = yes\s+merg_is_(?:default_empire|awakened_fe) = yes\s+\}"] = "is_country_type_with_subjects = no"
    targets4[r"\bOR = \{\s*merg_is_(?:default_empire|awakened_fe) = yes\s+merg_is_(?:default_empire|awakened_fe) = yes\s+\}"] = "is_country_type_with_subjects = yes"
    targets3[r"\bis_country_type = default\b"] = (exlude_trigger_folder, "merg_is_default_empire = yes")
    targets3[r"\bis_country_type = fallen_empire\b"] = (exlude_trigger_folder, "merg_is_fallen_empire = yes")
    targets3[r"\bis_country_type = awakened_fallen_empire\b"] = (exlude_trigger_folder, "merg_is_awakened_fe = yes")
    targets3[r"\bis_planet_class = pc_habitat\b"] = (exlude_trigger_folder, "merg_is_habitat = yes")
    targets3[r"\bhas_ethic = ethic_gestalt_consciousness\b"] = (exlude_trigger_folder, "is_gestalt = yes")
    targets3[r"\bhas_authority = auth_machine_intelligence\b"] = (exlude_trigger_folder, "is_machine_empire = yes")
    targets3[r"\bhas_authority = auth_hive_mind\b"] = (exlude_trigger_folder, "is_hive_empire = yes")
    targets3[r"\bhas_authority = auth_corporate\b"] = (exlude_trigger_folder, "is_megacorp = yes")
    targets3[r"\bowner_species = \{ has_trait = trait_cybernetic \}\b"] = (exlude_trigger_folder, "is_cyborg_empire = yes")
    # targets31 = [(re.compile(k, flags=0), targets31[k]) for k in targets31]


if debug_mode:
    import datetime
    # start_time = datetime.datetime.now()
    start_time = 0
    
### Pre-Compile regexps
targets3 = [(re.compile(k, flags=0), targets3[k]) for k in targets3]
targets4 = [(re.compile(k, flags=re.I), targets4[k]) for k in targets4]
# print(datetime.datetime.now() - start_time)
# exit()


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
    if debug_mode: global start_time
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

    if debug_mode:
        print("\tLoading folder", mod_path)
        start_time = datetime.datetime.now()

    # if os.path.isfile(mod_path + os.sep + 'descriptor.mod'):
    if os.path.exists(os.path.join(mod_path, 'descriptor.mod')):
        files = glob.iglob(mod_path + '/**', recursive=True)  # '\\*.txt'
        modfix(files)
    else:
        "We have a main folder"
        # folders = [f for f in os.listdir(mod_path) if os.path.isdir(os.path.join(mod_path, f))]
        folders = glob.iglob(mod_path + "/*/", recursive=True)
        for _f in folders:
            if os.path.exists(os.path.join(_f, 'descriptor.mod')):
                mod_path = _f
                mod_outpath = os.path.join(mod_outpath, _f)
                print(mod_path)
                files = glob.iglob(mod_path + '/**', recursive=True)  # '\\*.txt'
                modfix(files)


def modfix(file_list):
    # global mod_path, mod_outpath
    # print(targets3)
    if debug_mode: print("mod_outpath", mod_outpath)
    subfolder = ''
    for _file in file_list:
        if os.path.isfile(_file) and _file.endswith('.txt'):
            subfolder = os.path.relpath(_file, mod_path)
            file_contents = ""
            print("\tCheck file:", _file.encode(errors='replace'))
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
                subfolder = subfolder.replace("\\", "/")
                out = ""
                changed = False
                for i, line in enumerate(file_contents):
                    if len(line) > 8:
                        # for line in file_contents:
                        # if subfolder in "prescripted_countries":
                        #     print(line.strip().encode(errors='replace'))
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
                                print(" WARNING outdated removed syntax%s: %s in line %i file %s\n" % (msg, rt.group(0).encode(errors='replace'), i, basename))
                        
                        # for pattern, repl in targets3.items(): old dict way
                        for pattern in targets3: # new list way
                            repl = pattern[1]
                            pattern = pattern[0]
                            folder = None
                            # check valid folder
                            rt = False
                            # File name check
                            if isinstance(repl, dict):
                                # is a 3 tuple
                                file, repl = list(repl.items())[0]

                                if debug_mode:
                                    print("targets3", line.strip().encode(errors='replace'))
                                    print(pattern, repl, file)

                                if file in basename:
                                    if debug_mode: print("\tFILE match:", file, basename)
                                    folder, repl, rt = repl
                                else:
                                    folder, rt, repl = repl
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                elif subfolder in folder:
                                    rt = True
                                else: rt = False
                            # Folder check
                            elif isinstance(repl, tuple):
                                folder, repl = repl
                                # print("subfolder", subfolder)
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                # elif subfolder in folder:
                                elif isinstance(folder, str):
                                    if subfolder in folder:
                                        rt = True
                                        if debug_mode: print(folder)
                                elif isinstance(folder, re.Pattern):
                                    if folder.search(subfolder):
                                        # print("Check folder (regexp) True", subfolder, repl)
                                        rt = True
                                    elif debug_mode: print("Folder EXCLUDED:", subfolder, repl)
                                else: rt = False
                            else: rt = True
                            if rt: # , flags=re.I # , count=0, flags=0
                                rt = pattern.search(line) # , flags=re.I
                                if rt:
                                    line = pattern.sub(repl, line) # , flags=re.I                                  
                                    # line = line.replace(t, r)
                                    changed = True
                                    print("\tUpdated file: %s at line %i with %s\n" % (basename, i, line.strip().encode(errors='replace')))
                                #elif debug_mode and isinstance(folder, re.Pattern): print("DEBUG Match targets3:", pattern, repl, type(repl), line.strip().encode(errors='replace'))

                    out += line

                # for pattern, repl in targets4.items(): old dict way
                for pattern in targets4: # new list way
                    repl = pattern[1]
                    pattern = pattern[0]
                    targets = pattern.findall(out)
                    if targets and len(targets) > 0:
                        if debug_mode:
                            print("targets4", targets, type(targets))
                        for tar in targets:
                            # check valid folder
                            rt = False
                            replace = repl
                            if isinstance(repl, list) and isinstance(repl[1], tuple):
                                replace = repl.copy()
                                # folder = repl[1][0]
                                # replace[1] = repl[1][1]
                                folder, replace[1] = repl[1]
                                rt = False
                                if debug_mode: print(type(replace), replace, replace[1])
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                            if debug_mode: print(folder)
                                            break
                                elif isinstance(folder, str):
                                    if subfolder in folder:
                                        rt = True
                                        if debug_mode: print(folder)
                                elif isinstance(folder, re.Pattern) and folder.search(subfolder):
                                    # print("Check folder (regexp)", subfolder)
                                    rt = True
                                else: rt = False
                            else: rt = True
                            if rt:
                                # print(type(repl), tar, type(tar), subfolder)
                                if isinstance(repl, list):
                                    if isinstance(tar, tuple):
                                        tar = tar[0] # Take only first group
                                        # print("ONLY GRP1:", type(replace), replace)
                                    replace = re.sub(replace[0], replace[1], tar, flags=re.I|re.M|re.A)
                                if isinstance(repl, str) or (not isinstance(tar, tuple) and tar in out and tar != replace):
                                    print("Match:\n", tar)
                                    if isinstance(tar, tuple):
                                        tar = tar[0] # Take only first group
                                        if debug_mode: print("\tFROM GROUP1:\n", pattern)
                                    elif debug_mode: print("\tFROM:\n", pattern)
                                    print("Multiline replace:\n", replace) # repr(
                                    out = out.replace(tar, replace)
                                    changed = True
                                elif debug_mode:
                                    print("DEBUG Blind Match:", tar, repl, type(repl), replace)

                if changed and not only_warning:
                    structure = os.path.normpath(os.path.join(mod_outpath, subfolder))
                    out_file = os.path.join(structure, basename)
                    print('\tWRITE FILE:', out_file.encode(errors='replace'))
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
    if debug_mode: print(datetime.datetime.now() - start_time)

parse_dir() # mod_path, mod_outpath
# input("\nPRESS ANY KEY TO EXIT!")
