#!/usr/bin/env python
# -*- coding: utf-8 -*-
###    @author FirePrince
###    @revision 2021/10/20
###    USAGE: You need install https://pyyaml.org/wiki/PyYAMLDocumentation for Python3.x
###    ATTENTION: You must customize the vars localModPath and local_OVERHAUL
###    TODO: Renaming (already translated) keys is not working

#============== Import libs ===============
import os
import io
import tkinter as tk
from tkinter import messagebox
# import traceback
# import sys
# import json
# from ruamel.yaml import YAML
# from ruamel.yaml.compat import StringIO
import re
import glob
import yaml
# yaml=YAML(typ='safe')
# import chardet # test 'utf-8-sig'
# import codecs
import errno, winreg
try: from winreg import *
except: print("Not running windows")

#============== Initialise global variables ===============
# Write here your mod folder name and languages to replace/update
localModPath = ["distant_stars_overhaul", ["german", "russian", "spanish", "braz_por", "french", "polish", "simp_chinese"]]

loadVanillaLoc = True # replaces exact matching strings with vanilla ones
# loadDependingMods = False # replaces exact matching strings with ones from the depending mod(s)

ymlfiles = '*.yml' # you can also use single names
# ymlfiles = 'CrisisManagerMenu_l_english.yml'

key_IGNORE = "" # stops copying over localisations keys with this starting pattern eg. "dmm_mod."

localModPath, local_OVERHAUL = localModPath
print(localModPath, local_OVERHAUL)


def tr(s):
    # print(type(s), len(s))
    if isinstance(s, bytes):
        s = s.decode('utf-8-sig')
    # s = re.sub('\n', '\\n', s)
    s = s.replace(' *\\r?\\n', 'BRR')
    s = re.sub(r' *#[^\n"]*$', '', s, flags=re.M|re.ASCII) # remove comments end
    s = re.sub(r'^ *#[^\n]+$', '', s, flags=re.M|re.ASCII) # remove comments line
    # s = re.sub(r':\d \"\"\s*$', ": ""\n", s, flags=re.M|re.ASCII)
    s = re.sub(r'([^\d][^\n]|[\d][^\s])\"([ .?!,\w]{1,3})\"([^\n])', r'\1’\2’\3', s, flags=re.M|re.ASCII)
    s = re.sub(r'(^ [^\s:#]*?\:)\d* +\"([^\n]*?)\"\s*$', r"\1«\2»", s, flags=re.M|re.ASCII) # not working always, but it should (as other works so it is a bug)
    # s = re.sub(r'^( [\w\._]+):\d+ +\"', r"\1:«", s, flags=re.M|re.ASCII)
    # s = re.sub(r'\"\s*$', r"»", s, flags=re.M|re.ASCII)
    # print(s)
    s = s.replace("'", '’')
    s = re.sub(r'([^:#"])\"+([^\n])', r'\1’\2', s) #   [\]\w« \.§!?,(){}$]{2}
    # s = s.replace(":", '…')
    s = s.replace("«", ' "').replace("»", '"')
    # print(s)
    # s = re.sub(r':\d "+', ': "', s, flags=re.M|re.ASCII)
    return s

def getYAMLstream(lang, filename):
    "Read YAML file"
    if lang != "english":
        filename = filename.replace("english", lang)
    lang = os.path.join(os.getcwd(), filename)
    # print(lang)
    if os.path.isfile(lang):
        return io.open(lang, "rb")  # "rb" , encoding='utf-8-sig'


