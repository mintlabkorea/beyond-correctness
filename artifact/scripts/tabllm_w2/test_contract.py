"""Meaningful construction and inference checks, with no real outcomes."""
import unittest
import numpy as np
from sklearn.metrics import roc_auc_score
import common as C
from analyze import weighted_auc,category,adjudicate,weights_for
from audit import erase_labels

class ContractTests(unittest.TestCase):
    def test_empty_value_rendering(self):
        original=['- age: 42\n- count:\n- amount: 0']
        reference=['- Field 01: 42\n- Field 02:\n- Field 03: 0']
        expected=erase_labels(original,['age','count','amount'],'fixture')
        self.assertEqual(erase_labels(reference,['Field 01','Field 02','Field 03'],'fixture'),expected)
        altered=['- Field 01: 42\n- Field 02: \n- Field 03: 0']
        self.assertNotEqual(erase_labels(altered,['Field 01','Field 02','Field 03'],'fixture'),expected)
    def test_grid_and_pairing(self):
        cells=list(C.cells());self.assertEqual(len(cells),13140)
        self.assertEqual(len(set(cells)),13140)
        m=C.manifest()
        for d in C.DATASETS:
            candidates=m['datasets'][d]['candidates']
            self.assertEqual(set(candidates),set(C.REFS))
            for candidate in candidates.values():
                perm=candidate['line_to_identifier_index_zero_based']
                for f in C.FAMILIES:
                    labels=C.identifiers(f,perm)
                    self.assertEqual(len(labels),len(set(labels)))
                    self.assertEqual([int(x.split('_')[-1] if f=='R1' else x.split()[-1])-1 for x in labels],perm)

    def test_weighted_auc_ties_and_multiclass(self):
        rng=np.random.default_rng(17)
        y=np.tile(np.arange(4),5)
        probs=rng.integers(1,4,(20,4)).astype(float);probs/=probs.sum(axis=1,keepdims=True)
        weights=rng.integers(1,5,(8,20))
        actual=np.mean([weighted_auc((y==c).astype(int),probs[:,c],weights) for c in range(4)],axis=0)
        expected=[roc_auc_score(y,probs,multi_class='ovr',average='macro',sample_weight=w) for w in weights]
        np.testing.assert_allclose(actual,expected,atol=1e-14)
        # Explicit duplication and frequency weights must be identical.
        idx=np.repeat(np.arange(20),weights[0])
        self.assertAlmostEqual(actual[0],roc_auc_score(y[idx],probs[idx],multi_class='ovr',average='macro'))

    def test_shared_overlap_weights(self):
        union=list(range(6));y=np.array([0,0,0,1,1,1])
        split={'42':{'test':[0,1,3,4]},'0':{'test':[1,2,4,5]}}
        w=weights_for('bank',union,y,split,20)
        np.testing.assert_array_equal(w.sum(axis=1),6)
        np.testing.assert_array_equal(w[:,:3].sum(axis=1),3)
        self.assertTrue(all((w[:,s['test']][:,:2].sum(axis=1)>0).all() for s in split.values()))

    def test_categories_and_rules(self):
        self.assertEqual(category([-.02,.02]),'near-zero')
        self.assertEqual(category([.001,.03]),'unresolved')
        self.assertEqual(category([.021,.03]),'positive')
        self.assertEqual(category([-.04,-.021]),'negative')
        macro={f:{'category':'positive'} for f in C.FAMILIES}
        macro.update({f:{'equivalent':True} for f in ('R2-R1','R3-R1')})
        datasets={d:{'utility':{f:{'category':'positive'} for f in C.FAMILIES}} for d in C.DATASETS}
        self.assertEqual(adjudicate(macro,datasets),'A')
        macro['R2-R1']['equivalent']=False
        self.assertEqual(adjudicate(macro,datasets),'B')
        macro['R2']['category']='unresolved'
        self.assertEqual(adjudicate(macro,datasets),'C')

if __name__=='__main__': unittest.main()
