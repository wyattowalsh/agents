from scripts.hooks.hook_assurance import run_assurance


def test_hook_assurance_bundle_green():
    report = run_assurance(tier="bundle")
    assert report["ok"], report["findings"]
