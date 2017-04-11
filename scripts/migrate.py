mfdir = '../../extensions/MobileFrontend'

import json, shutil, os, subprocess, time
from collections import OrderedDict

messages = [ 'mobile-frontend-placeholder', 'skinname-minerva',
  'mobile-frontend-talk-back-to-userpage',
  'mobile-frontend-talk-back-to-projectpage',
  'mobile-frontend-talk-back-to-filepage',
  'mobile-frontend-talk-back-to-page',
  'mobile-frontend-editor-edit',
  'mobile-frontend-user-newmessages',
  'mobile-frontend-main-menu-contributions',
  'mobile-frontend-main-menu-watchlist',
  'mobile-frontend-main-menu-settings',
  'mobile-frontend-home-button',
  'mobile-frontend-random-button',
  'mobile-frontend-main-menu-nearby',
  'mobile-frontend-main-menu-logout',
  'mobile-frontend-main-menu-login',
  'mobile-frontend-history',
  'mobile-frontend-user-page-member-since',
  'mobile-frontend-main-menu-button-tooltip',
  'mobile-frontend-language-article-heading',
  'mobile-frontend-pageaction-edit-tooltip',
  'mobile-frontend-language-article-heading',
  'mobile-frontend-user-page-talk',
  'mobile-frontend-user-page-contributions',
  'mobile-frontend-user-page-uploads'
]

def reset():
    # Do cleanup in preparation for patchsets it will make.
    subprocess.call(["git clean -fd"], shell=True)
    subprocess.call(["git stash && git clean -fd"], shell=True, cwd=mfdir)
    subprocess.call(["rm -rf includes && rm -rf resources && rm -rf minerva.less && rm -rf i18n && rm -rf resources-minerva"], shell=True)
    subprocess.call(["mkdir includes && mkdir includes/skins && mkdir includes/models && mkdir resources && mkdir minerva.less && mkdir i18n && mkdir resources-minerva"], shell=True)
    time.sleep(1)

def saveJSON(path, data, sort_keys = False):
    with open(path, 'w') as outfile:
        json.dump(data, outfile, indent = "\t", ensure_ascii=False, separators=(',', ': '), sort_keys=sort_keys)

def clean( keys_to_remove, data_key ):
    # Remove the keys we added from MobileFrontend extension.json
    for key in keys_to_remove:
        try:
            del mfExtensionData[data_key][key]
        except KeyError:
            pass

def steal_files_in_directory(dir):
    # steal templates etc from MobileFrontend
    for root, dirs, files in os.walk(mfdir + '/' + dir):
        for file in files:
            steal(dir + file)

def steal( path ):
    print('stealing %s'%path)
    try:
        # ../ because we are in scripts folder
        shutil.move( mfdir + '/' + path, path )
    except ( FileNotFoundError, shutil.Error ) as e:
        print (e)
        # probably done in initial steal steps
        pass

def copy( path ):
    print('copying %s'%path)
    try:
        # ../ because we are in scripts folder
        shutil.copy( mfdir + '/' + path, path )
    except ( FileNotFoundError, shutil.Error ) as e:
        print (e)
        # probably done in initial steal steps
        pass

def isOwnedByMinerva(key, value):
    return key.startswith("Minerva") or key.startswith( 'skins.minerva' ) or \
        ( type(value) == type('string') and "skins/" in value )

def migrateObject(fromObj, toObj, key):
    obj = fromObj[key]
    keys_to_remove = []
    files_to_steal = []
    for subkey in obj:
        val = obj[subkey]
        if isOwnedByMinerva(subkey, val):
            if key == "ResourceModules":
                steal( 'resources/%s'% subkey )
            elif key == 'AutoloadClasses':
                steal( val )

            toObj[key][subkey] = val
            keys_to_remove.append(subkey)

    # cleanup
    print('remove %s'%keys_to_remove)
    clean( keys_to_remove, key )


reset()
f = open(mfdir +'/extension.json', 'r')
mfExtensionData = json.load(f, object_pairs_hook=OrderedDict)
f.close()
f = open('skin.json', 'r')
minervaSkinData = json.load(f, object_pairs_hook=OrderedDict)
f.close()

migrateObject( mfExtensionData, minervaSkinData, "AutoloadClasses")
migrateObject( mfExtensionData, minervaSkinData, "ResourceModules")
migrateObject( mfExtensionData, minervaSkinData, "config")

for moduleName, stylesheets in mfExtensionData['ResourceModuleSkinStyles']['minerva'].items():
    if stylesheets[0].startswith("resources-minerva/"):
        del mfExtensionData['ResourceModuleSkinStyles']['minerva'][moduleName]
        minervaSkinData['ResourceModuleSkinStyles']['minerva'][moduleName] = stylesheets
        steal('resources-minerva/' + moduleName + '/')

for hookname in mfExtensionData['Hooks']:
    mfHooks = mfExtensionData['Hooks'][hookname]
    minervaHooks = []
    newMfHooks = []
    for hook in mfHooks:
        if isOwnedByMinerva(hook, hook):
            minervaHooks.extend([hook])
        else:
            newMfHooks.extend([hook])
    if len(minervaHooks) > 0:
        minervaSkinData['Hooks'][hookname] = minervaHooks
    mfExtensionData['Hooks'][hookname] = newMfHooks

steal_files_in_directory('includes/skins/')
steal_files_in_directory('minerva.less/')
# steal the service wirings
steal('includes/Minerva.ServiceWiring.php');

# remove
del mfExtensionData["ValidSkinNames"]

# todo: setup config wirings.
# add onRegistration hook
minervaSkinData['callback'] = 'MinervaHooks::onRegistration';

with open('skin.json', 'w') as outfile:
    #prettify output
    json.dump(minervaSkinData, outfile, sort_keys = True, indent = 2, ensure_ascii=False, separators=(',', ': '))

with open(mfdir + '/extension.json', 'w') as outfile:
    #prettify output
    json.dump(mfExtensionData, outfile, indent = "\t", ensure_ascii=False, separators=(',', ': '))

# migrate i18n
print('migrating i18n')
for root, dirs, files in os.walk(mfdir + '/i18n/'):
    for language in files:
        newLanguageData = {}
        f = open(mfdir + '/i18n/' + language, 'r')
        languageData = json.load(f, object_pairs_hook=OrderedDict)
        f.close()
        messages.sort()
        for msgKey in messages:
            try:
                newLanguageData[msgKey] = languageData[msgKey]
                del languageData[msgKey]
            except KeyError:
                pass

        # save to mf
        saveJSON( mfdir + '/i18n/' + language, languageData )
        
        # mobile specific renames
        try:
            newLanguageData['skinname-minerva-neue'] = newLanguageData['skinname-minerva']
            del newLanguageData['skinname-minerva']
        except KeyError:
            pass

        # save to minerva
        saveJSON( 'i18n/' + language, newLanguageData, True )

'''
TODO: breaking the MobileFrontend dependency
minervaSkinData['AutoloadClasses']['MobileUI'] = 'includes/MobileUI.php';
minervaSkinData['AutoloadClasses']['MobilePage'] = 'includes/models/MobilePage.php';
copy('includes/MobileUI.php');
copy('includes/models/MobilePage.php')
'''