import pandas as pd

from intel_analysis_service.ml import (
    AnomalyDetector,
    RiskScorer,
    build_context_features,
)
from scripts.ml_training import schedule_jobs


def test_build_context_features_merges_sources():
    ts = pd.date_range('2024-01-01', periods=2, freq='H')
    weather = pd.DataFrame({'timestamp': ts, 'weather': [0.1, 0.2]})
    events = pd.DataFrame({'timestamp': ts, 'events': [1, 0]})
    transport = pd.DataFrame({'timestamp': ts[:1], 'transport': [5]})
    social = pd.DataFrame({'timestamp': ts[1:], 'social': [3]})
    infra = pd.DataFrame({'timestamp': ts, 'infra': [0, 0]})

    features = build_context_features(weather, events, transport, social, infra)
    assert set(features.columns) == {
        'timestamp',
        'weather',
        'events',
        'transport',
        'social',
        'infra',
        'event_density',
        'social_sentiment',
    }
    assert len(features) == 2
    assert features.isna().sum().sum() == 0
    assert features['event_density'].iloc[0] == 1
    assert features['social_sentiment'].iloc[1] == 1.5


def test_anomaly_detector_dynamic_threshold():
    train_ts = pd.date_range('2024-01-01', periods=10, freq='D')
    train_df = pd.DataFrame({'timestamp': train_ts, 'value': 1.0})
    detector = AnomalyDetector(factor=2.0).fit(train_df)

    test_ts = pd.date_range('2024-01-11', periods=3, freq='D')
    test_df = pd.DataFrame({'timestamp': test_ts, 'value': [1.0, 1.0, 5.0]})
    preds = detector.predict(test_df)
    assert preds['is_anomaly'].sum() == 1
    assert preds.iloc[2]['is_anomaly']


def test_anomaly_detector_accounts_for_environment():
    train_ts = pd.date_range('2024-01-01', periods=5, freq='D')
    train_df = pd.DataFrame(
        {
            'timestamp': train_ts,
            'value': 1.0,
            'event_density': 0.0,
            'social_sentiment': 0.0,
            'temperature': 20.0,
        }
    )
    detector = AnomalyDetector(
        factor=2.0,
        context_weights={'event_density': 2.0, 'social_sentiment': 1.0, 'temperature': 0.5},
    ).fit(train_df)

    test_df = pd.DataFrame(
        {
            'timestamp': [pd.Timestamp('2024-01-06')],
            'value': [5.0],
            'event_density': [3.0],
            'social_sentiment': [2.0],
            'temperature': [30.0],
        }
    )
    preds = detector.predict(test_df)
    assert not preds['is_anomaly'].iloc[0]


def test_risk_scorer_seasonal_threshold():
    train_ts = pd.date_range('2024-01-01', periods=10, freq='D')
    train_df = pd.DataFrame({'timestamp': train_ts, 'a': 1.0, 'b': 0.0})
    scorer = RiskScorer({'a': 1.0, 'b': 1.0}, quantile=0.9).fit(train_df)

    test_df = pd.DataFrame({'timestamp': [pd.Timestamp('2024-01-15')], 'a': 2.0, 'b': 1.0})
    result = scorer.score(test_df)
    assert result['is_risky'].iloc[0]


def test_schedule_jobs_runs_train_and_eval():
    results = schedule_jobs(run_once=True)
    kinds = [kind for kind, _ in results]
    assert 'train' in kinds
    assert 'eval' in kinds
