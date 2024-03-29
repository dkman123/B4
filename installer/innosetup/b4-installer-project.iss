; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

;#define Debug

; NOTE: either uncomment the two constants below or call the InnoSetup PreProcessor with the /d<name>=<value> command
;       line parameter. I.E.: ISCC.exe b4-installer-project.iss /Q /O../dist /dB4_VERSION_NUMBER=1.9.0 /dB4_VERSION_SUFFIX=dev6-20120930
;#define public B4_VERSION_NUMBER "x.y.z"
;#define public B4_VERSION_SUFFIX "xxx"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppID=5FB180C6-A3B4-46CF-85E0-F00168F1569D
AppName=BigBrotherBot
AppVerName=BigBrotherBot {#B4_VERSION_NUMBER}{#B4_VERSION_SUFFIX}
AppPublisher=BigBrotherBot
AppPublisherURL=http://www.bigbrotherbot.net/
AppSupportURL=http://www.bigbrotherbot.net/
AppUpdatesURL=http://www.bigbrotherbot.net/
AppCopyright=Copyright (C) 2024 BigBrotherBot.net
DefaultDirName={sd}\BigBrotherBot
DefaultGroupName=BigBrotherBot
LicenseFile=../assets_common\gpl-2.0.txt
OutputBaseFilename=b4-{#B4_VERSION_NUMBER}{#B4_VERSION_SUFFIX}-{#B4_VERSION_PLATFORM}{#B4_VERSION_ARCHITECTURE}
Compression=lzma/Ultra64
SolidCompression=true
InternalCompressLevel=Normal
DisableStartupPrompt=true
SetupLogging=true
VersionInfoVersion=1.0
VersionInfoDescription=B4 installation
VersionInfoCopyright=www.bigbrotherbot.net
VersionInfoTextVersion=1.0
VersionInfoProductName=BigBrotherBot
VersionInfoProductVersion={#B4_VERSION_NUMBER}
ExtraDiskSpaceRequired=111087522         
RestartIfNeededByRun=false
PrivilegesRequired=none
WizardImageBackColor=clBlack
WindowVisible=false
BackColor=clBlack
BackColor2=clGray
WizardSmallImageFile=../assets_common\WizB4SmallImage.bmp
WizardImageFile=../assets_common\WizB4Image.bmp
UsePreviousAppDir=true
AlwaysShowDirOnReadyPage=true
AlwaysShowGroupOnReadyPage=true
VersionInfoCompany=BigBrotherBot.net
WindowShowCaption=false
WindowResizable=false
SetupIconFile=../assets_common\b4.ico
EnableDirDoesntExistWarning=false
DirExistsWarning=yes
DisableProgramGroupPage=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "greek"; MessagesFile: "compiler:Languages\Greek.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "serbiancyrillic"; MessagesFile: "compiler:Languages\SerbianCyrillic.isl"
Name: "serbianlatin"; MessagesFile: "compiler:Languages\SerbianLatin.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Icons]
Name: "{commondesktop}\{cm:executable,b4}"; Filename: "{app}\b4.exe"; WorkingDir: "{app}"; Flags: dontcloseonexit; IconFilename: "{app}\b4.ico"; Comment: "Run BigBrotherBot {#B4_VERSION_NUMBER}{#B4_VERSION_SUFFIX}"
Name: "{group}\{cm:configWizard,Config wizard}"; Filename: "http://config.bigbrotherbot.net/"; Comment: "Run the B4 setup wizard"
Name: "{group}\{cm:B4ConfDir,config}"; \
    Filename: "{app}\extplugins\"; \
    IconFilename: "{app}\b4-plugins-icon.ico"
Name: "{group}\Extra\{cm:docs,docs}"; \
    Filename: "{uninstallexe}"
#Name: "{group}\Web\{cm:Website,BigBrotherBot}"; Filename: "http://www.bigbrotherbot.net/"
#Name: "{group}\Web\{cm:Manual,Manual}"; Filename: "http://wiki.github.com/BigBrotherBot/big-brother-bot/manual"
#Name: "{group}\Web\{cm:Forums,B4 Forums}"; Filename: "http://forum.bigbrotherbot.net/"
#Name: "{group}\Web\{cm:DownloadPlugins,Download plugins}"; Filename: "http://forum.bigbrotherbot.net/downloads/?cat=4"
#Name: "{group}\Web\{cm:B4configGenerator,B4 config generator}"; Filename: "http://config.bigbrotherbot.net/"
#Name: "{group}\Web\Artwork"; Filename: "http://www.bigbrotherbot.net/logos"
Name: "{group}\Web\Other tools\{cm:Echelon,Echelon}"; Filename: "https://github.com/dkman123/Echelon-2/"

;[Dirs]
;Name: {commonappdata}\BigBrotherBot; Permissions: users-full
Name: "{group}\Web\other tools\{cm:Xlrstats,XLRstats}"; Filename: "http://www.xlrstats.com/"

[Files]
Source: {app}\conf\*; DestDir: {app}\conf\backup; Flags: external skipifsourcedoesntexist uninsneveruninstall
Source: ../assets_common\readme-windows.txt; DestDir: "{app}"
Source: ../assets_common\gpl-2.0.txt; DestDir: {app}; DestName: license.txt;
Source: ../assets_common\readme-windows.txt; DestDir: {app}; DestName: readme.txt;
Source: ../assets_common\b4.ico; DestDir: {app}
Source: ../assets_common\b4-plugins-icon.ico; DestDir: {app}
Source: {#B4_BUILD_PATH}\b4.exe; DestDir: {app}
Source: {#B4_BUILD_PATH}\b4.exe; DestDir: {app}
Source: {#B4_BUILD_PATH}\PKG-INFO; DestDir: {app}
Source: {#B4_BUILD_PATH}\README.md; DestDir: {app};
Source: {#B4_BUILD_PATH}\*.dll; DestDir: {app}
Source: {#B4_BUILD_PATH}\*.pyd; DestDir: {app}
Source: {#B4_BUILD_PATH}\docs\*; DestDir: {app}\docs; Flags: recursesubdirs
Source: {#B4_BUILD_PATH}\sql\*; DestDir: {app}\sql; Flags: recursesubdirs
Source: {#B4_BUILD_PATH}\extplugins\*; DestDir: {app}\extplugins; Flags: recursesubdirs
Source: {#B4_BUILD_PATH}\conf\*; DestDir: {app}\conf; Flags: recursesubdirs
Source: {#B4_BUILD_PATH}\plugins\*; DestDir: {app}\plugins; Flags: recursesubdirs
Source: ../../examples\*; DestDir: "{app}\examples"; Flags: recursesubdirs

[UninstallDelete]
Name: {app}\*; Type: filesandordirs

[CustomMessages]
Website=BigBrotherBot Website
Forums=Forums
Manual=Manual
B4ConfDir=Configuration folder
extplugins=Plugins folder
configWizard=Run B4 config wizard
updateWizard=Update B4 database
executable=Run B4
DownloadPlugins=Download more plugins
Echelon=Echelon
Xlrstats=XLRstats
B4configGenerator=B4 config generator
sql=SQL folder
docs=Docs folder
executable=Run B4

[Run]
Filename: "{app}\readme.txt"; Flags: ShellExec SkipIfDoesntExist
