#   Copyright (C) 2015 Kevin S. Graer
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import subprocess, os, sys, re, random, threading
import datetime, time, shutil

from urllib import unquote
from xml.dom.minidom import parse, parseString
from resources.lib.utils import *
from resources.lib.Globals import *

try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo-web/submit.php'
except:
    pass
    
class SkinManager(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        if getProperty("PseudoTVSkinRunning") != "True":
            setProperty("PseudoTVSkinRunning", "True")
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
            self.doModal()
        
    
    def onInit(self):
        self.CurrentSkin = Skin_Select
        self.SkinPanel = self.getControl(500)
        self.fillSkins()
        
        
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('SkinManager: ' + msg, level)

        
    def skinMeta(self, skinname):
        skinBasePath = xbmc.translatePath(os.path.join(PTVL_SKIN_LOC,skinname))
        skinBaseURL = 'https://raw.githubusercontent.com/PseudoTV/PseudoTV_Skins/master/'+skinname
        cleanSkin = skinname
        
        #Skin local (already downloaded)
        if xbmcvfs.exists(os.path.join(skinBasePath,'skin.xml')):
            SkinLocal = 'true' 
            skinBase = skinBasePath
            LocalLogo = 'local.png'
        else:
            SkinLocal = 'false'
            LocalLogo = 'NA.png'
            skinBase = skinBaseURL

        try:
            #Fill Skin meta
            if SkinLocal == 'false':
                xml = open_url(os.path.join(skinBaseURL + '/skin.xml'))
            else:
                xml = open(os.path.join(skinBasePath,'skin.xml'), "r")
                
            dom = parse(xml)
            name = dom.getElementsByTagName('name')
            version = dom.getElementsByTagName('version')
            skinname = dom.getElementsByTagName('skinname') 
            resolutions = dom.getElementsByTagName('defaultresolution') 
            
            version = (version[0].childNodes[0].nodeValue).rstrip()     
            sknname = (skinname[0].childNodes[0].nodeValue).rstrip()  
            resolution = (resolutions[0].childNodes[0].nodeValue).rstrip()
            xml.close()         
        except:
            return
                
        #Skin currently inuse
        CurSkin = 'false'
        if self.CurrentSkin.lower() == sknname.lower():
            CurSkin = 'true'
            sknname = ' [ ' + sknname + ' ]'
        
        #Check PTVL.GUI version
        SkinOld = 'false'
        OutLogo = 'NA.png'
        if version != PTVL_SKINVER:
            SkinOld = 'true'
            OutLogo = os.path.join(IMAGES_LOC,'outdated.png')      
            # sknname += ' OUTDATED, please contact skin developer'
            
        self.SkinItems = xbmcgui.ListItem(label=sknname) 
        self.SkinItems.setProperty('PTVL.isSKINLOCAL',SkinLocal)                 
        self.SkinItems.setProperty('PTVL.SKINLOCAL',LocalLogo)                     
        self.SkinItems.setProperty('PTVL.isSKINSEL',CurSkin)              
        self.SkinItems.setProperty('PTVL.isSKINOUTDATED',SkinOld)       
        self.SkinItems.setProperty('PTVL.SKINOUTDATED',OutLogo)
        self.SkinItems.setProperty('PTVL.SKINNAME',sknname)
        self.SkinItems.setProperty('PTVL.SKIN',cleanSkin)
        self.SkinItems.setProperty('PTVL.SKINRESOLUTION',str(resolution))
        self.SkinItems.setProperty('PTVL.SKINLOGO',skinBase + '/logo.png')
        self.SkinItems.setProperty('PTVL.SKINVERSION','v.'+version)
        self.SkinItems.setProperty('PTVL.SKINAUTHOR','Designed by: ' + name[0].childNodes[0].nodeValue)
        self.SkinItems.setProperty('PTVL.SKINSHOT1',skinBase + '/screenshot01.png')  
        self.SkinItems.setProperty('PTVL.SKINSHOT2',skinBase + '/screenshot02.png')  
        self.SkinItems.setProperty('PTVL.SKINSHOT3',skinBase + '/screenshot03.png')  
        self.SkinItems.setProperty('PTVL.SKINSHOT4',skinBase + '/screenshot04.png')
        self.SkinItems.setProperty("PTVL.SKINPATH", str(skinBasePath)) 
        self.SkinItems.setProperty("PTVL.SKINURL", str(skinBaseURL))   
        self.SkinItems.setProperty("PTVL.SKINZIP", str(skinBaseURL + '/' + sknname +'.zip'))       
        self.SkinPanel.addItem(self.SkinItems)
        return
        
        
    def fillSkins(self):
        self.log("fillSkins")
        show_busy_dialog()
        self.skinMeta('Default')
        github_skinList = fillGithubItems('https://github.com/PseudoTV/PseudoTV_Skins')
        for i in range(len(github_skinList)):
            ssList = fillGithubItems('https://github.com/PseudoTV/PseudoTV_Skins/tree/master/%s' % github_skinList[i])
            for n in range(len(ssList)):
                if ((ssList[n].lower()).startswith('screenshot') and github_skinList[i] != '_Outdated'):
                    self.skinMeta(github_skinList[i])
                    break
        hide_busy_dialog()
        self.setFocusId(500)

        
    def closeManager(self):
        self.log("closeManager") 
        setProperty("PseudoTVSkinRunning", "False")
        self.close()
                   
 
    def onAction(self, act):
        action = act.getId()
        if action in ACTION_SELECT_ITEM:
            self.SelectAction(self.SkinPanel.getSelectedItem().getProperty('PTVL.SKIN'))
        elif action in ACTION_MOVE_LEFT:   
            self.log("onAction, ACTION_MOVE_LEFT")
            setProperty('PTVL.SSLEFTD','FF0297eb')
            setProperty('PTVL.SSRIGHTD','FFFFFFFF') 
        elif action in ACTION_MOVE_RIGHT:
            self.log("onAction, ACTION_MOVE_RIGHT")
            setProperty('PTVL.SSRIGHTD','FF0297eb')
        elif action in ACTION_PREVIOUS_MENU:
            self.closeManager()
        elif act.getButtonCode() == 61575 or action == ACTION_DELETE_ITEM:
            self.deleteSkin(self.SkinPanel.getSelectedItem().getProperty('PTVL.SKIN'))
                 

    def deleteSkin(self, selSkin):
        if selSkin == 'Default' or xbmcvfs.exists(self.SkinPanel.getSelectedItem().getProperty('PTVL.SKINPATH')) == 'false':
            return
        try:
            if yesnoDialog('%s "%s" Skin' %('Delete', selSkin)) == True:
                shutil.rmtree(self.SkinPanel.getSelectedItem().getProperty('PTVL.SKINPATH'))
        except:
            pass
        REAL_SETTINGS.setSetting("SkinSelector",'Default')
        self.closeManager()
    
    
    def downloadSkin(self, selSkin):
        self.log("downloadSkin")
        url = self.SkinPanel.getSelectedItem().getProperty('PTVL.SKINZIP')
        dl = os.path.join(PTVL_SKIN_LOC,'%s.zip'%selSkin)
        try:
            print url, dl
            download(url, dl, '')
            all(dl, os.path.join(PTVL_SKIN_LOC,''),True)
            try:
                xbmcvfs.delete(dl)
            except:
                pass
            return True
        except:
            return False
            
      
    def SelectAction(self, selSkin):
        self.log("SelectAction")
        if selSkin.lower() != self.CurrentSkin.lower():
            if self.SkinPanel.getSelectedItem().getProperty('PTVL.isSKINOUTDATED') == 'true':
                infoDialog('Skin version outdated!') 
                return
                
            if self.SkinPanel.getSelectedItem().getProperty('PTVL.isSKINLOCAL') == 'true':
                msg = 'Apply'
            else:
                msg = 'Download & Apply'
                
            if yesnoDialog('%s "%s" Skin' %(msg, selSkin)) == True:
                if self.SkinPanel.getSelectedItem().getProperty('PTVL.isSKINLOCAL') == 'false':
                    if self.downloadSkin(selSkin) == False:
                        return
                REAL_SETTINGS.setSetting("SkinSelector",selSkin)
                self.closeManager()
        
        
# SkinSelector setsetting to skin name
__cwd__ = REAL_SETTINGS.getAddonInfo('path')
mydialog = SkinManager("script.pseudotv.live.SkinManager.xml", __cwd__, "Default")
del mydialog