function degMap = RMDegMap(stack, config)
% RMDegMap return azimuth and elevation maps from retinotopic imaging data
% use fourier transform to calculate the phase of visual response

% INPUT
% stack[XYT or string], image data or directory of .mat image data
% config[struct or string], configurations used to calculate degMaps
% if no inputs, promp gui seletion

% OUTPUT
% degMaps[struct], contains degMapAzi and degMapElv and other files

%% data loading
if nargin == 0 % no input
    [fname,fpath] = uigetfile('*.mat','select data file ...');
    if fname == 0; return; end
    pause(1)
    [configName,configPath] = uigetfile('*.json','select config file ...');
    if configName == 0; return; end
    
    dataDir = fullfile(fpath, fname);
    stack = 0;
    configDir = fullfile(configPath, configName);
    config = jsondecode(fileread(configDir));
    savDir = configPath;
end

if ~exist('config','var') % no config
    [configName,configPath] = uigetfile('*.json','select configter file ...');
    configDir = fullfile(configPath, configName);
    if configName == 0; return; end
    savDir = configPath;
end

if ischar(stack) % give stack dir
    dataDir = stack;
end

if ischar(config) % give config dir
    configDir = config;
    savDir = fileparts(configDir);
end

%% check imaging file and configeter
config = jsondecode(fileread(configDir));
disp('config file loaded ...')
disp('and check configurations ...')
load(dataDir,'info')
T = info.Loops;

if T ~= config.realFrame; error('imaging file has wrong input configs'); end
verticalTrial = config.verticalFrame;
horizontalTrial = config.horizontalFrame;
interTrialFrame = config.interTrialFrame;
trialNum = config.trialNum;
gazeCenter = config.gazeCenter;
monitorResolution = config.monitorResolution;
monitorDisance = config.monitorDisance;
monitorSize = config.monitorSize;
frameRate = round(1000*T / (info.dTimeMSec(end) - info.dTimeMSec(1)));
config.frameRate = frameRate;
frameNumL2R = trialNum * verticalTrial;
frameNumR2L = frameNumL2R;
frameNumD2U = trialNum * horizontalTrial;
frameNumU2D = frameNumD2U;
totalFrame = frameNumL2R + frameNumR2L + frameNumD2U + frameNumU2D;

if totalFrame ~= config.realFrame; error('imaging file has wrong input configs'); end

% normaluize to dF/F
disp('processing data ...')
load(dataDir,'stack')
[d1,d2,~] = size(stack);
FOV = rescale(stack(:,:,1));
dataL2R = stack(:,:,1:frameNumL2R);
dataR2L = stack(:,:,frameNumL2R+1:frameNumL2R+frameNumR2L);
dataD2U = stack(:,:,frameNumL2R+frameNumR2L+1:frameNumL2R+frameNumR2L+frameNumD2U);
dataU2D = stack(:,:,frameNumL2R+frameNumR2L+frameNumD2U+1:end);
clear stack
avgL2R = squeeze(mean(reshape(double(dataL2R),d1,d2,verticalTrial,trialNum),4));
avgR2L = squeeze(mean(reshape(double(dataR2L),d1,d2,verticalTrial,trialNum),4));
avgD2U = squeeze(mean(reshape(double(dataD2U),d1,d2,horizontalTrial,trialNum),4));
avgU2D = squeeze(mean(reshape(double(dataU2D),d1,d2,horizontalTrial,trialNum),4));
avgL2R = avgL2R./repmat(mean(avgL2R,3),[1,1,verticalTrial]);
avgR2L = avgR2L./repmat(mean(avgR2L,3),[1,1,verticalTrial]);
avgD2U = avgD2U./repmat(mean(avgD2U,3),[1,1,horizontalTrial]);
avgU2D = avgU2D./repmat(mean(avgU2D,3),[1,1,horizontalTrial]);
avgL2R(isnan(avgL2R)) = 0;
avgR2L(isnan(avgR2L)) = 0;
avgD2U(isnan(avgD2U)) = 0;
avgU2D(isnan(avgU2D)) = 0;
avgL2R = avgL2R - movmean(avgL2R,30,3);
avgR2L = avgR2L - movmean(avgR2L,30,3);
avgD2U = avgD2U - movmean(avgD2U,30,3);
avgU2D = avgU2D - movmean(avgU2D,30,3);
clipL2R = avgL2R(:,:,interTrialFrame+1:end);
clipR2L = avgR2L(:,:,interTrialFrame+1:end);
clipD2U = avgD2U(:,:,interTrialFrame+1:end);
clipU2D = avgU2D(:,:,interTrialFrame+1:end);