if loadVanillaLoc:
    ### Read Stellaris path from registry
    loadVanillaLoc = ""
    if os.name == 'nt':
        aReg =  winreg.HKEY_CURRENT_USER
        proc_arch = os.environ['PROCESSOR_ARCHITECTURE'].lower()
        proc_arch64 = os.environ['PROCESSOR_ARCHITEW6432'].lower()
        aKey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        aReg =  winreg.HKEY_LOCAL_MACHINE
        print(r"*** Reading Stellaris path from %s ***" % (aKey))
        if proc_arch == 'x86' and not proc_arch64: arch_keys = {0}
        elif proc_arch == 'x86' or proc_arch == 'amd64': arch_keys = {winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY}
        else: raise Exception("Unhandled arch: %s" % proc_arch)
        for arch_key in arch_keys:
            key = winreg.OpenKey(aReg, aKey, 0, winreg.KEY_READ | arch_key)
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                skey_name = winreg.EnumKey(key, i)
                skey = winreg.OpenKey(key, skey_name)
                if len(loadVanillaLoc) > 0 and os.path.isdir(loadVanillaLoc): break
                else:
                    try:
                        if winreg.QueryValueEx(skey, 'DisplayName')[0].startswith("Stellaris") and len(winreg.QueryValueEx(skey, 'InstallLocation')[0]) > 0:
                            loadVanillaLoc = winreg.QueryValueEx(skey, 'InstallLocation')[0]
                            if len(loadVanillaLoc) > 0:
                                loadVanillaLoc = os.path.normpath(loadVanillaLoc)
                                if os.path.isdir(loadVanillaLoc):
                                    # print("REG", loadVanillaLoc, winreg.QueryValueEx(skey, 'DisplayName')[0])
                                    break
                                else: loadVanillaLoc = ""
                    except OSError as e:
                        if e.errno == errno.ENOENT: # DisplayName doesn't exist in this skey
                            pass
                    finally:
                        skey.Close()
    else:
        loadVanillaLoc = os.path.expanduser("~/.steam/steam/steamapps/common/Stellaris")

    if len(loadVanillaLoc) > 0 and os.path.isdir(loadVanillaLoc):
        loadVanillaLoc = os.path.join(loadVanillaLoc, "localisation")
    else:
        raise Exception('ERROR: Unable to locate the Stellaris path.')

    os.chdir(loadVanillaLoc)
    print(loadVanillaLoc)
    vanillafiles = glob.iglob(os.path.join('english', ymlfiles), recursive=False)
    # vanillafiles = ["english\\l_english.yml"] # TEST
    loadVanillaLoc = {}

    for filename in vanillafiles:
        print(filename)
        streamEn = getYAMLstream("english", filename)
        streamEn = streamEn.read()
        # FIX VANILLA
        if filename == "english\\l_english.yml":
            if isinstance(streamEn, bytes):
                streamEn = streamEn.decode('utf-8-sig')
            streamEn = streamEn.replace('android_occupation_army_desc:0 ""', 'android_occupation_army_desc: "')

        streamEn = yaml.safe_load(tr(streamEn))
        streamEn = streamEn["l_english"]
        if isinstance(streamEn, dict):
            loadVanillaLoc.update(streamEn)
        else:
            print("XAML TYPE ERROR", type(streamEn),streamEn)
            # loadVanillaLoc.extend(streamEn)

# ymlfiles = '*.yml'

# def abort(message):
#   mBox('abort', message, 0)
#   sys.exit(1)


def mBox(mtype, text):
    tk.Tk().withdraw()
    style = not mtype and messagebox.showinfo or mtype == 'Abort' and messagebox.showwarning or messagebox.showerror
    style(title=mtype, message=text)


def iBox(title, prefil): # , master
    answer = tk.filedialog.askdirectory(
        initialdir=prefil,
        title=title,
        # parent=master
        )
    return answer


# mods_registry = "mods_registry.json" # old launcher (changed in 2.7.2)
mods_registry = "settings.txt"
localizations = ["english", "german", "russian", "spanish", "braz_por", "french", "polish", "simp_chinese"]

# Check Stellaris settings location
settingsPath = [
    ".", "..",
    os.path.join(os.path.expanduser('~'), 'Documents', 'Paradox Interactive', 'Stellaris'),
    os.path.join(os.path.expanduser('~'), '.local', 'share', 'Paradox Interactive', 'Stellaris')
]

