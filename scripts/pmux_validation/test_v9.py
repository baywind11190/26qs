"""V9 contract tests: real scheduling/judgment; native process boundary is injected."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
try:
    import measure_v9 as V
except ImportError:
    V = None
from test_measure_v8 import raw


def sample(side='baseline', ticks=2_000_000, peak=100_000_000):
    r = raw(side, ticks, peak)
    r.update(measurement_revision=V.H.REVISION,heap_policy=V.H.POLICY,debug_heap_env='1',heap_observation=dict(pid=r['main_pid'],layout='win64-ntheap-v1',verified=True,heap_signature=0xffeeffee,ntglobal_flags=0,heap_flags=2,heap_force_flags=0))
    r['performance_scheme'] = V.SCHEME
    return r


def case_spec(name):
    return dict(id=name,top='test1',file=f'tree/{name}.v',canonical_file=f'cases/{name}.v',
                sha256='a'*64,canonical_sha256='a'*64,default_parameters={})


class V9Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(V, 'V9 is not implemented')

    def summary(self, base=2_000_000, opt=2_200_000, reviews=None):
        return dict(case='test1', performance_scheme=V.SCHEME, same_run_policy=V.POLICY,
                    execution_complete=True, samples=[sample(ticks=base), sample('optimized', opt)],
                    recheck_samples=reviews or [], recheck_complete=reviews is not None)

    def reviews(self, bt=None, ot=None):
        result = []
        for n, (b, o) in enumerate(zip(bt or [100]*5, ot or [105]*5), 1):
            for side, ticks in [('baseline', b), ('optimized', o)]:
                r = sample(side, ticks, 999_000_000)
                r.update(sample_id=f'r{n}-{side}', phase='recheck', repetition=n,
                         repeat_evidence_ok=True)
                result.append(r)
        return result

    def test_schedule_warmup_and_side_major_initial(self):
        ctx = {'official_cases': [case_spec('a'),case_spec('b')]}
        warm = V.schedule(ctx, 'warmup')
        self.assertEqual([(r['case'], r['side'], r['repetition']) for r in warm],
                         [(c, 'baseline', n) for c in ['a','b'] for n in range(1,11)])
        self.assertEqual([(r['case'], r['side']) for r in V.schedule(ctx, 'initial')],
                         [('a','baseline'),('b','baseline'),('a','optimized'),('b','optimized')])
        self.assertEqual([(r['side'], r['repetition']) for r in V.schedule(ctx, 'recheck', ['b'])],
                         [(s,n) for n in range(1,6) for s in ('baseline','optimized')])

    def test_trigger_integer_boundaries_and_scope(self):
        for b,o,want,scope in [(100,105,False,None),(100,106,True,'OFFICIAL_UNDER_1S'),
                (10_000_000,10_600_000,True,'OFFICIAL_1_TO_10S'),
                (99_999_999,106_000_000,True,'OFFICIAL_1_TO_10S'),
                (100_000_000,106_000_000,False,None)]:
            r=V.recheck_decision(b,o)
            self.assertEqual((r['required'],r['scope']),(want,scope))

    def test_average_of_times_not_average_of_ratios_and_first_excluded(self):
        reviews=self.reviews([100,100,100,100,1000],[120,120,120,120,900])
        j=V.evaluate_summary(self.summary(opt=4_000_000,reviews=reviews))
        self.assertTrue(j['valid'])
        self.assertEqual(j['initial_wall_5pct'],'FAIL')
        self.assertEqual(j['wall_5pct'],'PASS')
        self.assertEqual(j['wall_base_ms'],280/10000)
        self.assertEqual(j['wall_opt_ms'],276/10000)
        self.assertEqual(j['base_memory_bytes'],100_000_000)
        self.assertTrue(j['mem_ok'])

    def test_recheck_does_not_rescue_first_memory_failure(self):
        summ=self.summary(reviews=self.reviews())
        summ['samples'][1]['yosys_peak_working_set_bytes']=106_000_000
        j=V.evaluate_summary(summ)
        self.assertEqual(j['wall_5pct'],'PASS')
        self.assertFalse(j['mem_ok']); self.assertFalse(j['pass'])

    def test_failed_recheck_preserves_valid_initial_memory_and_trigger(self):
        summ=self.summary()
        summ['execution_complete']=False
        j=V.evaluate_summary(summ)
        self.assertEqual(j['initial_wall_base_ticks'],2_000_000)
        self.assertEqual(j['initial_wall_opt_ticks'],2_200_000)
        self.assertEqual(j['base_memory_bytes'],100_000_000)
        self.assertTrue(j['memory_valid']);self.assertTrue(j['recheck_required'])
        self.assertEqual(j['time_decision_source'],'RECHECK_INCOMPLETE')
        self.assertFalse(j['pass'])
        self.assertIsNone(j['wall_base_ms'])
        summ['samples'][1]['yosys_peak_working_set_bytes']=116_000_000
        self.assertTrue(V.evaluate_summary(summ)['any_over_15pct'])

    def test_missing_duplicate_wrong_order_and_changed_evidence_invalid(self):
        for mutate in [lambda r:r.pop(),lambda r:r.__setitem__(1,r[0]),
                       lambda r:r.reverse(),lambda r:r[0].update(repeat_evidence_ok=False)]:
            reviews=self.reviews();mutate(reviews)
            j=V.evaluate_summary(self.summary(reviews=reviews))
            self.assertFalse(j['valid']);self.assertFalse(j['pass'])
        self.assertFalse(V.evaluate_summary(self.summary())['valid'])

    def test_no_trigger_no_extra_samples_and_old_scheme_rejected(self):
        summ=self.summary(opt=2_100_000)
        self.assertTrue(V.evaluate_summary(summ)['pass'])
        summ['recheck_samples']=self.reviews()
        self.assertFalse(V.evaluate_summary(summ)['valid'])
        self.assertTrue(V.sample_errors(raw()))

    def test_dff_is_informational_other_resource_gates_remain(self):
        import builtin_common as B
        b=dict(logic_units=10,dff_count=1,io_ports=2,io_bits=2,other_cell_types={})
        o=dict(b,dff_count=2)
        self.assertTrue(B.compare_resource_counts(b,o,allow_dff_increase=True)['resource_checks_ok'])
        self.assertFalse(B.compare_resource_counts(b,dict(o,logic_units=11),allow_dff_increase=True)['resource_checks_ok'])
        self.assertFalse(B.compare_resource_counts(b,dict(o,io_bits=3),allow_dff_increase=True)['resource_checks_ok'])

    def invoke(self, root, *, trigger=True, fail_at=None, change_at=None, cases=2, old_scheme_at=None, dependency_change_at=None):
        ps=root/'ps.exe';ps.write_bytes(b'ps')
        bins={s:root/(s+'.exe') for s in ['baseline','optimized']}
        for p in bins.values():p.write_bytes(b'tool')
        abcs={s:root/(s+'-abc.exe') for s in bins}
        for p in abcs.values():p.write_bytes(b'abc')
        share=root/'share/yosys';(share/'intel/cycloneiv').mkdir(parents=True)
        (share/'intel/cycloneiv/cells_map.v').write_text('fixture map')
        (share/'abc9_map.v').write_text('fixture abc data')
        rtl=root/'input.v';rtl.write_text('module test1; endmodule')
        specs=[case_spec(f'case{n}') for n in range(cases)]
        ctx=dict(mode='builtin',performance_scheme=V.SCHEME,same_run_policy=V.POLICY,
                 official_cases=specs,wall_time_tool={'path':str(ps)},builtin={s:{'binary_sha256':V.sha(p)} for s,p in bins.items()})
        ctx['builtin']['abc']={s:str(p) for s,p in abcs.items()}
        ctx['tool_data_fourcase_filter']={'direct_share_files':['abc9_map.v']}
        calls=[]
        def native(command,*,cwd,**kw):
            cwd=Path(cwd);calls.append(cwd)
            for name in ['post_abc.il','mapped.il']:
                (cwd/name).write_text('module \\test1\nend\n'+('changed' if len(calls)==change_at else ''))
            for name in ['stat.json','post_abc_stat.json']:
                (cwd/name).write_text(json.dumps({'design':{'num_cells':1,'num_cells_by_type':{'cycloneiv_lcell_comb':1}}}))
            (cwd/'run.log').write_text('fixture log')
            side=Path(command[0]).stem
            ticks=2_200_000 if trigger and side=='optimized' and '05_public' in cwd.parts else 2_000_000
            r=sample(side,ticks);r.update(powershell_path=str(ps),powershell_sha256=V.sha(ps))
            if len(calls)==fail_at:r.update(rc=1)
            if len(calls)==old_scheme_at:r['performance_scheme']='old-v8'
            if len(calls)==dependency_change_at:abcs[side].write_bytes(b'changed abc')
            V.save(cwd/'measure_result.raw.json',r)
            V.save(cwd/'combined_request.json',dict(command=command,cwd=str(cwd),log_path=str(cwd/'run.log'),
                 performance_scheme=V.SCHEME,measurement_revision=V.H.REVISION,heap_policy=V.H.POLICY,method=V.METHOD,result_path=str(cwd/'measure_result.raw.json')))
            V.save(cwd/'worker_response.json',dict(ok=True,metrics=dict(r)))
            return r
        flow=f'read_verilog -sv {rtl}\n'
        rc=V.run(ctx,root,bins,{c['id']:flow for c in specs},execute=native)
        ledger=json.loads((root/'09_performance/round01/synthesis_ledger.json').read_text())
        return rc,calls,ledger,ctx

    def test_run_exact_count_and_evidence_recheck_no_trigger(self):
        for trigger,count in [(False,24),(True,44)]:
            with self.subTest(trigger=trigger),tempfile.TemporaryDirectory() as tmp:
                rc,calls,ledger,ctx=self.invoke(Path(tmp),trigger=trigger)
                self.assertEqual(rc,0);self.assertEqual(len(calls),count)
                self.assertEqual(ledger['total_public_completed_runs'],count)
                self.assertTrue(V.verify_run_evidence(Path(tmp),ctx)['ok'])
                first=Path(tmp)/'05_public/round01/case0/baseline/mapped.il'
                first.write_text('tampered')
                self.assertFalse(V.verify_run_evidence(Path(tmp),ctx)['ok'])

    def test_invalid_sample_or_changed_recheck_stops_without_replacement(self):
        for args,want in [({'fail_at':3},3),({'change_at':25},25),({'old_scheme_at':2},2),({'dependency_change_at':25},25)]:
            with self.subTest(args=args),tempfile.TemporaryDirectory() as tmp:
                rc,calls,ledger,ctx=self.invoke(Path(tmp),**args)
                self.assertEqual(rc,1);self.assertEqual(len(calls),want)
                self.assertFalse(ledger['execution_complete'])
                if want==25:
                    summ=json.loads((Path(tmp)/'09_performance/round01/performance_summary.json').read_text())[0]
                    j=V.evaluate_summary(summ)
                    self.assertTrue(j['memory_valid']);self.assertEqual(j['base_memory_bytes'],100_000_000)
                    self.assertTrue(j['recheck_required']);self.assertEqual(j['time_decision_source'],'RECHECK_INCOMPLETE')

    def test_final_fifteen_boundary_and_large_case_no_recheck(self):
        j=V.evaluate_summary(self.summary(reviews=self.reviews(ot=[115]*5)))
        self.assertEqual((j['wall_5pct'],j['wall_15pct']),('FAIL','PASS'))
        j=V.evaluate_summary(self.summary(base=100_000_000,opt=116_000_000))
        self.assertTrue(j['valid']);self.assertFalse(j['recheck_required'])
        self.assertEqual(j['wall_15pct'],'FAIL')

    def test_report_preserves_initial_and_reviews_without_claiming_missing_proof(self):
        import report_v9
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rc,calls,ledger,ctx=self.invoke(root,cases=1)
            ctx['policy_source']={'path':'POLICY.md'}
            (root/'validation_context.json').write_text(json.dumps(ctx),encoding='utf-8')
            self.assertEqual(report_v9.build_report(root),'NEEDS_REVIEW')
            manifest=json.loads((root/'11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertTrue(manifest['measurement_evidence']['ok'])
            self.assertEqual(manifest['public_runs_total'],22)
            self.assertEqual(manifest['category_status']['formal'],'NOT_RUN')
            self.assertEqual(manifest['performance'][0]['initial_wall_5pct'],'FAIL')
            self.assertEqual(manifest['performance'][0]['wall_5pct'],'PASS')
            self.assertEqual(len(json.loads((root/'11_summary/recheck_samples.json').read_text())),10)
            ctx['performance_scheme']='pmux-perf-single-powershell-same-run-exitpeak-v8'
            (root/'validation_context.json').write_text(json.dumps(ctx),encoding='utf-8')
            with self.assertRaises(ValueError):report_v9.build_report(root)

    def test_all_nine_trigger_and_unique_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc,calls,ledger,ctx=self.invoke(Path(tmp),cases=9)
            self.assertEqual((rc,len(calls)),(0,198))
            self.assertEqual(len(set(calls)),198)
            self.assertTrue(V.verify_run_evidence(Path(tmp),ctx)['ok'])

    def test_native_files_are_bound_and_compared_to_derived_metrics(self):
        for name in ('measure_result.raw.json','combined_request.json','worker_response.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);rc,calls,ledger,ctx=self.invoke(root,cases=1)
                path=root/'05_public/round01/case0/baseline'/name
                data=json.loads(path.read_text())
                data['time_span_ticks']=999
                path.write_text(json.dumps(data))
                self.assertFalse(V.verify_run_evidence(root,ctx)['ok'])

    def test_abc_dependency_identity_is_in_each_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rc,calls,ledger,ctx=self.invoke(root,cases=1)
            first=json.loads((root/'05_public/round01/case0/baseline/measure_result.json').read_text())
            self.assertIn('tool_dependencies',first)
            self.assertIn('abc',first['tool_dependencies'])
            self.assertIn('abc9_map.v',first['tool_dependencies']['data'])


    def test_worker_heap_fields_cannot_be_omitted_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rc,calls,ledger,ctx=self.invoke(root,cases=1,trigger=False)
            self.assertEqual(rc,0)
            folder=root/'05_public/round01/case0/baseline'
            row=json.loads((folder/'measure_result.json').read_text())
            original=json.loads((folder/'worker_response.json').read_text())
            for key in ('measurement_revision','heap_policy','debug_heap_env','heap_observation'):
                response=copy.deepcopy(original);response['metrics'].pop(key)
                V.save(folder/'worker_response.json',response)
                altered=copy.deepcopy(row);altered['native_evidence']['worker_response.json']=V.sha(folder/'worker_response.json')
                self.assertTrue(V.native_errors(folder,altered),key)

if __name__=='__main__':unittest.main()
