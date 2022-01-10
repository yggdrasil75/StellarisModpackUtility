###     Made by ShadowTrolll
# @revision 2021/10/17 + tier number + tech multiline (by FirePrince)

#===============  Options  ================
# switch subbing tech key with localisation on
techKeysOnly = True # True
# if not techKeysOnly=True display both
techKeys = True # True

#============== Import libs ===============
import json
import os
import re
try:
    from winreg import *
except:
    print("Not running windows")

#============== Initialise global variables ===============
modsDir = ""
stellarisDir = ""
selectedEncoding = 'UTF-8'
forbiddenFileChars = ['<','>',':','"','/','\\','|','?','*']


#============== Load config ===============
scriptConfig = {}
with open("config.json", 'r') as file:
    scriptConfig = json.loads(file.read().replace('\\','/'))

print("Welcome to Stellaris modded tech tree exporter by ShadowTrolll#0811!")

#============== Set paths ===============
if (os.name == 'nt'):
    try:
        keyPath = r'SOFTWARE\WOW6432Node\Valve\Steam'
        key = OpenKey(HKEY_LOCAL_MACHINE, keyPath)
        steamDir = QueryValueEx(key, "InstallPath")[0]
        CloseKey(key)
        modsDir = steamDir + r'\steamapps\workshop\content\281990'
        stellarisDir = steamDir + r'\steamapps\common\Stellaris'
    except:
        modsDir = "ERROR_NOT_FOUND"
        stellarisDir = "ERROR_NOT_FOUND"
else:
    modsDir = os.path.expanduser("~/.steam/steam/steamapps/workshop/content/281990")
    stellarisDir = os.path.expanduser("~/.steam/steam/steamapps/common/Stellaris")

if not scriptConfig["stellarisPath"] == "default":
    stellarisDir = scriptConfig["stellarisPath"]

if not scriptConfig["modsPath"] == "default":
    modsDir = scriptConfig["modsPath"]

#============== Make sure paths exist, DOESNT CHECK CONTENT! ===============
while not os.path.isdir(modsDir):
    print ("\nFolder does not exist: " + modsDir)
    modsDir = input("Mods directory could not be found, please enter the FULL path to your Stellaris workshop directory (the folder that contains a lot of numbers): ").strip()

while not os.path.isdir(os.path.join(stellarisDir, 'localisation', 'english')):
    print ("\nFolder does not contain necessary files: " + stellarisDir)
    stellarisDir = input("Stellaris install directory could not be found, please enter the FULL path to it (the folder with stellaris.exe)").strip()

#============== 'Fix' mod specific string quirks ===============
modFixes = [
    "\u00a3",
    "\u00a7H",
    "\u00a7"
    ]
def fixTechNames(name, techNames):
    tmp_splitParts = name.split('$')
    name = name.replace('$','')
    for fix in modFixes:
        name = name.replace(fix, '')
    for tmp_part in tmp_splitParts:
        if tmp_part in techNames:
            name = name.replace(tmp_part, techNames[tmp_part])
    return name

#============== Main handling functions ===============
def loadTechNames(filePath):
    with open(filePath, 'r', encoding = selectedEncoding, errors = 'replace') as file:
        nameDict = {}
        for line in file:
            line = line.lstrip()
            if not line.startswith('#'):
                lineParts = line.split(":")
                if len(lineParts) == 1:
                    continue
                linePart0 = lineParts.pop(0)
                if linePart0.startswith(" "):
                    linePart0 = linePart0[1:]
                linePart0 = linePart0.strip().replace("\"", "")

                linePartsRest = ""
                linePartsCount = 0
                for linePart in lineParts:
                    if linePart.startswith("0"):
                        linePart = linePart[1:]
                    if linePart.startswith(" "):
                        linePart = linePart[1:]
                    linePart = linePart.rstrip().replace("\"", "")
                    if linePartsCount > 0:
                        linePartsRest += ": "
                    linePartsRest += linePart
                    linePartsCount+= 1

                nameDict[linePart0] = linePartsRest
        return nameDict

