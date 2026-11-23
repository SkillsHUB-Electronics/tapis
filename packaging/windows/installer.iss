; Inno Setup script: one offline setup.exe with the frozen app and VB-CABLE.
; Build: iscc /DAppVersion=0.2.0 packaging\windows\installer.iss
;   expects dist\Tapis\ (PyInstaller output) and build\vbcable\ (extracted VBCABLE_Driver_Pack)

#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif
#define Root "..\.."

[Setup]
; The AppId is unchanged since the app was called "Noise Filter", so this setup updates an old
; installation in place of adding a second one (see [InstallDelete] and CurStepChanged below).
AppId={{6F0B7C1E-2B7A-4E8B-9C55-4C1F2E1A9D31}
AppName=Tapis
AppVersion={#AppVersion}
AppPublisher=SkillsHUB Electronics
DefaultDirName={autopf}\Tapis
DefaultGroupName=Tapis
; move old "Noise Filter" installations to the new folder and Start menu group
UsePreviousAppDir=no
UsePreviousGroup=no
OutputDir={#Root}\dist
OutputBaseFilename=Tapis-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
UninstallDisplayIcon={app}\Tapis.exe
CloseApplications=force
ChangesEnvironment=yes
SetupIconFile={#Root}\noise_filter\assets\icon.ico
LicenseFile={#Root}\LICENSE
InfoBeforeFile={#Root}\packaging\windows\VB-CABLE-NOTICE.txt

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
; Inno Setup has no official Indonesian translation, so key lines are bilingual.
InstallCable=Install VB-CABLE virtual microphone / Pasang mic virtual VB-CABLE
CableInstalling=Installing VB-CABLE... / Memasang VB-CABLE...
AddToPath=Add the tapisctl command (control by command line / AI) to PATH / Tambahkan perintah tapisctl ke PATH

[Tasks]
Name: "vbcable"; Description: "{cm:InstallCable}"; Check: not CableInstalled
Name: "addtopath"; Description: "{cm:AddToPath}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#Root}\dist\Tapis\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Root}\packaging\windows\VB-CABLE-NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "{#Root}\PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\build\vbcable\*"; DestDir: "{tmp}\vbcable"; Flags: ignoreversion recursesubdirs deleteafterinstall; Tasks: vbcable

[InstallDelete]
; leftovers of the old name "Noise Filter" (before 0.11.0); settings in %APPDATA% are kept and moved by the app
Type: filesandordirs; Name: "{autopf}\Noise Filter"
Type: filesandordirs; Name: "{autoprograms}\Noise Filter"
Type: files; Name: "{autodesktop}\Noise Filter.lnk"
Type: files; Name: "{commondesktop}\Noise Filter.lnk"

[Icons]
Name: "{group}\Tapis"; Filename: "{app}\Tapis.exe"
Name: "{group}\{cm:UninstallProgram,Tapis}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tapis"; Filename: "{app}\Tapis.exe"; Tasks: desktopicon

[Registry]
; The app writes this value itself ("Start with Windows" setting); remove it on uninstall.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "Tapis"; \
  ValueType: none; Flags: uninsdeletevalue dontcreatekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "NoiseFilter"; \
  ValueType: none; Flags: uninsdeletevalue dontcreatekey

; tapisctl.exe (command-line / AI control) is reachable from any terminal
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueName: "Path"; \
  ValueType: expandsz; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{tmp}\vbcable\VBCABLE_Setup_x64.exe"; Parameters: "-i -h"; StatusMsg: "{cm:CableInstalling}"; \
  Flags: waituntilterminated; Tasks: vbcable; AfterInstall: AfterCable
Filename: "{app}\Tapis.exe"; Description: "{cm:LaunchProgram,Tapis}"; Flags: nowait postinstall skipifsilent

[Code]
var CableJustInstalled: Boolean;

function CableInstalled: Boolean;
begin
  Result := FileExists(ExpandConstant('{sys}\drivers\vbaudio_cable64_win10.sys')) or
            FileExists(ExpandConstant('{sys}\drivers\vbaudio_cable64_win7.sys')) or
            FileExists(ExpandConstant('{sys}\drivers\vbaudio_cable64arm_win10.sys'));
end;

procedure AfterCable;
var Code: Integer;
begin
  if not CableInstalled then
    { silent install did not take: show the VB-Audio setup window instead }
    Exec(ExpandConstant('{tmp}\vbcable\VBCABLE_Setup_x64.exe'), '', '', SW_SHOW, ewWaitUntilTerminated, Code);
  CableJustInstalled := CableInstalled;
end;

const EnvKey = 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';

function NeedsAddPath(Dir: string): Boolean;
var Paths: string;
begin
  if not RegQueryStringValue(HKLM, EnvKey, 'Path', Paths) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Paths) + ';') = 0;
end;

procedure RemovePath(Dir: string);
var Paths: string; P: Integer;
begin
  if not RegQueryStringValue(HKLM, EnvKey, 'Path', Paths) then exit;
  P := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Paths) + ';');
  if P = 0 then exit;
  { P is the position of the separator in front of Dir in ';' + Paths + ';' }
  if P = 1 then
    Delete(Paths, 1, Length(Dir) + 1)
  else
    Delete(Paths, P - 1, Length(Dir) + 1);
  RegWriteExpandStringValue(HKLM, EnvKey, 'Path', Paths);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  { an old "Noise Filter" may still be running from the folder that [InstallDelete] removes }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM NoiseFilter.exe', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

const RunKey = 'Software\Microsoft\Windows\CurrentVersion\Run';

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { the old install folder is gone, so take it off PATH }
    RemovePath(ExpandConstant('{autopf}\Noise Filter'));
    { keep "Start with Windows" on for people who had it on under the old name }
    if RegValueExists(HKCU, RunKey, 'NoiseFilter') then
    begin
      RegWriteStringValue(HKCU, RunKey, 'Tapis', '"' + ExpandConstant('{app}\Tapis.exe') + '" ui --minimized');
      RegDeleteValue(HKCU, RunKey, 'NoiseFilter');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemovePath(ExpandConstant('{app}'));
end;

function NeedRestart: Boolean;
begin
  Result := CableJustInstalled;
end;

