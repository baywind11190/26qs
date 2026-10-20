"""Integer CPU accounting; nested observations never enter the partition sum."""
import math

MAIN_MARKS=('main_entry','design_read_end','fsm_opt_end','pmux_begin','pmux_end','abc9_begin','abc9_end','final')
STAGE_NAMES=('启动及读取','前段综合至fsm_opt结束','计量边界间隔','PMUX槽位','ABC前准备','ABC9整体','综合剩余及输出收尾')
METHOD='windows-cpu-stage-diagnostic-v1'

def schedule():
    for pair in range(1,6):
        sides=('baseline','optimized') if pair%2 else ('optimized','baseline')
        for case in ('test1','test2','test3','test4'):
            for side in sides:yield pair,case,side

def total(mark,prefix):
    vals=[mark.get(prefix+'_user'),mark.get(prefix+'_kernel')]
    if not all(type(v) is int and v>=0 for v in vals):raise ValueError('invalid CPU counter')
    return sum(vals)

def partition(marks):
    primary=[]
    for label in MAIN_MARKS:
        matching=[m for m in marks if m.get('label')==label]
        if len(matching)!=1:raise ValueError('missing/duplicate checkpoint: '+label)
        primary.append(matching[0])
    if [m['label'] for m in marks if m['label'] in MAIN_MARKS]!=list(MAIN_MARKS):raise ValueError('stage order mismatch')
    result=[]
    for name,left,right in zip(STAGE_NAMES,primary,primary[1:]):
        root=total(right,'root')-total(left,'root');job=total(right,'job')-total(left,'job')
        if root<0 or job<0:raise ValueError('nonmonotonic CPU checkpoints')
        result.append(dict(stage=name,begin=left['label'],end=right['label'],root_ticks=root,job_ticks=job,
                           job_minus_root_delta_ticks=job-root))
    return result

def validate(data,native):
    if data.get('schema')!=1 or data.get('method')!=METHOD or data.get('valid') is not True or data.get('error')!=0:
        raise ValueError('diagnostic method/status invalid')
    if data.get('pid')!=native.get('main_pid') or data.get('created')!=native.get('process_create_filetime'):
        raise ValueError('root PID/creation identity mismatch')
    marks=data.get('marks') or [];stages=partition(marks)
    last={'root':0,'job':0}
    for m in marks:
        for prefix in last:
            now=total(m,prefix)
            if now<last[prefix]:raise ValueError('nonmonotonic raw snapshot')
            last[prefix]=now
    records=data.get('abc') or []
    if not records:raise ValueError('no ABC CPU records')
    identities=set()
    for index,r in enumerate(records,1):
        if r.get('call_id')!=index or r.get('ready')!=2 or r.get('exit_code')!=0 or r.get('launcher_exit')!=0:
            raise ValueError('ABC record incomplete')
        if not r.get('pid') or not r.get('created') or (r['pid'],r['created']) in identities:
            raise ValueError('ABC process identity invalid/duplicated')
        identities.add((r['pid'],r['created']))
        for prefix in ('start','end'):total(r,prefix)
        if total(r,'end')<total(r,'start'):raise ValueError('ABC CPU nonmonotonic')
        begin=[m for m in marks if m['label']=='abc_call_begin' and m['call_id']==index]
        end=[m for m in marks if m['label']=='abc_call_end' and m['call_id']==index]
        if len(begin)!=1 or len(end)!=1 or marks.index(begin[0])>=marks.index(end[0]):raise ValueError('ABC call boundaries invalid')
    if len([m for m in marks if m['label']=='abc_call_begin'])!=len(records):raise ValueError('ABC call count mismatch')
    first=marks[0];final=next(m for m in marks if m['label']=='final')
    if sum(s['root_ticks'] for s in stages)!=total(final,'root')-total(first,'root'):raise ValueError('root partition sum mismatch')
    if sum(s['job_ticks'] for s in stages)!=total(final,'job')-total(first,'job'):raise ValueError('job partition sum mismatch')
    abc=sum(total(r,'end') for r in records)
    abc_entry=sum(total(r,'start') for r in records)
    exited_root=native.get('root_cpu_user_ticks',0)+native.get('root_cpu_kernel_ticks',0)
    return dict(stages=stages,pre_main_root_ticks=total(first,'root'),abc_process_ticks=abc,
        abc_pre_entry_ticks=abc_entry,abc_main_body_ticks=abc-abc_entry,
        root_final_ticks=total(final,'root'),job_final_ticks=total(final,'job'),
        root_after_exit_ticks=exited_root,root_exit_tail_ticks=exited_root-total(final,'root'),
        outer_job_ticks=native['cpu_total_ticks'],inner_processes=final['processes'],outer_processes=native['job_total_processes'],
        outer_minus_inner_ticks=native['cpu_total_ticks']-total(final,'job'),
        inner_minus_root_abc_ticks=total(final,'job')-total(final,'root')-abc)

def observed_quantum(rows):
    values=[]
    for row in rows:
        for m in row['diagnostic']['marks']:
            values.extend(m[k] for k in ('root_user','root_kernel','job_user','job_kernel') if m[k]>0)
        for r in row['diagnostic']['abc']:
            values.extend(r[k] for k in ('start_user','start_kernel','end_user','end_kernel') if r[k]>0)
    return math.gcd(*values) if values else None

def directional_clue(values,base,opt,quantum):
    pos=sum(v>0 for v in values);neg=sum(v<0 for v in values);zero=len(values)-pos-neg
    small=quantum is not None and max(abs(v) for v in values)<=quantum
    overlap=max(min(base),min(opt))<=min(max(base),max(opt))
    clue=max(pos,neg)>=4 and not small and zero<3
    return dict(clue=clue,direction='增加' if pos>=4 else '减少' if neg>=4 else None,
                overlap=overlap,confirmed=False,positive=pos,negative=neg,zero=zero,small=small)
