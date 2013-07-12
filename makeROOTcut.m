%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% function success = makeROOTcut(dataDir,cutDir,cutStruct)
% 
% Script  to produce ROOT cut files
%
% Input: 
%    (1) Path to RQ data directory:  string or cell array of strings 
%    (2) Path to cut ROOT files directory: string 
%    (3) Structure with cuts and CVS version (string)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function status = makeROOTcut22(dataDir, cutDir, cut, version)
  
  cutStruct = struct(cut, version);
  
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % SETUP/INPUT
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
  
  
  % cdmstools path
  pathCAP = '/data3/cdmsbatsProd/processing/cdmstools/';
    
  % initialize success flag
  status = 0;
  
  
  % ========== CAP paths =========
  cd(pathCAP);
  cdmsStartup;
  add_CAP_paths;
  
  
  % ===========  INPUT ===========
  
  % --- check RQ data dir ---  
  if ischar(dataDir)
    dataDir = cellstr(dataDir);
  end;
  
  for ii=1:length(dataDir)
    if exist(dataDir{ii})~=7
      disp('ERROR in makROOTcut: A data directory not found');
      return;
    end
  end
  
  
  % --- check cut dir ---
  if exist(cutDir)~=7
    disp('ERROR in makROOTcut: No cut directory found');
    return;
  end
    
  
  % --- check  cuts ---
  if isempty(cutStruct)
    return;
  end
  
  
  
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % LOAD DATA
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
  
 
  CAPtree = [pathCAP '/CAP_user/matfile/CAP_FCCS_treefile.mat'];
  if ~exist(CAPtree)
    disp('ERROR in makROOTcut: No CAP FCCS Tree available!');
    return;
  end
  
  % ----  Start CAP session ---
  success = CAP_root_init('CAP_batch_setup',0,dataDir); 
   
  if (~success)
    disp('ERROR in makROOTcut: CAP_root_init failed, unable to load the data!');
    return;
  end
  
  
  
  
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % CALCULATE AND SAVE CUTS
  % %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    
    
  % --- get CUT list ----
  cutList = fieldnames(cutStruct);
 
  
  % --- get GLOBAL variables ---
  CAP_FCCS_mgmt_globs; 
  
  % --- get a list of detectors ---
  CAP_namemap_globs
  detList = CAP_detlist;
  cGen = ~(detList ==1); % remove "1" (use to tag non specific RQs) 
  detList = detList(cGen);
  
  %TEMP/TEMP: remove cdmslite
  cLite = ~( (detList-mod(detList,100))/100 == 21);
  detList = sort(detList(cLite));
      
  % --- get seriesnumber - filenames map
  filemap = CAP_get_sn_fileroot_map;
  sn = SeriesNumber(0);
  
  
  
  %  ======= EVENT level cuts =======
  
  for icut=1:length(cutList)
    
    
    % ---  cut name/version ---
    cutName = cutList{icut};
    cutVersion = cutStruct.(cutName);
    
    % --- check FCCS cut exist ---
    fullcutName = which(cutName);
    
    if isempty(fullcutName)
      disp(['ERROR in makROOTcut: Cannot find "' cutName '" CAP cut']);
      return;
    end
    
    % determine if  detector dependent
    try
     [dependlist, isgen] = CAP_FCCS_parse_func(fullcutName);
    catch err
      disp(['ERROR in makROOTcut: Error parsing function ' fullcutName ]);
      return;
    end
    

    % Only  event based cuts
    if isgen~=1
      continue;
    end    
    
    % --- create cutName directory ---
    fullCutDir = [cutDir '/' cutName];
    if ~exist(fullCutDir)
      mkdir(fullCutDir);
    end
    
    
    % --- convert cut name into function  ---
    cutFunc = str2func(cutName);
    
       
    % --- get value ---
    try
      cut = cutFunc();
    catch err
      disp(['ERROR in makROOTcut: Error getting cut values for ' cutName]);
      return;
    end

  
    % --- LOOP file map  and save cut ---
    for ifile = 1:length(filemap.SeriesNumber)
     
      % get events corresponding to file
      cutSeries = ismember(sn,filemap.SeriesNumber{ifile});
              
      % create File Name
      fullFileName = [fullCutDir '/' cutName '_' filemap.fileroot{ifile} '.root'];
      
      % save data
      RRQ = [];
      RRQ.([cutName]) = double(cut(cutSeries));
	 

      try 
        root_save(fullFileName,'create','cutDir','cutevent',fieldnames(RRQ),struct2cell(RRQ));	
        root_save(fullFileName,'update','cutInfoDir','cvsInfo',{'cvsRevision'},{cutVersion});	
      catch err
        disp(['ERROR saving ROOT file ' fullFileName]);
        return;
      end;

    end
    
    % cleanup
    clear cut;
    
  end
  
  % ==== delete buffer ====
  CAP_delete_buff_col(1);
  
  
  
  
  %  ======= DETECTOR level cuts =======
  
  
  % loop detectors
  createRootFile =1;
  for idet=1:length(detList)
    
     % CAP detnum
     detnum = detList(idet);
     det = mod(detnum,100);
     dettype = (detnum-det)/100;
     
        
     % loop cuts
     for icut=1:length(cutList)
       
       % ---  cut name/version ---
       cutName = cutList{icut};
       cutVersion = cutStruct.(cutName);
       
       % --- check FCCS cut exist ---
       fullcutName = which(cutName);
       
       if isempty(fullcutName)
	 disp(['ERROR in makROOTcut: Cannot find "' cutName '" CAP cut']);
	 return;
       end
       
       % determine if  detector dependent
       try
         [dependlist, isgen] = CAP_FCCS_parse_func(fullcutName);
       catch err
         disp(['ERROR in makROOTcut: Error parsing function ' fullcutName ]);
         return;
       end
       
       
       % only detector dependent cuts
       if isgen==1
	 continue;
       end
       
       
       % --- create cutName directory ---
       fullCutDir = [cutDir '/' cutName];
       if ~exist(fullCutDir)
	  mkdir(fullCutDir);
       end
	
       
       % --- convert cut name into function  ---
       cutFunc = str2func(cutName);
	
       % --- get value ---
       if (dettype==11)

         try
           cut = cutFunc(detnum);
         catch err
	   disp(['ERROR in makROOTcut: Error getting cut values for ' cutName]);
           return;
         end

       else
	 cut = zeros(size(DetType(detnum,0)));
       end
       
              
       % --- LOOP file map  and save cut ---
       for ifile = 1:length(filemap.SeriesNumber)
     
	 % get events corresponding to file
	 cutSeries = ismember(sn,filemap.SeriesNumber{ifile});
              
	 
	 % check detector type
	 cutType= cutSeries & DetType(detnum,0)==dettype;
	 if sum(cutType)==0
	   continue;
	 end
	 
	 
	 %  Get RRQs
	 RRQ = [];
	 RRQ.Empty = Empty(detnum,cutSeries);
	 RRQ.DetType = DetType(detnum,cutSeries);
	 RRQ.([cutName]) = double(cut(cutSeries));
	 
	 
	 % save data
	 fullFileName = [fullCutDir '/' cutName '_' filemap.fileroot{ifile} '.root'];
	 treeName = ['cutzip' num2str(det)];

	 % save CVS info
         try
	   if  createRootFile ==1;
	     root_save(fullFileName,'create','cutDir',treeName,fieldnames(RRQ),struct2cell(RRQ));
	     root_save(fullFileName,'update','cutInfoDir','cvsInfo',{'cvsRevision'},{cutVersion});	
	   else
	     root_save(fullFileName,'update','cutDir',treeName,fieldnames(RRQ),struct2cell(RRQ));
	   end
	 catch err
	   disp(['ERROR saving ROOT file ' fullFileName]);
           return;
         end;


	 % cleanup
	 clear RRQ;
	 
       end % end series
       
       % cleanup
       clear cut;
     
     end % end cuts
     
     % ==== delete buffer ====
     CAP_delete_buff_col(detnum);
     createRootFile = 0; % info already saved
  end
   
  
  status = 1;
  return;
   
