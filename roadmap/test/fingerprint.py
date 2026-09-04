import json,re,hashlib
s=open('index.html').read()
i=s.index('const PLAN=['); j=s.index('\nconst ALLDAYS')
plan=s[i:j]
hdrs=[(m.start(),m.group(1)) for m in re.finditer(r'\{n:(\d+),ph:\d+,th:"[^"]*"',plan)]
pat=r'D\("\w+",\d+,"((?:[^"\\]|\\.)*)","((?:[^"\\]|\\.)*)","((?:[^"\\]|\\.)*)","(?:[^"\\]|\\.)*"\)'
fp={}
for k,(pos,n) in enumerate(hdrs):
    end=hdrs[k+1][0] if k+1<len(hdrs) else len(plan)
    for idx,m in enumerate(re.findall(pat,plan[pos:end])):
        t,d,o=[json.loads('"'+x+'"') for x in m]
        fp["%s-%d"%(n,idx)]={"t":t,"h":hashlib.sha256((t+" "+d+" "+o).encode()).hexdigest()[:16]}
bs=s.index('const STEPS={'); be=s.index('\n};',bs)
keys=re.findall(r'^"(\d+-\d+)":\{t:',s[bs:be],re.M)
json.dump({k:fp[k] for k in keys},open('test/steps-fingerprints.json','w'),indent=1,ensure_ascii=False)
print("fingerprinted",len(keys))
