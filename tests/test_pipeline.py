import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from fraudshield.api import create_app
from fraudshield.features import RAW_FEATURES, make_features, make_preprocessor
from fraudshield.scoring import Scorer, apply_policy
from fraudshield.train import split_time, choose_threshold

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT/'artifacts'

def test_split_keeps_timestamp_ties_together():
    data=pd.DataFrame({'TransactionDT':np.repeat(np.arange(100),2),
                       'isFraud':np.tile([0,1],100)})
    parts,_=split_time(data)
    assert sum(map(len,parts))==len(data)
    assert parts[0].TransactionDT.max()<parts[1].TransactionDT.min()
    assert parts[1].TransactionDT.max()<parts[2].TransactionDT.min()

def test_label_and_id_cannot_be_model_inputs():
    assert 'TransactionID' not in RAW_FEATURES
    assert 'isFraud' not in RAW_FEATURES
    f=make_features(pd.DataFrame([{'TransactionAmt':10,'TransactionDT':100,
        'ProductCD':'W','isFraud':1,'TransactionID':42}]))
    assert 'isFraud' not in f and 'TransactionID' not in f

def test_category_normalization_matches_json_roundtrip():
    a=make_features(pd.DataFrame([{'card1':1234.0,'TransactionAmt':10,'TransactionDT':100}]))
    b=make_features(pd.DataFrame([{'card1':1234,'TransactionAmt':10,'TransactionDT':100}]))
    pd.testing.assert_frame_equal(a,b)

def test_preprocessing_handles_missing_identity_and_unseen_categories():
    prep=make_preprocessor()
    raw=pd.DataFrame([{'TransactionAmt':10,'TransactionDT':10,'ProductCD':'W'},
                      {'TransactionAmt':20,'TransactionDT':20,'ProductCD':'C'}])
    prep.fit(make_features(raw))
    unseen=pd.DataFrame([{'TransactionAmt':15,'TransactionDT':30,'DeviceInfo':'NEW_DEVICE'}])
    out=prep.transform(make_features(unseen))
    dense=out.toarray() if hasattr(out,'toarray') else out
    assert np.isfinite(dense).all()

def test_threshold_uses_budget():
    y=np.array([0]*90+[1]*10)
    score=np.arange(100)/100
    t,info=choose_threshold(y,score)
    assert (score>=t).mean()<=.10
    assert info['validation_recall']==1

@pytest.mark.parametrize('score,action',[(.1,'allow'),(.2,'warn'),(.4,'pause'),(.8,'hold')])
def test_policy_boundaries(score,action):
    assert apply_policy(score,{'warn':.2,'pause':.4,'hold':.8})[0]==action

@pytest.fixture
def sample():
    return json.loads((ARTIFACTS/'sample_fraud.json').read_text())

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('FRAUDSHIELD_API_KEY','test-only-credential-1234567890')
    with TestClient(create_app(ARTIFACTS)) as c:
        yield c

AUTH={'Authorization':'Bearer test-only-credential-1234567890'}

def test_api_requires_auth(client,sample):
    assert client.post('/v1/score',json=sample).status_code==401
    assert client.post('/v1/score',json=sample,headers={'Authorization':'Bearer wrong'}).status_code==401

def test_repeated_predictions_and_explanation_reconcile(client,sample):
    a=client.post('/v1/score',json=sample,headers=AUTH)
    assert a.status_code==200,a.text
    b=client.post('/v1/score',json=sample,headers=AUTH).json()
    a=a.json()
    assert a['model_score']==b['model_score']
    assert a['model_factors']==b['model_factors']
    e=a['explanation']
    assert abs(e['base_margin']+e['all_feature_contributions_sum']-e['model_margin'])<1e-4
    assert np.isclose(1/(1+np.exp(-e['model_margin'])),a['model_score'],atol=1e-6)

@pytest.mark.parametrize('feature,value',[('isFraud',1),('TransactionID',1),('fake_column',2),
    ('TransactionAmt',-1),('TransactionAmt','100'),('TransactionAmt',True),
    ('DeviceInfo',{}),('ProductCD','UNKNOWN'),('TransactionAmt',1e300)])
def test_api_rejects_bad_or_forbidden_features(client,sample,feature,value):
    sample['features'][feature]=value
    assert client.post('/v1/score',json=sample,headers=AUTH).status_code==422

def test_missing_identity_works(client,sample):
    sample['features'].pop('DeviceInfo',None)
    sample['features'].pop('DeviceType',None)
    response=client.post('/v1/score',json=sample,headers=AUTH)
    assert response.status_code==200,response.text
    assert 'DeviceInfo' in response.json()['missing_features']

def test_missing_required_rejected(client,sample):
    del sample['features']['TransactionAmt']
    assert client.post('/v1/score',json=sample,headers=AUTH).status_code==422

def test_no_secret_startup(monkeypatch):
    monkeypatch.delenv('FRAUDSHIELD_API_KEY',raising=False)
    with pytest.raises(RuntimeError,match='FRAUDSHIELD_API_KEY'):
        with TestClient(create_app(ARTIFACTS)):
            pass

def test_saved_model_prediction_matches_report_threshold(sample):
    scorer=Scorer(ARTIFACTS)
    result=scorer.score(sample['transaction_id'],sample['features'])
    assert result['policy_version']==scorer.metadata['policy']['version']
    assert result['action']==apply_policy(result['model_score'],scorer.metadata['policy'])[0]
