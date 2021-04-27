function autoRM
% a function wraps RMDegMap, RMSetParams and RMAreaMap together
[fname,fpath] = uigetfile('*.mat','select raw or degMap data file ...');
if fname == 0; return; end
dataDir = fullfile(fpath, fname);
degMapFlg = isinMatfile(dataDir,'dataL2R');

if degMapFlg
disp('using degMap file')
degMap = load(dataDir);
else
pause(1)
[configName,configPath] = uigetfile('*.json','select config file ...');
configDir = fullfile(configPath, configName);
if configName == 0; return; end
degMap = RMDegMap(dataDir, configDir);
end
app = RMSetParam(degMap);
waitfor(app)
RMAreaMap(degMap.savDir)
end