% binning
binSiz = d1/256;
if binSiz >= 2
FOV = binning(FOV, [binSiz, binSiz])/ binSiz^2;
clipL2R = binning(clipL2R, [binSiz, binSiz, 1]) / binSiz^2;
clipR2L = binning(clipR2L, [binSiz, binSiz, 1]) / binSiz^2;
clipD2U = binning(clipD2U, [binSiz, binSiz, 1]) / binSiz^2;
clipU2D = binning(clipU2D, [binSiz, binSiz, 1]) / binSiz^2;
end
% calculate phase maps using fast fourier transform
ffdL2R = fft(clipL2R, [], 3);
ffdR2L = fft(clipR2L, [], 3);
ffdD2U = fft(clipD2U, [], 3);
ffdU2D = fft(clipU2D, [], 3);
phaseL2R = 2*pi - wrapTo2Pi(angle(ffdL2R(:,:,2))+2*pi);
phaseR2L = 2*pi - wrapTo2Pi(angle(ffdR2L(:,:,2))+2*pi);
phaseD2U = 2*pi - wrapTo2Pi(angle(ffdD2U(:,:,2))+2*pi);
phaseU2D = 2*pi - wrapTo2Pi(angle(ffdU2D(:,:,2))+2*pi);

% calculate visual field
disp('get degree maps ...')
gazePointX = 0.5 * monitorSize(1) * (monitorResolution(1) + gazeCenter(1)) / monitorResolution(1);
gazePointY = 0.5 * monitorSize(2) * (monitorResolution(2) + gazeCenter(2)) / monitorResolution(2);
visAzimuth = rad2deg(atan(gazePointX/monitorDisance)) + rad2deg(atan((monitorSize(1) - gazePointX)/monitorDisance));
visElevation = rad2deg(atan(gazePointY/monitorDisance)) + rad2deg(atan((monitorSize(2) - gazePointY)/monitorDisance));

degMapL2R = visAzimuth * phaseL2R / (2*pi);
degMapR2L = visAzimuth * (1 - phaseR2L / (2*pi));
degMapD2U = visElevation * phaseD2U / (2*pi) - rad2deg(atan(gazePointY/monitorDisance));
degMapU2D = visElevation * (1 - phaseU2D / (2*pi)) - rad2deg(atan(gazePointY/monitorDisance));

degMapAzi = (degMapL2R + degMapR2L) / 2;
degMapElv = (degMapD2U + degMapU2D) / 2;


h = figure('Position',[200,200,900,320]);
ax(1) = subplot('Position',[0.03,0.1,0.3,0.9]);
imagesc(FOV)
title('FOV')
colorbar;
axis tight; axis equal; axis off;
cm = gray(128);
colormap(ax(1), cm)
ax(2) = subplot('Position',[0.37,0.1,0.3,0.9]);
imagesc(imgaussfilt(degMapAzi,3))
title('visual azimuth')
colorbar;
axis tight; axis equal; axis off;
try cm = turbo(128); catch; cm=gray(128); end
colormap(ax(2), cm)
ax(3) = subplot('Position',[0.68,0.1,0.3,0.9]);
imagesc(imgaussfilt(degMapElv,3))
title('visual elevation')
colorbar;
colormap(ax(3), cm)
axis tight; axis equal; axis off;

maps.config = config;
maps.FOV = FOV;
maps.dataL2R = single(clipL2R);
maps.dataR2L = single(clipR2L);
maps.dataD2U = single(clipD2U);
maps.dataU2D = single(clipU2D);
maps.phaseMapL2R = phaseL2R;
maps.phaseMapR2L = phaseR2L;
maps.phaseMapD2U = phaseD2U;
maps.phaseMapU2D = phaseU2D;
maps.degMapL2R = degMapL2R;
maps.degMapR2L = degMapR2L;
maps.degMapD2U = degMapD2U;
maps.degMapU2D = degMapU2D;
maps.degMapAzi = degMapAzi;
maps.degMapElv = degMapElv;

if exist('savDir', 'var')
    disp('saving data ...')
    fName = ['RMDegMap-' config.subjectID '-' config.dateTimeStamp '.mat'];
    tName = ['RMDegMap-' config.subjectID '-' config.dateTimeStamp '.tiff'];
    maps.savDir = fullfile(savDir,fName);
    save(fullfile(savDir,fName), '-struct', 'maps')
    saveas(h, fullfile(savDir,tName), '-r300', '-transparent')
end

if nargout > 0; degMap = maps; end

end