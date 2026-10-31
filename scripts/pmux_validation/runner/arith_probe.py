"""Non-scoring arithmetic integration probes and immutable evidence verification."""
import hashlib
import json
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def freeze_probe(probe, root):
    import copy, shutil
    errors=verify_probe(probe)
    if errors: raise ValueError('; '.join(errors))
    frozen=copy.deepcopy(probe)
    for name,row in frozen['cases'].items():
        dest=Path(root)/'01_meta'/'arith_probe'/name; dest.mkdir(parents=True)
        for file,spec in row['files'].items():
            shutil.copyfile(spec['path'],dest/file)
            spec['path']=str(dest/file)
    if verify_probe(frozen): raise ValueError('Frozen arithmetic probe mismatch')
    return frozen

def verify_probe(probe, binary_sha256=None):
    if not isinstance(probe, dict) or probe.get('ok') is not True:
        return ['arithmetic probe missing or failed']
    errors=[]
    if not probe.get('binary_sha256') or (binary_sha256 and probe['binary_sha256'] != binary_sha256):
        errors.append('arithmetic probe binary identity mismatch')
    for name, expected in (('shareable',1),('observed',0)):
        row=(probe.get('cases') or {}).get(name,{})
        if row.get('shares') != expected or row.get('equivalence') != 'PASS':
            errors.append('arithmetic probe result mismatch: '+name)
        files=row.get('files') or {}
        if set(files) != {'fixture.v','probe.ys','before.json','after.json','after.il','probe.log'}:
            errors.append('arithmetic probe files incomplete: '+name)
        for file,spec in files.items():
            try:
                if sha(spec['path']) != spec['sha256']: raise ValueError(file)
            except (OSError,KeyError,ValueError): errors.append('arithmetic probe evidence mismatch: '+name+'/'+file)
        try:
            def counts(file):
                data=json.loads(Path(files[file]['path']).read_text())
                return (data.get('design') or data['modules']['\\top'])['num_cells_by_type']
            before,after=counts('before.json'),counts('after.json')
            log=Path(files['probe.log']['path']).read_text(errors='replace')
            if (log.count('ARITH_SHARE total=%d all=1'%expected)!=1 or 'Equivalence successfully proven!' not in log or 'ERROR:' in log
                or (expected and (before.get('$add',0)+before.get('$sub',0)!=2 or after.get('$add',0)+after.get('$sub',0)!=0 or after.get('$alu',0)!=1))
                or (not expected and before!=after)):
                raise ValueError('probe semantic mismatch')
        except (OSError,KeyError,ValueError,TypeError): errors.append('arithmetic raw evidence invalid: '+name)
    return errors

def run_probe(build_dir,binary,cfg,run_logged,build_env):
    result={'ok':False,'binary_sha256':sha(binary),'cases':{}}
    for name,observed,expected in (('shareable',False,1),('observed',True,0)):
        folder=Path(build_dir)/'smoke'/('arith-'+name);folder.mkdir()
        rtl='''module top(input [1:0] sel, input [3:0] a,b,c,d, output reg [3:0] y%s);
wire [3:0] add_result=a+b; wire [3:0] sub_result=c-d;
always @* case(sel) 0:y=add_result; 1:y=sub_result; default:y=0; endcase
%s
endmodule
''' % (', output [3:0] observe' if observed else '', 'assign observe=add_result;' if observed else '')
        (folder/'fixture.v').write_text(rtl)
        (folder/'probe.ys').write_text('''read_verilog fixture.v
hierarchy -top top
proc
opt
design -save gold
tee -o before.json stat -json
pmux_opt -arith
tee -o after.json stat -json
write_rtlil after.il
design -save gate
design -reset
design -copy-from gold -as gold top
design -copy-from gate -as gate top
equiv_make gold gate equiv
prep -top equiv
equiv_simple
equiv_status -assert
''')
        rc=run_logged([str(binary),'-s','probe.ys'],cwd=folder,log=folder/'probe.log',timeout=60,env=build_env(cfg,[str(Path(binary).parent)]))
        text=(folder/'probe.log').read_text(errors='replace')
        def counts(file):
            data=json.loads((folder/file).read_text());return (data.get('design') or data['modules']['\\top'])['num_cells_by_type']
        before,after=counts('before.json'),counts('after.json')
        if (rc or text.count('ARITH_SHARE total=%d all=1'%expected)!=1
            or 'Equivalence successfully proven!' not in text
            or (expected and (before.get('$add',0)+before.get('$sub',0)!=2 or after.get('$add',0)+after.get('$sub',0)!=0 or after.get('$alu',0)!=1))
            or (not expected and before!=after)):
            raise RuntimeError('Arithmetic probe failed: '+str(folder))
        result['cases'][name]=dict(shares=expected,equivalence='PASS',files={f:dict(path=str(folder/f),sha256=sha(folder/f)) for f in ('fixture.v','probe.ys','before.json','after.json','after.il','probe.log')})
    result['ok']=True
    errors=verify_probe(result,sha(binary))
    if errors: raise RuntimeError('; '.join(errors))
    return result