settingsPath = [s for s in settingsPath if os.path.isfile(
    os.path.join(s, mods_registry))]

ymlfiles = glob.iglob(os.path.join('english', ymlfiles), recursive=False)

# for s in settingsPath:
#   if os.path.isfile(os.path.join(s, mods_registry)):
#       settingsPath[0] = s
#       break
print(settingsPath)

if len(settingsPath):
    settingsPath = settingsPath[0]
else:
    # from tkinter import filedialog
    mBox('Error', 'Unable to locate ' + mods_registry)
    settingsPath = iBox(
        "Please select the Stellaris settings folder:", settingsPath[0])

# mods_registry = os.path.join(settingsPath, mods_registry)

localModPath = os.path.join(settingsPath, "mod", localModPath, "localisation")

os.chdir(localModPath)

regRev1 = re.compile(r'^ +\"([^:"\s]+)\": ', re.MULTILINE)
regRev2 = re.compile(r'(?:\'|([^:"]{2}))\'?$', re.MULTILINE)


def trReverse(s):
    "Paradox workaround"
    # print(type(s))
    if isinstance(s, bytes):
        s = s.decode('utf-8-sig')
    s = s.replace('\r\n', '\n')  # Windows
    s = s.replace('  ', ' ')
    s = re.sub(r'BRR *', r'\\n', s)
    s = re.sub(regRev1, r' \g<1>:0 ', s)  # add 0 to keys
    s = re.sub(re.compile(r'^"(l_\S+)":\n'), r'\1:\n', s)
    # s = s.replace("”", "\"")
    s = s.replace("’", "\'")
    # s = s.replace("…", ':')
    # s = re.sub(regRev2, r'\1"', s)
    return s


def writeStream(lang, stream, filename):
    "Write YAML file"
    filename = filename.replace("english", lang)
    if not os.path.isdir(lang):
        try:
            os.mkdir(lang)
        except OSError:
            print("Creation of the directory %s failed" % lang)
        else:
            print("Successfully created the directory %s " % lang)
    lang = os.path.join(os.getcwd(), filename)
    print(lang, os.path.isfile(lang))
    # if not os.path.isfile(lang):
    if isinstance(stream, bytes):
        stream = stream.decode('utf-8-sig')
    with io.open(lang, 'w', encoding='utf-8-sig') as f:
        f.write(stream)
        # yaml.dump(stream, f, indent=1)

# BOM = codecs.BOM_UTF8 # u'feff'
# def testYAML_BOM(text):
#     "Test YAML encoding"
#     # filename = filename.replace("english", lang)
#     # lang = os.path.join(os.getcwd(), filename)
#     # with open(lang, mode='rb') as f:
#         # text = f.read(4)
#     # print(BOM, "BOM", text)
#     # if not text.startswith(BOM):
#     if text != BOM:
#         print("File not in UTF8-BOM:")
#         # changed = True
#         return True

# yaml = ruamel.yaml.YAML(typ='safe')
yaml.default_flow_style = False
yaml.allow_unicode = True
# yaml.indent = 0
# yaml.allow_duplicate_keys = False
# if __name__ == '__main__':
# yaml.warnings({'YAMLLoadWarning': False})

if loadVanillaLoc and isinstance(loadVanillaLoc, dict):
    loadVanillaLoc = loadVanillaLoc.items() # (May switched dict has better performance?)
else: loadVanillaLoc = False

