from pathlib import Path
import sys, os, importlib, copy
from io import BytesIO
from unittest.mock import patch
import pandas as pd
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base))
sys.path.insert(0,str(base/'validation/reference'))
from backend.features.pubmed_scraper import legacy_adapter as adapter
original_base=importlib.import_module('PubmedScraper').PubmedScraper
app_base=importlib.import_module('backend.features.pubmed_scraper.legacy.PubmedScraper').PubmedScraper
original_classes={mode:importlib.import_module(name).__dict__[name] for mode,name in [('author','PubmedScraperAuthors'),('hco','PubmedScraperHCO'),('hcp_file','PubmedScraperHCP')]}
def article(pmid, domestic=True):
 authors=[{'ForeName':'Alice','LastName':'Smith','Initials':'A','AffiliationInfo':[{'Affiliation':'Department of Medicine, Example Hospital, London, UK' if domestic else 'Department of Medicine, Example Hospital, Boston, USA'}]}, {'ForeName':'Robert','LastName':'Jones','Initials':'R','AffiliationInfo':[{'Affiliation':'Other Hospital, Boston, USA'}]}]
 return dict(pmid=pmid,title='Study '+pmid,author_list=authors,author_role_list=['First','Last'],publication_types='Journal Article',nct_codes='',collaborators='Alice Smith, Robert Jones',study_group_names='Study Group',coi_statements=['',''],coi_statements_all='',year=2025,doi='',url='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/')
def fetch(self,query):
 queries.append(query)
 return copy.deepcopy([article('1')]) if '[Affiliation]' in query else copy.deepcopy([article('1'),article('2',False)])
def frames(raw):
 x=pd.ExcelFile(BytesIO(raw)); return {s:pd.read_excel(x,s).fillna('') for s in x.sheet_names}
real_writer=pd.ExcelWriter
checks=0
os.chdir(base/'validation/reference')
import tempfile
fixture_dir = tempfile.TemporaryDirectory()
for mode,fmt,full in [('author',None,False),('company',None,False),('hco',None,False),('hcp_file','csv',False),('hcp_file','xlsx',False),('hcp_file','multi',True)]:
 raw=None; path=None; sheet='Clinicians'
 if fmt:
  inp=pd.DataFrame({'Clinician\nName':['Alice Smith','Alice Smith']})
  path=Path(fixture_dir.name)/('fixture.csv' if fmt=='csv' else 'fixture.xlsx')
  if fmt=='csv': inp.to_csv(path,index=False)
  else:
   with real_writer(path) as w:
    inp.to_excel(w,sheet_name=sheet,index=False)
    if fmt=='multi': pd.DataFrame({'Other':['X']}).to_excel(w,sheet_name='Other',index=False)
  raw=path.read_bytes()
 queries=[]
 output=BytesIO()
 klass=original_classes['author' if mode=='company' else mode]
 with patch.object(original_base,'get_pubmeds',fetch),patch('time.sleep'),patch('builtins.input', side_effect=[str(path)]+([sheet] if fmt=='multi' else [])+['Clinician Name','y' if full else 'n'] if fmt else []),patch('pandas.ExcelWriter',side_effect=lambda dest,**kw:real_writer(output,**kw)):
  klass('test','UK',5).main()
 expected_queries=queries.copy(); expected=frames(output.getvalue())
 for rare in [True,False]:
  queries=[]
  with patch.object(app_base,'get_pubmeds',fetch),patch('time.sleep'):
   result=adapter.run_legacy_workflow(mode,'test','United Kingdom',5,'test@example.com','',raw,path.name if path else '',sheet,'Clinician Name',full,rare)
  assert queries==expected_queries,(mode,queries,expected_queries)
  actual=frames(result.getvalue())
  assert actual.keys()==expected.keys()
  for s in actual: pd.testing.assert_frame_equal(actual[s],expected[s])
  checks+=1
 print('PASS',mode,fmt,full)
print('Validated',checks,'workflow comparisons, including queries and all workbook sheets.')

fixture_dir.cleanup()
