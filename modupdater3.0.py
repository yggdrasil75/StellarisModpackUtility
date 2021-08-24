###    @author FirePrince
###    @revision 2021/08/24

#============== Import libs ===============
import os, sys  # io for high level usage
import glob
import re

# from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

#============== Initialise global variables ===============
mod_path = os.path.expanduser('~') + '/Documents/Paradox Interactive/Stellaris/mod'

mod_outpath = ""

if not sys.version_info.major == 3 and sys.version_info.minor >= 6:
    print("Python 3.6 or higher is required.")
    print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
    sys.exit(1)

# 3.0.*
removedTargets = {
    r"\sproduced_energy",
    r"\s(ship|army|colony|station)_maintenance",
    r"\s(construction|trade|federation)_expenses",
    r"\s+can_support_spaceport\s*=\s*(yes|no)" # < 2.0
}

# targets2 = {
#     r"MACHINE_species_trait_points_add = \d" : ["MACHINE_species_trait_points_add ="," ROBOT_species_trait_points_add = ",""],
#     r"job_replicator_add = \d":["if = {limit = {has_authority = auth_machine_intelligence} job_replicator_add = ", "} if = {limit = {has_country_flag = synthetic_empire} job_roboticist_add = ","}"]
# }

# 3.0.* (only one-liner)
targets3 = {
    r"\tsurveyed\s*=\s*\{": r"\tset_surveyed = {",
    r"(\s+)set_surveyed\s*=\s*(yes|no)": r"\1surveyed = \2",
    r"has_completed_special_project\s+": "has_completed_special_project_in_log ",
    r"has_failed_special_project\s+": "has_failed_special_project_in_log ",
    r"species\s*=\s*last_created(\s)": r"species = last_created_species\1",
    r"owner\s*=\s*last_created(\s)": r"owner = last_created_country\1",
    r"(any|every|random)_pop\s*=": r"\1_owned_pop =",
    r"(\s)(any|every|random)_planet\s*=": r"\1\2_galaxy_planet =",
    r"(\s)(any|every|random)_ship\s*=": r"\1\2_galaxy_fleet =",
    r"(any|every|random|count)_sector\s*=": r"\1_galaxy_sector =",
    r"(any|every|random)_war_(attacker|defender)\s*=": r"\1_\2 =",
    r"(any|every|random|count)_recruited_leader\s*=": r"\1_owned_leader =",
    r"count_planets\s*": "count_galaxy_planet ",
    r"count_ships\s*": "count_galaxy_fleet ",
    r"count(_owned)?_pops\s*": "count_owned_pop ",
    r"count_(owned|fleet)_ships\s*": "count_owned_ship ", # 2.7
    # "any_ship_in_system": "any_fleet_in_system", # works only sure for single size fleets
    r"spawn_megastructure\s*=\s*\{([^{}#]+)location\s*=": r"spawn_megastructure = {\1planet =",
    r"\s+planet\s*=\s*(solar_system|planet)[\s\n\r]*": "",  # REMOVE
    r"any_system_within_border\s*=\s*\{\s*any_system_planet\s*=": "any_planet_within_border =",
    r"is_country_type\s*=\s*default\s+has_monthly_income\s*=\s*\{\s*resource = (\w+) value <=? \d": r"no_resource_for_component = { RESOURCE = \1",
    r"([^\._])(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*(\w+)\s*\}": r"\1is_owned_by = \2",
    r"(\s+)exists\s*=\s*(solar_system|planet)\.(?:space_)?owner": r"\1has_owner = yes",
    # code optss only
    r"(\s+)NOT\s*=\s*\{\s*([^\s]+)\s*=\s*yes\s*\}": r"\1\2 = no",
    ## somewhat older
    r"(\s+)ship_upkeep_mult\s*=": r"\1ships_upkeep_mult =",     
    r"(\s+)add_(energy|unity|food|minerals|influence|alloys|consumer_goods|exotic_gases|volatile_motes|rare_crystals|sr_living_metal|sr_dark_matter|sr_zro)\s*=\s*(\d+|@\w+)": r"\1add_resource = { \2 = \3 }"
}


