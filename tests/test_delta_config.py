from deepdelta.delta_config import DeltaConfig


def test_combined_flags():
    config = DeltaConfig.KeyCaseIgnored | DeltaConfig.IdAsKey
    assert config.matches(DeltaConfig.KeyCaseIgnored) is True
    assert config.matches(DeltaConfig.IdAsKey) is True


def test_matches():
    config1 = DeltaConfig.CaseIgnored
    assert config1.matches(DeltaConfig.ValueCaseIgnored) is True
    assert config1.matches(DeltaConfig.KeyCaseIgnored) is True


def test_matches_with_mask():
    config = DeltaConfig.KeySpaceTrimmed | DeltaConfig.IdAsKey
    assert config.matches(DeltaConfig.KeySpaceTrimmed, DeltaConfig.SpaceTrimmed) is True
    assert config.matches(DeltaConfig.ValueSpaceTrimmed) is False


