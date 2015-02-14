% CAP_FCCS_get_updated_cuts
% 
% Prints a list of all cuts that will need to be regenerated during a root
% cut generation routine.
% 
% Inputs:
%   
%   basepath: Path to the primary analysis module for the cuts to be
%             updated.  For instance, the SuperCDMS HT analysis basepath is
%             the location of the scdmstools_HT repository. (str)
%   filelist: Name of the MatCAP generated filelist that corresponds to the
%             full dataset for the given analysis. (str)
%
%%%%%%%%%%

function CAP_FCCS_get_updated_cuts(basepath, filelist)

% Add separator to path
if basepath(end) ~= filesep
    basepath = [basepath filesep]
end

% Get old treefile
load([basepath 'CAP_buffer/' filelist '/CAP_FCCS_treefile.mat']);
CAP_FCCS_old = CAP_FCCS_revdatemap;

% Generate current treefile
CAP_init('MatCAP_user_setup.m',[basepath 'MatCAP/mgmt_files/filelists/' filelist '_filelist.mat'])

% Get new treefile
global CAP_global
CAP_FCCS_new = CAP_global.CAP_FCCS_revdatemap;

% Select only cuts
cc = strncmp('c',CAP_global.CAP_FCCS_revdatemap.keys(),1);

% Select only development quantities
matches = strfind(CAP_global.CAP_FCCS_revdatemap.keys(),'_dev');
cc1 = ~cellfun(@isempty,matches);

% Get list of cuts
cuts2check = CAP_FCCS_new.keys();
cuts2check = cuts2check(cc&cc1);

% Initialize array of cuts to regenerate
cuts2regen = {};

% Loop through all cuts to check
for i = 1:length(cuts2check)
    
    % Initialize cell array
    tempCuts = {};
    
    % Check if cut is already in list
    if any(~cellfun(@isempty,strfind(cuts2regen,cuts2check{i})))
        continue
    end
    
    % Get list of dependencies for the cut (includes the cut itself)
    downDepend = CAP_FCCS_search_tree(cuts2check{i},'down');
    
    % Check all revdates in dependency
    depChecks = false(length(downDepend),1);
    for j = 1:length(downDepend)
        
        % If cut doesn't exist in old tree
        if ~CAP_FCCS_old.isKey(downDepend{j})
            depChecks(j) = 1;
            
            % If cut exists in old tree, check the date
        else
            depChecks(j) = CAP_FCCS_new(downDepend{j}) ~= CAP_FCCS_old(downDepend{j});
        end
    end
    
    % If any of the functions have updated
    if any(depChecks)
        
        % If any of the dates are new, add two sets of cuts to list:
        %  1. Any cuts in down depend list (including itself)
        %  2. All cuts up the tree from these cuts
        
        % 1. Any dependency in down depend list (including itself)
        tempCuts = [tempCuts; downDepend(depChecks)]; %#ok<*AGROW>
        
        % 2. All dependency up the tree from these cuts
        for j = 1:length(tempCuts)
            upDepend = CAP_FCCS_search_tree(tempCuts{j},'up');
            tempCuts = [tempCuts; upDepend];
        end
        
        % The above strategy can lead to duplicates and possibly non cuts, so
        % we need to clean it up.
        
        % Remove duplicates
        tempCuts = unique(tempCuts);
        
        % Ensure it's a cut
        cc = strncmp('c',tempCuts,1);
        tempCuts = tempCuts(cc);
        
        % Make sure it's a development quantities
        matches = strfind(tempCuts,'_dev');
        cc1 = ~cellfun(@isempty,matches);
        tempCuts = tempCuts(cc1);
        
        % Store in output array
        cuts2regen = [cuts2regen; tempCuts];
    end
end

% Sort the list of cuts
cuts2regen = sort(unique(cuts2regen));

for i = 1:length(cuts2regen)
    disp(cuts2regen(i));
end