# 3.0.* (multiline)
targets4 = {
    r"\screate_leader\s*=\s*\{[^{}]+?type\s*=\s*\w+": [r"(\screate_leader\s*=\s*\{[^{}]+?\s+)type\s*=\s*(\w+)", r"\1class = \2"],
    # r"\s*\n{2,}": "\n\n", # remove surplus lines
    ### Boolean operator merge
    # NAND <=> OR = { NOT
    r"\s+OR\s*=\s*\{(?:\s*NOT\s*=\s*\{[^{}#]*?\})+\s*\}[ \t]*\n": [r"^(\s+)OR\s*=\s*\{\s*?\n(?:(\s+)NOT\s*=\s*\{\s*)?([^{}#]*?)\s*\}(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]*?)\s*\})?", r"\1NAND = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15"], # up to 7 items (sub-trigger)
    # NOR <=> AND = { NOT 
    r"\s+AND\s*=\s*\{\s+(?:\s+NOT\s*=\s*\{\s*(?:[^{}#]+|\w+\s*=\s*{[^{}#]+\s*\})\s*\}){2,}": [r"^(\s+)AND\s*=\s*\{\s*?\n(?:(\s+)NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?(?:(\s+)?NOT\s*=\s*\{\s*([^{}#]+|\w+\s*=\s*\{[^{}#]+\s*\})\s*\})?", r"\1NOR = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15"], # up to 7 items (sub-trigger)
    # NOR <=> (AND) = { NOT 
    r"(?<![ \t]OR)\s+=\s*\{\s+(?:[^{}#\n]+\n)*(?:\s+NO[RT]\s*=\s*\{\s*[^{}#]+?\s*\}){2,}": [r"(\t*)NO[RT]\s*=\s*\{\s*([^{}#]+?)\s*\}\s*NO[RT]\s*=\s*\{\s*([^{}#]+?)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"], # only 2 items (sub-trigger) (?<!\sOR) Negative Lookbehind
    # NAND <=> NOT = { AND
    r"\s+NO[RT]\s*=\s*\{\s*AND\s*=\s*\{[^{}#]*?\}\s*\}": [r"(\t*)NO[RT]\s*=\s*\{\s*AND\s*=\s*\{[ \t]*\n(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?\s*\}[ \t]*\n", r"\1NAND = {\n\2\3\4\5"], # only 4 items (sub-trigger)
    # NOR <=> NOT = { OR
    r"\s+NO[RT]\s*=\s*\{\s*OR\s*=\s*\{[^{}#]*?\}\s*\}": [r"(\t*)NO[RT]\s*=\s*\{\s*OR\s*=\s*\{[ \t]*\n(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?\t([^{}#]*?)[ \t]*\}[ \t]*\n", r"\1NOR = {\n\2\3\4\5\6"], # only right indent for 5 items (sub-trigger)
    ### End boolean operator merge
    r"\sany_country\s*=\s*\{[^{}#]*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default)": [r"(\s)any_country\s*=\s*(\{[^{}#]*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default))", r"\1any_playable_country = \2"],
    r"\s(?:every|random|count)_country\s*=\s*\{[^{}#]*limit\s*=\s*\{\s*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default)": [r"(\s(?:every|random|count))_country\s*=\s*(\{[^{}#]*limit\s*=\s*\{\s*(?:has_event_chain|is_ai\s*=\s*no|is_country_type\s*=\s*default))", r"\1_playable_country = \2"],
    r"\{\s+(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*[\w\._:]+\s*\}\s*\}": [r"\{\s+(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*([\w\._:]+)\s*\}\s*\}", r"{ is_owned_by = \1 }"],
    r"NO[RT]\s*=\s*\{\s{3,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s{3,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s{3,}\}": "is_fallen_empire = no",
    r"OR\s*=\s*\{\s{3,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s{3,}is_country_type\s*=\s*(?:fallen_empire|awakened_fallen_empire)\s{3,}\}": "is_fallen_empire = yes",
    r"NO[RT]\s*=\s*\{\s*is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = no",
    r"OR\s*=\s*\{\s*is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+is_country_type\s*=\s*(?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = yes",
    r"NO[RT]\s*=\s*\{\s*(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+\}": "is_synthetic_empire = no",
    r"OR\s*=\s*\{\s*(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+(?:has_authority\s*=\s*auth_machine_intelligence|has_country_flag\s*=\s*synthetic_empire)\s+\}": "is_synthetic_empire = yes",
    r"NO[RT]\s*=\s*\{\s*has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s*has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s*has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s*\}": "is_homicidal = no",
    r"OR\s*=\s*\{\s*has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s+has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s+has_valid_civic\s*=\s*(?:civic_fanatic_purifiers|civic_machine_terminator|civic_hive_devouring_swarm)\s*\}": "is_homicidal = yes"
}

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
    print("Welcome to Stellaris Mod-Updater-3.0 by F1r3Pr1nc3!")

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
            print("\tCheck file:",_file)
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
                            rt = re.search(rt, line, flags=re.I)
                            if rt:
                                print("\tWARNING outdated removed trigger: %s in line %i file %s" % (
                                    rt.group(0), i, basename))
                        for pattern, repl in targets3.items():
                            # print(line)
                            # print(pattern, repl)
                            if re.search(pattern, line, flags=re.I):
                                # , count=0, flags=0
                                line = re.sub(pattern, repl, line, flags=re.I)
                                # line = line.replace(t, r)
                                changed = True
                                print("\tUpdated file: %s at line %i with %s" % (basename, i, line.strip()))
                    out += line

                for pattern, repl in targets4.items():
                    targets = re.findall(pattern, out, flags=re.I)
                    # if targets:
                    if len(targets) > 0:
                        # print(targets, type(targets))
                        for tar in targets:
                            replace = repl
                            # print(type(repl), tar, type(tar))
                            print("Match:\n", tar)
                            if type(repl) == list:
                                replace = re.sub(repl[0], repl[1], tar, flags=re.I|re.M|re.A)
                            if type(repl) == str or (type(tar) != tuple and tar in out):
                                print("Multiline replace:\n", replace) # repr(
                                out = out.replace(tar, replace)
                                changed = True

                if changed:
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
    print("Done!")


parse_dir()  # mod_path, mod_outpath