# techNames = type dict
def handleTechFile(filePath, techNames):
    techArray = { "---": [] }
    with open(filePath, 'r', encoding = selectedEncoding, errors = 'replace') as file:
        lastTech = "---"
        tier = False
        splitLine = []
        for line in file:
            #line = line.lstrip() # can't as we scan with indention
            ### add tier nr
            # if line.startswith('tier'):
            if re.search(r"^\s*tier", line):
                tier = re.search(r'\btier\s*=\s*"?(\d+)\"?', line)
                if tier and lastTech in techArray:
                    tier = tier.group(1)
                    try:
                        techArray[lastTech].insert(1, int(tier)) # len([[tech_name]) > 0
                    except:
                        print(lastTech + " has no translation")

            if re.search(r"^\s*prerequisites", line) or len(splitLine) > 0:
            # if line.startswith('prerequisites') or len(splitLine) > 0:
                splitLine = line.split()
                if len(splitLine) == 0 or splitLine[0] == "}":
                    splitLine = []
                    continue
                # print(splitLine)
                if "prerequisites" in splitLine[0]:
                    splitLine.pop(0)
                for tech_key in splitLine:
                    if "#" == tech_key:
                        splitLine = ["#"]
                        continue
                    elif "#" in tech_key:
                        tech_key = tech_key.split('#')[0]
                        splitLine = ["#"]
                    if len(tech_key) > 4:
                        tech_key = tech_key.replace("\"", "")
                        # tech_key = re.sub(r"[\" ]*", "", tech_key, re.A)
                        # print("\tafter", tech_key)
                        if tech_key in techNames:
                            if not techKeysOnly:
                                tech_name = techNames[tech_key]
                                while '$' in tech_name:
                                    tech_name = fixTechNames(tech_name, techNames)
                                if techKeys:
                                    tech_name += " (%s)" % tech_key
                            else:
                                tech_name = tech_key
                            techArray[lastTech].append(tech_key)
                if len(splitLine) > 0 and splitLine[-1] == "}":
                    splitLine = []
                continue
            reprLine = repr(line)
            if not any(s in reprLine for s in (r'\t', '@')) and len(reprLine) > 5 and not line.startswith(" ") and not line.startswith('#'):
                tech_key = (line.split("="))[0].strip().replace('"','')
                if tech_key in techNames:
                    tech_name = techNames[tech_key]
                    while '$' in tech_name:
                        tech_name = fixTechNames(tech_name, techNames)

                    techArray[tech_key] = [tech_name]
                    lastTech = tech_key

    return techArray

#============== Seek mods with technology ===============
techMods = []
print ("Working in directory: " + modsDir)
for item in os.listdir(modsDir):
    modPath = os.path.join(modsDir, item)
    if os.path.isdir(modPath):
        if os.path.isdir(os.path.join(modPath, 'common', 'technology')):
            techMods.append(item)

print ("\nIndentified mods with technologies:")
print (techMods)

#============== Load localization files ===============
englishTechNames = {}
for root, dirs, files in os.walk(os.path.join(stellarisDir, 'localisation', 'english')):
    for name in files:
        if "english" in name:
            print ("\tLoading localization from file: " + os.path.join(root, name))
            englishTechNames.update(loadTechNames(os.path.join(root, name)))

for mod in techMods:
    for root, dirs, files in os.walk(os.path.join(modsDir, mod, 'localisation')):
            for name in files:
                if "english" in name:
                    print ("\tLoading localization from file: " + os.path.join(root, name))
                    englishTechNames.update(loadTechNames(os.path.join(root, name)))

#============== Main script ===============
jsonOut = {}

if scriptConfig["loadVanillaTech"].lower() == "true":
    print ("Handling vanilla techs")
    jsonOut["Vanilla"] = {}
    for techFile in os.listdir(os.path.join(stellarisDir, 'common', 'technology')):
        if os.path.isfile(os.path.join(stellarisDir, 'common', 'technology', techFile)):
            print ("\tHandling file: " + techFile)
            jsonOut["Vanilla"][techFile] = handleTechFile(os.path.join(stellarisDir, 'common', 'technology', techFile), englishTechNames)

for mod in techMods:
    modName = ""
    try:
        with open(os.path.join(modsDir, mod, r'descriptor.mod'), 'r', encoding = selectedEncoding, errors = 'replace') as file:
            for line in file:
                if "name" in line:
                    modName = line.strip()[6:-1].replace("\"", "") + " [" + mod + "]"
    except:
        modName = "NO MOD NAME FOUND" + " [" + mod + "]"

    print (("\nHandling mod: " + modName).encode(errors='replace'))
    techFiles = []
    jsonOut[modName] = {}
    modTechPath = os.path.join(modsDir, mod, 'common', 'technology')
    for techFile in os.listdir(modTechPath):
        if os.path.isfile(os.path.join(modTechPath, techFile)):
            print ("\tHandling file: " + techFile)
            jsonOut[modName][techFile] = handleTechFile(os.path.join(modTechPath, techFile), englishTechNames)

#============== Write output to file and handle script end ===============
print ("\nWriting tech data to Tech Relations.json")
jsonFile = open("Tech Relations.json", "w", encoding = selectedEncoding, errors = 'replace')
jsonString = json.dumps(jsonOut, indent = 4)
jsonFile.write(jsonString)
jsonFile.close()
print ("Done! The file can be found under " + os.getcwd())