#CrisisManagerEvent_l_english ,'**'
for filename in ymlfiles:
    print(filename)
    streamEn = getYAMLstream(localizations[0], filename)
    streamEn = streamEn.read()
    # print(streamEn)
    dictionary = {}
    # try:
    #   print(type(dictionary),dictionary)
    #   # print(dictionary["ï»¿l_english"])
    # except yaml.YAMLError as exc:
    #   print(exc)
    # doc = yaml.load_all(stream, Loader=yaml.FullLoader)
    # doc = yaml.dump(dictionary) # ["\u00ef\u00bb\u00bfl_english"]
    # doc = json.dumps(dictionary) # ["\u00ef\u00bb\u00bfl_english"]
    # doc = yaml.dump(dictionary)
    # print(type(dictionary), dictionary)
    # doc = tr(dictionary['l_english'])
    # dictionary = yaml.load(tr(streamEn), Loader=yaml.FullLoader)
    dictionary = yaml.safe_load(tr(streamEn))
    # print("New document:", type(dictionary))
    doc = dictionary["l_english"]
    # print(type(doc), isinstance(doc, dict)) True
    print(type(loadVanillaLoc), isinstance(loadVanillaLoc, dict)) # type(loadVanillaLoc) == dict

    # Replace with Vanilla
    if loadVanillaLoc and isinstance(doc, dict):
        # print("LOAD loadVanillaLoc")
        for k, v in doc.items():
            if len(v) > 2:
                for vkey, vvalue in loadVanillaLoc:
                    if len(vvalue) > 2 and v == vvalue and not vvalue.startswith("$"):
                        doc[k] = '$'+ vkey +'$'
                        print(k, "REPLACED with vanilla", vkey)

    # for doc in dictionary:
    for lang in range(1, len(localizations)):
        changed = False
        lang = localizations[lang]
        stream = getYAMLstream(lang, filename)
        if not stream:
            stream = {}
            print("Create new document "+lang)
            stream = streamEn.replace(b'l_english', bytes('l_'+lang, "utf-8"))
            # copy file with new header
            writeStream(lang, stream, filename)
            continue
        else:
            stream = stream.read()
            # print(stream[0],"BOM", filename.replace("english", lang))
            # changed = testYAML_BOM(stream.read(3))
            if stream[0] != 239: # b'ufeff':
                print(filename.replace("english", lang), "not UTF8-BOM", stream[0])
                changed = True

        langStream = tr(stream)
        # print("Str document:", type(langStream), langStream)
        # langStream = yaml.load(langStream, Loader=yaml.FullLoader)
        langStream = yaml.safe_load(langStream)

        if not "l_"+lang in langStream: # not langStream.startswith("l_"+lang):
            print("Key ERROR on file", filename.replace("english", lang), "try to fix", type(langStream))
            # Fix it!?
            langStream["l_"+lang] = langStream.pop(next(iter(langStream))) # old list(langStream.keys())[0]
            # continue

        langDict = langStream["l_"+lang]
        #print("Dict document:", type(langStream), langStream)

        # for _, doc in dictionary.items():
        if isinstance(langDict, dict):
            for key, value in doc.items():
                # print(key, value)
                if key not in langDict or value == "" or langDict[key] in ("", "REPLACE_ME") or (lang in local_OVERHAUL and langDict[key] != value) and not (key_IGNORE != "" and key.startswith(key_IGNORE)):
                    langDict[key] = value
                    changed = True
                    print("Fixed document " +
                          filename.replace("english", lang), key, value)
                    # break
                # else: print(bytes(key + ":0 " + langDict[key], "utf-8").decode("utf-8"))
            for key in list(langDict.keys()):
                if key not in doc:
                    del langDict[key]
                    changed = True
                    print(key, "removed from document " +
                          filename.replace("english", lang))

        if changed:
            # dictionary = doc.copy()
            # dictionary.update(langDict)
            # langStream["l_"+lang] = dictionary
            langStream["l_"+lang] = langDict
            # print(type(langStream), langStream)
            langStream = yaml.dump(langStream, width=10000, allow_unicode=True,
                                   indent=1, default_style='"')  # , encoding='utf-8'
            langStream = trReverse(langStream)
            # print(type(langStream), langStream.encode("utf-8"))
            writeStream(lang, langStream, filename)
