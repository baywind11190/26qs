#!/usr/bin/env python3
"""Explicit V8 functional recheck. No synthesis, build, performance run, or cache update."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE / 'runner'))
import eqy_recheck_support as W
from prepare_builtin import _build_env
from process_utils import process_group_kwargs, terminate_process_tree

TARGET_COMMIT = '17f9361099dcda757c16bb81caa18ddb52d74c4e'


def build_plan(source, requested, short_root):
    result = {'mode': 'functional_recheck', 'formal_synthesis_expected_runs': 0,
              'functional_expected_chains': 0, 'blocked': []}
    try:
        source, short_root = W.safe_root(source), W.safe_root(short_root)
        audit = W.audit_source(source)
        ctx = json.loads((source / 'validation_context.json').read_text(encoding='utf-8'))
        cases = W.select_cases(ctx['official_cases'], requested)
        if ctx['target_commit'] != TARGET_COMMIT or ctx['integration_profile'] != 'p3-local-lut':
            raise ValueError('Wrong algorithm commit or integration profile')
        if W.sha(source / '02_assets/tree/src/pmux_opt.cc') != ctx['source_sha256']:
            raise ValueError('Frozen algorithm identity mismatch')
        for name in ('yosys', 'eqy', 'abc'):
            tool = ctx['tools'][name]
            if W.sha(Path(tool['path'])) != tool['sha256']:
                raise ValueError('Frozen tool identity mismatch: ' + name)
        model = source / '03_runner/form_cells_cycloneiv.v'
        inputs = [{'source': str(model), 'sha256': W.sha(model), 'kind': 'model'}]
        for case in cases:
            rtl = source / '02_assets' / case['file']
            if W.sha(rtl) != case['sha256']:
                raise ValueError('Frozen RTL hash mismatch: ' + case['id'])
            inputs.append({'source': str(rtl), 'sha256': W.sha(rtl), 'kind': 'rtl'})
            for side, chain in [('optimized', W.CHAINS[0]), ('baseline', W.CHAINS[1])]:
                net = source / '05_public/round01' / case['id'] / side / 'post_abc.il'
                original = json.loads((source / '10_selfcheck/chains/run01' / case['id'] / chain / 'summary.json').read_text(encoding='utf-8'))
                if W.sha(net) != original['formal_netlist_sha256'] or not original['partition_states']:
                    raise ValueError('Frozen chain/netlist binding mismatch')
                inputs.append({'source': str(net), 'sha256': W.sha(net), 'kind': 'post_abc', 'case': case['id'], 'side': side})
        parent = short_root / source.name
        workspace = next((parent / ('a%02d' % n) for n in range(1, 10000)
                          if not (parent / ('a%02d' % n)).exists()), None)
        if workspace is None:
            raise ValueError('No unused short workspace attempt')
        W.safe_root(workspace)
        predicted=[]
        for case in cases:
            for side,chain in [('optimized',W.CHAINS[0]),('baseline',W.CHAINS[1])]:
                job=W.job_dir(workspace,case['id'],side)
                original=json.loads((source/'10_selfcheck/chains/run01'/case['id']/chain/'summary.json').read_text(encoding='utf-8'))
                lengths=[len(str(job/'config.eqy')),len(str(job/'setup.log'))]
                for part in original['partition_states']:
                    cwd=job/'work/strategies'/part/'simple'
                    lengths.extend(len(str(cwd)+'/../../../partitions/'+part+'.'+suffix) for suffix in ('sv','il'))
                if max(lengths)>W.LIMIT:
                    raise ValueError('Predicted EQY path budget exceeded')
                predicted.append({'case':case['id'],'side':side,'max_raw_length':max(lengths)})
        for item in inputs:
            if len(str(workspace/'inputs'/Path(item['source']).name))>W.LIMIT:
                raise ValueError('Predicted EQY input path budget exceeded')
        result.update(source_round=str(source), eqy_work_root=str(short_root), workspace=str(workspace),
                      cases=[c['id'] for c in cases], functional_expected_chains=2 * len(cases),
                      target_commit=ctx['target_commit'], integration_profile=ctx['integration_profile'],
                      path_budget=W.LIMIT, predicted_paths=predicted, inputs=inputs, source_manifest_entries=audit['manifest_entries'],
                      tools={k:ctx['tools'][k] for k in ('yosys', 'eqy', 'abc')},
                      _context=ctx, _source_audit=audit)
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        result['blocked'].append(str(exc))
    return result


def public_plan(plan):
    return {k:v for k,v in plan.items() if not k.startswith('_')}


def next_result(repo):
    parent = W.safe_root(Path(repo) / 'results/official_eval')
    prefix = datetime.now().strftime('%Y-%m-%d_%H%M') + '_eqy_pathfix_17f9361'
    for n in range(1, 10000):
        path = parent / (prefix + '_r%02d' % n)
        try:
            path.mkdir()
            return path
        except FileExistsError:
            continue
    raise ValueError('No unused result round')


def run(plan):
    source = Path(plan['source_round']); workspace = Path(plan['workspace'])
    ctx = dict(plan['_context'])
    root = next_result(ctx['repo'])
    meta = root / '01_meta'; meta.mkdir()
    (root / '10_selfcheck').mkdir()
    summary_dir = root / '11_summary'; summary_dir.mkdir()
    W.save(meta / 'plan.json', public_plan(plan))
    W.save(meta / 'source_before.json', plan['_source_audit'])
    identity = {**public_plan(plan), 'result_round': str(root), 'status': 'STARTED',
                'python': {'path': sys.executable, 'sha256': W.sha(Path(sys.executable))},
                'mapping': [{'case': c, 'side': s, 'job': str(W.job_dir(workspace, c, s))}
                            for c in plan['cases'] for s in ('optimized', 'baseline')]}
    W.create_workspace(workspace, identity)
    rows=[]; problems=[]; rc=None; interrupted=False; archive=[]; source_ok=False; path_audits={}
    try:
        shutil.copytree(PACKAGE / 'runner', root / '03_runner', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(source / '03_runner/form_cells_cycloneiv.v', root / '03_runner/form_cells_cycloneiv.v')
        shutil.copyfile(PACKAGE / 'recheck_eqy.py', meta / 'recheck_eqy.py.snapshot')
        shutil.copyfile(PACKAGE / 'PACKAGE_SHA256.json', meta / 'PACKAGE_SHA256.json')
        shutil.copyfile(source / 'POLICY.md', root / 'POLICY.md')
        for item in plan['inputs']:
            if item['kind'] == 'rtl':
                src=Path(item['source']); dst=root / src.relative_to(source)
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src,dst)
        alg = root / '02_assets/tree/src/pmux_opt.cc'; alg.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source / '02_assets/tree/src/pmux_opt.cc', alg)
        ctx.update(source_runner_sha256=ctx.get('runner_sha256'),
                   runner_sha256={p.relative_to(root/'03_runner').as_posix():W.sha(p)
                                  for p in (root/'03_runner').rglob('*') if p.is_file()},
                   source_created_at=ctx.get('created_at'),
                   mode='functional_recheck', created_at=datetime.now().isoformat(),
                   functional_recheck={'source_round':str(source), 'workspace':str(workspace),
                                       'root':plan['eqy_work_root'], 'cases':plan['cases']})
        W.save(root / 'validation_context.json', ctx)
        env = _build_env(ctx)
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
        W.save(meta / 'runtime_environment.json', {k:env.get(k) for k in
            ('PATH','MSYSTEM','LC_ALL','PYTHONUTF8','PYTHONIOENCODING','PYTHONNOUSERSITE','MSYS2_PATH_TYPE')})
        command=[sys.executable,'-X','utf8','-B',str(root/'03_runner/run_eqy_chains.py'),
                 '--input-mode','builtin','--frozen-round',str(source), '--cases',*plan['cases'],
                 '--eqy-work-root',plan['eqy_work_root']]
        W.save(meta / 'execution.json', {'command':command, 'cwd':str(root), 'launch_count':1,
                                        'formal_synthesis_runs':0})
        with (meta / 'chains.log').open('xb') as log:
            process=subprocess.Popen(command, cwd=root, env=env, stdout=log,stderr=subprocess.STDOUT,
                                     **process_group_kwargs())
            try:
                rc=process.wait()
            except KeyboardInterrupt:
                interrupted=True; terminate_process_tree(process); process.wait(); rc=130
                problems.append('INTERRUPTED; unfinished chains are NOT_RUN')
    except Exception as exc:
        problems.append(type(exc).__name__+': '+str(exc))
    finally:
        for c in plan['cases']:
            for chain in W.CHAINS:
                p=root/'10_selfcheck/chains/run01'/c/chain/'summary.json'
                row={
                    'case':c,'chain':chain,'state':'NOT_RUN','verified':False,'partitions_total':0,'partitions_pass':0}
                if p.is_file():
                    try:
                        row=json.loads(p.read_text(encoding='utf-8'))
                    except (ValueError,OSError,UnicodeError) as exc:
                        problems.append('EVIDENCE_ERROR: '+str(p)+': '+str(exc))
                        row.update(state='INCOMPLETE',evidence_error=str(exc))
                side='optimized' if chain==W.CHAINS[0] else 'baseline'
                ap=W.job_dir(workspace,c,side)/'path_audit.json'
                if ap.is_file():
                    try:
                        path_audits[c+':'+chain]=json.loads(ap.read_text(encoding='utf-8'))
                    except (ValueError,OSError,UnicodeError) as exc:
                        problems.append('EVIDENCE_ERROR: '+str(ap)+': '+str(exc))
                elif row.get('state')=='PASS':
                    problems.append('EVIDENCE_MISSING: '+str(ap))
                rows.append(row)
        identity.update(status='INTERRUPTED' if interrupted else 'FINISHED', process_rc=rc, problems=problems)
        try:
            W.save(workspace / 'workspace_manifest.json', identity)
            archive=W.archive_tree(workspace, root/'10_selfcheck/eqy_archive')
            W.save(summary_dir/'archive_manifest.json', archive)
            diag_parent=workspace.parent
            for name in ('diagnostics','diagnostics_env01'):
                if (diag_parent/name).is_dir():
                    W.save(meta/(name+'_archive_manifest.json'),W.archive_tree(diag_parent/name,meta/name))
        except Exception as exc:
            problems.append('ARCHIVE_ERROR: '+str(exc))
        try:
            after=W.audit_source(source)
            source_ok=after==plan['_source_audit']
            W.save(meta/'source_after.json',after)
            if not source_ok:
                problems.append('SOURCE_ROUND_CHANGED')
        except Exception as exc:
            problems.append('SOURCE_AUDIT_ERROR: '+str(exc))
        passed=rc==0 and not problems and source_ok and bool(archive) and W.complete(rows,plan['cases'])
        result={'scope':'functional_recheck_only','source_round':str(source),'workspace':str(workspace),
                'functional_verdict':'PASS' if passed else 'NEEDS_REVIEW','chains':rows,
                'formal_synthesis_runs':0,'performance':'NOT_RUN','delivery':'NOT_RUN',
                'official_recognition':'NOT_CLAIMED','source_unchanged':source_ok,'problems':problems,
                'process_rc':rc,'archive_verified':bool(archive),'path_audits':path_audits}
        W.save(summary_dir/'recheck_summary.json',result)
        write_report(root,plan,result)
        all_files=W.inventory(root)
        (summary_dir/'ALL_SHA256.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in sorted(all_files.items())),encoding='utf-8')
    print(json.dumps({'result_round':str(root),'functional_verdict':result['functional_verdict'],
                      'process_rc':rc,'source_unchanged':source_ok,'problems':problems},ensure_ascii=False))
    return 0 if passed else 2


def write_report(root,plan,result):
    workspace=Path(plan['workspace'])
    diagnostic=root/'01_meta/diagnostics_env01/diagnostics.json'
    d=json.loads(diagnostic.read_text(encoding='utf-8')) if diagnostic.is_file() else {}
    lines=['# V8 六条 EQY 功能证明专项复核','',
           '本轮范围：三例、两侧共六条功能证明链；新增正式综合次数为0，时间和内存评测为NOT_RUN。',
           '', '**功能专项结论：'+result['functional_verdict']+'**', '',
           '原轮次：`'+plan['source_round']+'`。原九例失败报告及其原判定完整保留；本轮不改变原九例整体结论。',
           '算法提交：`'+plan['target_commit']+'`；集成方式：`p3-local-lut`；执行现场：`'+str(workspace)+'`。', '',
           '## 根因实验','',
           '受控读取实验确认路径因素：'+str(d.get('path_cause_confirmed',False))+'。相同工具和文件字节、相同相对读取命令，仅改变工作位置。',
           '首组诊断未加载完整工具DLL环境，进程未正常启动，单独归档且不参与根因判定；diagnostics_env01为有效对照。',
           '', '## 六条链结果与路径长度','',
           '| 用例 | 侧别 | 分区通过/总数 | 功能结果 | 原最长拼接长度 | 新最长拼接长度 |',
           '|---|---|---:|---|---:|---:|']
    for row in result['chains']:
        c=row['case']; chain=row['chain']; side='optimized' if chain==W.CHAINS[0] else 'baseline'
        old=[x for x in d.get('inventory',[]) if x['case']==c and x['chain']==chain]
        old_max=max((v['raw_length'] for x in old for v in x['references']),default=0)
        new=result['path_audits'].get(c+':'+chain,{})
        lines.append('| '+c+' | '+side+' | '+str(row['partitions_pass'])+'/'+str(row['partitions_total'])+' | '+row['state']+' | '+str(old_max)+' | '+str(new.get('max_raw_length','NOT_RUN'))+' |')
        unclosed={p:s for p,s in row.get('partition_states',{}).items() if s!='PASS'}
        if unclosed:
            lines.append('')
            lines.append('未闭合分区：`'+json.dumps(unclosed,ensure_ascii=False)+'`。')
    lines += ['', '## 完整性与实现边界','',
              '原轮次逐文件复核未改变：'+str(result['source_unchanged'])+'；执行现场归档校验：'+str(result['archive_verified'])+'。',
              '通过正规eqy -d指定受管理短工作区；保留noDF-local-r1、模型dffeas-v3、depth 5、证明600秒、探针120秒及原并发设置。',
              '专项入口recheck_eqy.py与共用运行器显式复用冻结RTL、模型及六份post_abc.il，运行前核对原ALL_SHA256、工具身份与原分区集合；路径预算200字符。',
              '只完善新结果的工具错误/前提状态归类；原始报告、脚本快照及哈希清单未改。正式V8 run默认工作路径保持现状。',
              '未执行综合、构建、算法优化、性能复测、交付验收、注册表修改或Git提交/推送。',
              '', '## 后续正式接入的最小修改方案','',
              '六链全部有效PASS、无未闭合分区且归档完整时，专项路径修复具备接入条件；九例完整正式流程尚未验证该路径模式。',
              '后续单独实施：配置增加显式eqy_work_root；plan核对根路径和预计长度；run冻结轮次/用例/侧别映射并用正规-d；work与merged统一走短根；失败/超时/中断均原位保留并核验归档。',
              '同步POLICY路径条款、工程协作约定、说明、包清单及缓存指纹；性能计量、资源门槛、证明假设和深度保持原口径。',
              '增加正式九例集合、test3合并证明及中断归档测试；经另行授权再正式集成与运行。现阶段不修改正式默认配置或POLICY。',
              '', '问题：`'+json.dumps(result['problems'],ensure_ascii=False)+'`。', '']
    (root/'00_report.md').write_text('\n'.join(lines),encoding='utf-8')


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=('plan','run'))
    ap.add_argument('source_round',type=Path)
    ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--eqy-work-root',type=Path,required=True)
    args=ap.parse_args(argv)
    plan=build_plan(args.source_round,args.cases,args.eqy_work_root)
    try:
        from validate import verify_package_manifest
        verify_package_manifest(PACKAGE)
    except (ValueError,OSError) as exc:
        plan['blocked'].append(str(exc))
    if args.mode=='plan' or plan['blocked']:
        print(json.dumps(public_plan(plan),ensure_ascii=False,indent=2))
        return 2 if plan['blocked'] else 0
    return run(plan)


if __name__=='__main__':
    raise SystemExit(main())