# if os.path.isfile(os.path.join(os.getcwd(), "2_Export_relations_into_Trees.py")):
#     input("Press enter to continue to the second script or close this window to exit...\nPS: If you want to support me, you can do as at  https://www.buymeacoffee.com/ShadowTrolll")
#     exec(open("2_Export_relations_into_Trees.py").read())
# else:
#     input("Complementary script missing (has to be in the same folder as this one and the output), press enter to exit...\nPS: If you want to support me, you can do as at  https://www.buymeacoffee.com/ShadowTrolll")

hasVanillaTech = False
vanillaContent = {}
vanillaTechs = []
vanillaTechsWithPrereq = {}
exportStringGL = ""
modTechs = []
modTechsWithPrereq = {}
forbiddenFileChars = ['<','>',':','"','/','\\','|','?','*']

class stellarisTech:
    def __init__(self, techName, prereq):
        self.techName = str(techName) # str
        self.prereq = prereq # array

    def exportPrereq(self, level = 0):
        global exportStringGL
        levelIndent = ""
        for x in range(level):
            levelIndent += "\t"
        exportStringGL += (levelIndent + self.techName + "\n")

        for techPrereq in self.prereq:
            if techPrereq in modTechsWithPrereq:
                for tempTech in modTechs:
                    if tempTech.techName == techPrereq:
                        if tempTech.techName == self.techName:
                            continue
                        tempTech.exportPrereq(level + 1)
                        break
            elif techPrereq in vanillaTechsWithPrereq and hasVanillaTech:
                for tempTech in vanillaTechs:
                    if tempTech.techName == techPrereq:
                        if tempTech.techName == self.techName:
                            continue
                        tempTech.exportPrereq(level + 1)
                        break
            else:
                exportStringGL += (levelIndent + "\t|--" + str(techPrereq) + "\n")


def export_relations_into_trees(jsonContent):
    global exportStringGL
    global hasVanillaTech
    if not jsonContent:
        jsonContent = {}
        with open('Tech Relations.json', 'r', encoding = 'UTF-8') as file:
            jsonContent = json.loads(file.read())
    print(type(jsonContent))

    if "Vanilla" in jsonContent:
        hasVanillaTech = True
        print("Has Vanilla Tech")
        vanillaContent = jsonContent.pop("Vanilla")

    if not os.path.isdir('Tech Trees by mod'):
        os.mkdir('Tech Trees by mod')

    if hasVanillaTech:
        print ("\nProcessing vanilla techs ")
        for file in vanillaContent:
            print("\tProcessing file: " + file)
            for technology in vanillaContent[file]:
                print("\t\tProcessing technology: " + technology)
                if len(vanillaContent[file][technology]) > 0:
                    print("\t\t\tTechnology has prerequirements.")
                    vanillaTechsWithPrereq[technology] = vanillaContent[file][technology]
                vanillaTechs.append(stellarisTech(technology, vanillaContent[file][technology]))

    for mod in jsonContent:
        print (("\nProcessing mod: " + mod).encode(errors='replace'))
        modTechs = []
        for file in jsonContent[mod]:
            print("\tProcessing file: " + file)
            for tech_key in jsonContent[mod][file]:
                techArr = jsonContent[mod][file][tech_key]
                print("\t\tProcessing technology: " + tech_key)
                if len(techArr) > 1:
                    tech_name = techArr.pop(0)
                    tier = techArr.pop(0)
                    if type(tier) == int:
                        tech_name += " (%i)" % (tier) # " (" + str(tier) + ")"
                    if techKeysOnly:
                        tech_name = tech_key
                    elif techKeys and type(tech_name) == str:
                        tech_name += " (%s)" % tech_key

                    if len(techArr) > 0:
                        print("\t\t\tTechnology %s has prerequirements:" % (tech_name))
                        modTechsWithPrereq[tech_name] = techArr
                    modTechs.append(stellarisTech(tech_name, techArr))

        exportStringGL = ""
        for tech in modTechs:
            tech.exportPrereq()
            exportStringGL += "\n"
        validModName = mod.replace(":", " - ")
        for char in forbiddenFileChars:
            validModName = validModName.replace(char, '')
        with open(os.path.join('Tech Trees by mod', (validModName + "_TREE_EXPORT.txt")), 'w', encoding = 'UTF-8') as file:
            file.write(exportStringGL)

    print('Done! Tech Trees can be found in the folder "Tech Trees by mod" under ' + os.getcwd())
    input('Press enter to exit...\nPS: If you want to support me, you can do as at  https://www.buymeacoffee.com/ShadowTrolll')

export_relations_into_trees(jsonOut)
