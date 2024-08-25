[Setup]
; General settings
AppName=PicPyles
AppVersion=1.0.0
DefaultDirName={autopf}\EthernalSystems\PicPyles
DefaultGroupName=PicPyles
AllowNoIcons=yes
OutputBaseFilename=PicPylesInstaller
Compression=lzma
SolidCompression=yes
AppPublisher=Ethernal Systems
AppPublisherURL=https://github.com/reish2/PicPyles
AppSupportURL=https://github.com/reish2/PicPyles
AppUpdatesURL=https://github.com/reish2/PicPyles
OutputDir=Output

[Files]
; Include the executable and any necessary files
Source: "dist\PicPyles\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Add icons for the application
Name: "{group}\PicPyles"; Filename: "{app}\PicPyles.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall PicPyles"; Filename: "{uninstallexe}"

[Run]
; Run the application after installation
Filename: "{app}\PicPyles.exe"; Description: "{cm:LaunchProgram,PicPyles}"; Flags: nowait postinstall skipifsilent

[Messages]
SetupAppTitle=PicPyles Installer
SetupWindowTitle=PicPyles Setup
FinishedLabel=PicPyles has been installed on your computer.

[Setup]
; Installer settings
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
ChangesAssociations=yes
