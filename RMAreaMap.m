function areaMap = RMAreaMap(degMap, param)
% RMAreaMap process degMap to identify visual areas
% INPUT
% degMap [struct or str] contains visual field degree Maps or its directory
% param [struct] contains parameters optional
% savDir save dir

% OUTPUT
% areaMap [struct] contains visual area maps

if nargin == 0 % no input
    [fname,fpath] = uigetfile('*.mat','select data file ...');
    dataDir = fullfile(fpath, fname);
    degMap = load(dataDir);
    if isfield(degMap,'param'); param = degMap.param; end
end

if ischar(degMap)
    dataDir = degMap;
    degMap = load(dataDir);
    if isfield(degMap,'param'); param = degMap.param; end
end

if ~exist('param','var')
    disp('using default parameters')
    disp('you can set parameter with RMsetParams.mlapp')
    param.degMapFltSigma = 6; % gaussian filter sigma
    param.signMapFltSigma = 8; % gaussian filter sigma
    param.signMapThreshold = 0.6; % increase to include less areas
    param.signMapErosion = 4; % increase for smoother area
    param.patchMapThreshold = 0.3; % increase to include less areas
    param.patchMapErosion = 6; % increase to include less areas
    param.patchMapExtention = 5; % increase to include more areas
end

%% calculate the raw viusal sign map, no parameter needed here
[dhdx, dhdy] = gradient(degMap.degMapAzi);
[dvdx, dvdy] = gradient(degMap.degMapElv);
graddirX = atan2(dhdy,dhdx);
graddirY = atan2(dvdy,dvdx);
vdiff = exp(1i*graddirX) .* exp(-1i*graddirY);
signMap = sin(angle(vdiff));
signMap(isnan(signMap)==1) = 0;
%imview(signMap)

% calculate additional maps with some imaging process tricks
% step1: filter the degMaps to make the gradient smooth
degMapAziFt = imgaussfilt(degMap.degMapAzi, param.degMapFltSigma);
degMapElvFt = imgaussfilt(degMap.degMapElv, param.degMapFltSigma);
%imview(cat(2,degMapAziFt-60,2*degMapElvFt))

% step2: calculate binarized visual sign map
[dhdx, dhdy] = gradient(degMapAziFt);
[dvdx, dvdy] = gradient(degMapElvFt);
graddirX = atan2(dhdy,dhdx);
graddirY = atan2(dvdy,dvdx);
vdiff = exp(1i*graddirX) .* exp(-1i*graddirY);
signMapU = sin(angle(vdiff));
signMapU(isnan(signMapU)==1) = 0;
signMapFt = imgaussfilt(signMapU, param.signMapFltSigma);
signMapThrd = signMapFt;
signMapThreshold = (param.signMapThreshold * std(signMapFt(:)));
signMapThrd(signMapThrd>=signMapThreshold) = 1;
signMapThrd(signMapThrd<=-1*signMapThreshold) = -1;
signMapThrd((signMapThrd>-1*signMapThreshold)&(signMapThrd<signMapThreshold)) = 0;
%imview(signMapThrd)
signMapPos = signMapThrd;
signMapPos(signMapPos ~= 1) = 0;
signMapPos = imfill(signMapPos);
signMapPos = imopen(signMapPos, strel('disk', param.signMapErosion, 0));
signMapPos = imclose(signMapPos, strel('disk', param.signMapErosion, 0));
signMapNeg = -1*signMapThrd;
signMapNeg(signMapNeg ~= 1) = 0;
signMapNeg = imfill(signMapNeg);
signMapNeg = imopen(signMapNeg, strel('disk', param.signMapErosion, 0));
signMapNeg = imclose(signMapNeg, strel('disk', param.signMapErosion, 0));
signMapTz = signMapPos - signMapNeg;
signMapBz = signMapPos + signMapNeg;
%imview(signMapTz)

