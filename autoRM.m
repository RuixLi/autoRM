function autoRM
% a function wraps RMDegMap, RMSetParams and RMAreaMap together
% modified May, 2021 fix bug

[fname,fpath] = uigetfile('*.mat','select raw or degMap data file ...');

if fname == 0; return; end

dataDir = fullfile(fpath, fname);
degMapFlg = isinMatfile(dataDir,'dataL2R');

if degMapFlg
disp('using degMap file')
degMap = load(dataDir);
degMap.savDir = dataDir;
else
pause(1)
[configName,configPath] = uigetfile('*.json','select config file ...');
configDir = fullfile(configPath, configName);
if configName == 0; return; end
degMap = RMDegMap(dataDir, configDir);
end

if ~isfield(degMap,'param')
disp('set parameters')
app = RMSetParam(degMap);
waitfor(app)
end

RMAreaMap(degMap.savDir)
end

function bools = isinMatfile(matfileObject,fieldName)

% isinMatfile checks whether a field exists matfile object

% INPUT
% matfileObjec[matfile object/str], matfile object or its dir
% filedName[str/cell], a string of field name or a cell of strings

% OUTPUT
% bools[logical] bool values for true or false

% written by Ruix.Li in Oct,2020

if ischar(matfileObject)
VarInfo = who('-file', matfileObject);
else
filedir = matfileObject.Properties.Source;
VarInfo = who('-file', filedir);
end

if ~iscell(fieldName)
bools = ismember(fieldName, VarInfo);
else
nL = numel(fieldName);
bools = false(1,nL);

for i = 1:nL
    bools(i) = ismember(fieldName{i},VarInfo);
end

end
end