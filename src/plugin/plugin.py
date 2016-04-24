import os

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigBoolean, \
	getConfigListEntry, ConfigSubDict, ConfigInteger, ConfigNothing
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eEnv

import serviceapp_client


SINKS_DEFAULT = ("dvbvideosink", "dvbaudiosink")
SINKS_EXPERIMENTAL = ("dvbvideosinkexp", "dvbaudiosinkexp")

sinkChoices = []
if (os.path.isfile(eEnv.resolve("$libdir/gstreamer-1.0/libgstdvbvideosink.so")) and
			os.path.isfile(eEnv.resolve("$libdir/gstreamer-1.0/libgstdvbaudiosink.so"))):
	sinkChoices.append("original")
if (os.path.isfile(eEnv.resolve("$libdir/gstreamer-1.0/libgstdvbvideosinkexp.so")) and
			os.path.isfile(eEnv.resolve("$libdir/gstreamer-1.0/libgstdvbaudiosinkexp.so"))):
	sinkChoices.append("experimental")

playerChoices = ["gstplayer", "exteplayer3"]

config.plugins.serviceapp = ConfigSubsection()
configServiceApp = config.plugins.serviceapp

configServiceApp.servicemp3 = ConfigSubsection()
configServiceApp.servicemp3.replace = ConfigBoolean(default=False, descriptions={0: "original", 1: "serviceapp"})
configServiceApp.servicemp3.replace.value = serviceapp_client.isServiceMP3Replaced()
configServiceApp.servicemp3.player = ConfigSelection(default="gstplayer", choices=playerChoices)

configServiceApp.gstplayer = ConfigSubDict()
configServiceApp.gstplayer["servicemp3"] = ConfigSubsection()
configServiceApp.gstplayer["servicegstplayer"] = ConfigSubsection()
for key in configServiceApp.gstplayer.keys():
	configServiceApp.gstplayer[key].sink = ConfigSelection(default="original", choices=sinkChoices)
	configServiceApp.gstplayer[key].bufferSize = ConfigInteger(8192, (1024, 1024 * 64))
	configServiceApp.gstplayer[key].bufferDuration = ConfigInteger(0, (0, 100))
	configServiceApp.gstplayer[key].subtitleEnabled = ConfigBoolean(default=True)

configServiceApp.exteplayer3 = ConfigSubDict()
configServiceApp.exteplayer3["servicemp3"] = ConfigSubDict()
configServiceApp.exteplayer3["serviceexteplayer3"] = ConfigSubDict()


def initServiceAppSettings():
	for key in configServiceApp.gstplayer.keys():
		if key == "servicemp3":
			settingId = serviceapp_client.OPTIONS_SERVICEMP3_GSTPLAYER
		elif key == "servicegst":
			settingId = serviceapp_client.OPTIONS_SERVICEGSTPLAYER
		else:
			continue
		playerCfg = configServiceApp.gstplayer[key]
		if playerCfg.sink.value == "original":
			videoSink, audioSink = SINKS_DEFAULT
		elif playerCfg.sink.value == "experimental":
			videoSink, audioSink = SINKS_EXPERIMENTAL
		else:
			continue
		subtitleEnabled = playerCfg.subtitleEnabled.value
		bufferSize = playerCfg.bufferSize.value
		bufferDuration = playerCfg.bufferDuration.value

		serviceapp_client.setGstreamerPlayerSettings(settingId, videoSink, audioSink, subtitleEnabled, bufferSize, bufferDuration)

	if configServiceApp.servicemp3.player.value == "gstplayer":
		serviceapp_client.setServiceMP3GstPlayer()
	elif configServiceApp.servicemp3.player.value == "exteplayer3":
		serviceapp_client.setServiceMP3ExtEplayer3()

initServiceAppSettings()


