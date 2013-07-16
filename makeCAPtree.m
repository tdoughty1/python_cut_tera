%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% function success = makeCAPtree;
% 
% Script to regenerate CAP FCCS tree
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function success = makeCAPtree;

% ========== CAP paths =========
   
pathCAP = '/tera2/data3/cdmsbatsProd/processing/cdmstools';


cd(pathCAP);
run(setupUtility/cdmsStartup);
run(setupUtility/add_CAP_paths);


% ========= Regenerate Tree =========
  
CAPtree = [pathCAP '/CAP_user/matfile/CAP_FCCS_treefile.mat'];
if exist(CAPtree)
  delete(CAPtree);
end

try
 success = CAP_FCCS_regen_tree;
catch err
 error('ERROR in makeCAPtree: unable to make CAP FCCS tree');
 return;
end;

return;


  