%% step3 : remove background samll areas
patchMapBz = imgaussfilt(signMapU, 1);
patchThreshold = (param.patchMapThreshold * std(patchMapBz(:)));
patchMapBz(patchMapBz>=patchThreshold) = 1;
patchMapBz(patchMapBz<=-1*patchThreshold) = -1;
patchMapBz((patchMapBz>-1*patchThreshold)&(patchMapBz<patchThreshold)) = 0;
patchMapBz = abs(patchMapBz);
imSiz = size(patchMapBz, 1);
padWidth = round(imSiz/8);
imL = [zeros(imSiz,padWidth) patchMapBz zeros(imSiz,padWidth)];
imSiz = size(imL, 2);
imL = [zeros(padWidth,imSiz); imL; zeros(padWidth,imSiz)];
patchMapOp = imopen(imL,strel('disk',param.patchMapErosion, 0));
patchMapCls = imclose(patchMapOp,strel('disk', param.patchMapExtention, 0));
patchMapCls = imfill(patchMapCls);
patchMapCls = imdilate(patchMapCls,strel('disk', 2, 0));
patchMapCls = imfill(patchMapCls);
patchMap = patchMapCls(padWidth+1:end-padWidth,padWidth+1:end-padWidth);
labelMap = bwlabel(patchMap,4);
patchList = unique(labelMap);
patchSize = zeros(1,length(patchList));
for iPatch = 1:length(patchList)
    patchIdx = find(labelMap == patchList(iPatch));
    patchSize(iPatch) = length(patchIdx);
end
patchSize(1) = 0;
[~, mainPatches] = max(patchSize);
patchMap(labelMap ~= patchList(mainPatches)) = 0;
signMapTz = patchMap .* signMapTz;
signMapBz = patchMap .* signMapBz;
%imview(signMapTz)

%% step4: output the results
FOV = degMap.FOV;
signFOV = cat(3, .7*FOV+.3*signMap, .6*FOV, .7*FOV-0.3*signMap);
tzFOV = cat(3, .7*FOV+.3*signMapTz, .6*FOV, .7*FOV-0.3*signMapTz);
bzFOV = 0.6 * degMap.FOV .* signMapBz + 0.3 * degMap.FOV;
%%
config = degMap.config;
h = figure('Position',[100,100,900,600]);
ax(1) = subplot('Position',[0.07,0.50,0.3,0.42]);
imshow(FOV)
title([config.subjectID '-' config.dateTimeStamp])
cm = gray(128);

ax(2) = subplot('Position',[0.07,0.04,0.3,0.42]);
imshow(bzFOV)
title('high light')
axis tight; axis equal; axis off;

ax(3) = subplot('Position',[0.37,0.50,0.3,0.42]);
imshow(signFOV)
title('raw sign')

ax(4) = subplot('Position',[0.37,0.04,0.3,0.42]);
imshow(tzFOV)
title('visual sign')

ax(5) = subplot('Position',[0.67,0.04,0.3,0.42]);
imagesc(degMap.degMapAzi)
axis equal; axis tight; axis off;
title('azimuth')
try cm = turbo(64); catch ; cm = gray(64); end
colormap(ax(5),cm)

ax(6) = subplot('Position',[0.67,0.50,0.3,0.42]);
imagesc(degMap.degMapElv);
axis equal; axis tight; axis off;
title('elevation')
colormap(ax(6),cm)

%% save data
maps.FOV = FOV;
maps.rSignMap = signMap;
maps.signMap = signMapTz;
maps.areaMap = signMapBz;
maps.hitFOV = bzFOV;
maps.signFOV = tzFOV;
maps.param = param;
maps.config = config;
maps.degMapAzi = degMap.degMapAzi;
maps.degMapElv = degMap.degMapElv;
savDir = strrep(dataDir,'RMDegMap','RMAreaMap');
maps.savDir = savDir;

save(savDir, '-struct', 'maps');
savDir = [savDir(1:end-4) '.tiff'];
saveas(h, savDir, '-r500', '-transparent')

if nargout > 0; areaMap = maps; end
end