class ServiceAppSettings(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="400,400" title="ServiceApp Settings" backgroundColor="#48080808">
			<widget name="config" position="10,10" size="380,380" />
		</screen> """

	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session)
		self.onLayoutFinish.append(self.initConfigList)
		self.onClose.append(self.deInitConfig)
		self["actions"] = ActionMap(["SetupActions"], {"ok": self.keyOk, "cancel": self.keyCancel}, -2)

	def initConfigList(self):
		configServiceApp.servicemp3.player.addNotifier(self.serviceMP3PlayerChanged, initial_call=False)
		configServiceApp.servicemp3.replace.addNotifier(self.serviceMP3ReplacedChanged, initial_call=False)
		self["config"].setList(self.buildConfigList())

	def buildConfigList(self):
		configList = [getConfigListEntry(_("Enigma2 playback system"), configServiceApp.servicemp3.replace)]
		if configServiceApp.servicemp3.replace.value:
			configList.append(getConfigListEntry(_("Player"), configServiceApp.servicemp3.player))
			if configServiceApp.servicemp3.player.value == "gstplayer":
				gstPlayerOptionsCfg = configServiceApp.gstplayer["servicemp3"]
				configList.append(getConfigListEntry("", ConfigNothing()))
				configList.append(getConfigListEntry(_("ServiceMp3 (%s)" % str(serviceapp_client.ID_SERVICEMP3)), ConfigNothing()))
				configList.append(getConfigListEntry("  " + _("Sink"), gstPlayerOptionsCfg.sink))
				configList.append(getConfigListEntry("  " + _("Subtitles"), gstPlayerOptionsCfg.subtitleEnabled))
				configList.append(getConfigListEntry("  " + _("Buffer size"), gstPlayerOptionsCfg.bufferSize))
				configList.append(getConfigListEntry("  " + _("Buffer duration"), gstPlayerOptionsCfg.bufferDuration))
			else:
				configList.append(getConfigListEntry("", ConfigNothing()))
				configList.append(getConfigListEntry(_("ServiceMp3 (%s)" % str(serviceapp_client.ID_SERVICEMP3)), ConfigNothing()))
		gstPlayerOptionsCfg = configServiceApp.gstplayer["servicegstplayer"]
		configList.append(getConfigListEntry("", ConfigNothing()))
		configList.append(getConfigListEntry(_("ServiceGstPlayer (%s)" % str(serviceapp_client.ID_SERVICEGSTPLAYER)), ConfigNothing()))
		configList.append(getConfigListEntry("  " + _("Sink"), gstPlayerOptionsCfg.sink))
		configList.append(getConfigListEntry("  " + _("Subtitles"), gstPlayerOptionsCfg.subtitleEnabled))
		configList.append(getConfigListEntry("  " + _("Buffer size"), gstPlayerOptionsCfg.bufferSize))
		configList.append(getConfigListEntry("  " + _("Buffer duration"), gstPlayerOptionsCfg.bufferDuration))
		configList.append(getConfigListEntry("", ConfigNothing()))
		configList.append(getConfigListEntry(_("ServiceExtEplayer3 (%s)" % str(serviceapp_client.ID_SERVICEEXTEPLAYER3)), ConfigNothing()))
		return configList

	def serviceMP3ReplacedChanged(self, configElement):
		self["config"].setList(self.buildConfigList())

	def serviceMP3PlayerChanged(self, configElement):
		self["config"].setList(self.buildConfigList())

	def deInitConfig(self):
		configServiceApp.servicemp3.player.removeNotifier(self.serviceMP3PlayerChanged)
		configServiceApp.servicemp3.replace.removeNotifier(self.serviceMP3ReplacedChanged)

	def keyOk(self):
		if configServiceApp.servicemp3.replace.isChanged():
			self.session.openWithCallback(self.saveSettingsAndClose, MessageBox, _("Enigma2 Playback System was changed and Enigma2 should be restarted\nDo you want to restart it now?"), type=MessageBox.TYPE_YESNO)
		else:
			self.saveSettingsAndClose()

	def saveSettingsAndClose(self, callback=False):
		initServiceAppSettings()
		if configServiceApp.servicemp3.replace.value:
			serviceapp_client.setServiceMP3Replace(True)
		else:
			serviceapp_client.setServiceMP3Replace(False)
		self.saveAll()
		self.close(callback)


def main(session, **kwargs):
	def restartE2(restart=False):
		if restart:
			from Screens.Standby import TryQuitMainloop
			session.open(TryQuitMainloop, 3)
	session.openWithCallback(restartE2, ServiceAppSettings)


def Plugins(**kwargs):
	return [PluginDescriptor(name=_("ServiceApp"), description=_("setup player framework"), where=PluginDescriptor.WHERE_PLUGINMENU, needsRestart=False, fnc=main)]
