
import os  # io for high level usage
import glob
import re
# from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

mod_path = os.path.expanduser('~') + '/Documents/Paradox Interactive/Stellaris/mod'
# mod_path = 'c:/Games/Settings/Mods/CrisisManagers (all)'
if not os.path.isdir(mod_path):
    mod_path = os.getcwd()
mod_outpath = mod_path

# 3.0.*
removedTargets = {
    r"\sproduced_energy",
    r"\s(ship|army|colony|station)_maintenance",
    r"\s(construction|trade|federation)_expenses"
}
# 3.0.*
targets3 = {
    r"surveyed\s*=\s*\{(\s*)set_surveyed": r"set_surveyed = {\1surveyed",
    r"has_completed_special_project\s+": "has_completed_special_project_in_log ",
    r"has_failed_special_project\s+": "has_failed_special_project_in_log ",
    r"species\s*=\s*last_created(\s)": r"species = last_created_species\1",
    r"owner\s*=\s*last_created(\s)": r"owner = last_created_country\1",
    r"(any|every|random)_pop\s*=": r"\1_owned_pop =",
    r"(\s)(any|every|random)_planet\s*=": r"\1\2_galaxy_planet =",
    r"(\s)(any|every|random)_ship\s*=": r"\1\2_galaxy_fleet =",
    r"(any|every|random|count)_sector\s*=": r"\1_galaxy_sector =",
    r"(any|every|random)_war_defender\s*=": r"\1_defender =",
    r"(any|every|random)_war_attacker\s*=": r"\1_attacker =",
    r"(any|every|random|count)_recruited_leader\s*=": r"\1_owned_leader =",
    r"count_planets\s*": "count_galaxy_planet ",
    r"count_ships\s*": "count_galaxy_fleet ",
    r"count(_owned)?_pops\s*": "count_owned_pop ",
    r"count_owned_ships\s*": "count_owned_ship ",
    # "any_ship_in_system": "any_fleet_in_system", # works only sure for single size fleets
    r"spawn_megastructure\s*=\s*\{([^{}]+)location\s*=": r"spawn_megastructure = {\1planet =",
    r"\s+planet =\s*(solar_system|planet)\s*\n?": "", # REMOVE
    r"any_system_within_border\s*=\s*\{[\s\n]*any_system_planet\s*=": "any_planet_within_border =",
    r"is_country_type\s*=\s*default\s+has_monthly_income = \{ resource = (\w+) value <=? \d": r"no_resource_for_component = { RESOURCE = \1",
    r"([^\._])(?:space_)?owner\s*=\s*\{\s*is_(?:same_empire|country|same_value)\s*=\s*(\w+)\s*\}": r"\1is_owned_by = \2",
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


def parse_dir():
    global mod_path, mod_outpath
    files = []
    mod_path = os.path.normpath(mod_path)
    mod_path = iBox("Please select a mod folder:", mod_path)
    # mod_path = input('Enter target directory: ')
    mod_outpath = iBox('Enter out directory (optional):', mod_path)
    # mod_outpath = input('Enter out directory (optional):')
    mod_outpath = os.path.normpath(mod_outpath)

    if not os.path.isdir(mod_path):
        # except OSError:
        #     print('Unable to locate the mod path %s' % mod_path)
        mBox('Error', 'Unable to locate the mod path %s' % mod_path)
    if not os.path.isdir(mod_outpath) or mod_outpath == mod_path:
        mod_outpath = mod_path
        print('Warning: Mod files will be overwritten!')
    else:
        mod_outpath = os.path.normpath(mod_outpath)

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
        # print(_file)
        if os.path.isfile(_file) and re.search(r"\.txt$", _file):
            subfolder = os.path.relpath(_file, mod_path)
            file_contents = ""
            with open(_file, 'r', encoding='utf-8') as txtfile:
                # try:
                # print(_file, type(_file))
                file_contents = txtfile.readlines()
                subfolder, basename = os.path.split(subfolder)
                # basename = os.path.basename(_file)
                txtfile.close()
                out = ""
                changed = False
                for i, line in enumerate(file_contents):
                    # for line in file_contents:
                    # print(line)
                    for rt in removedTargets:
                        rt = re.search(rt, line)
                        if rt:
                            print("WARNING outdated removed trigger: %s in line %i file %s" % (
                                rt.group(0), i, basename))
                    for pattern, repl in targets3.items():
                        if re.search(pattern, line):
                            # , count=0, flags=0
                            line = re.sub(pattern, repl, line)
                            # line = line.replace(t, r)
                            print("Updated file: %s at line %i with %s" %
                                  (basename, i, line.strip()))
                            changed = True
                    out += line

                if changed:
                    structure = os.path.join(mod_outpath, subfolder)
                    out_file = os.path.join(structure, basename)
                    print('Folder: %s File: %s' % (structure, out_file))
                    if not os.path.exists(structure):
                        os.makedirs(structure)
                        # print('Create folder:', subfolder)
                    with open(out_file, "w", encoding='utf-8') as txtfile:
                        txtfile.write(out)
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