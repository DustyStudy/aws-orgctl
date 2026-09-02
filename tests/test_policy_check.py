from orgctl.policy_check import PolicyCheckResult


def test_allowed_property_true_on_allowed():
    r = PolicyCheckResult(
        action="s3:GetObject", resource="*", decision="allowed", matched_statements=["p1"]
    )
    assert r.allowed is True


def test_allowed_property_false_on_explicit_deny():
    r = PolicyCheckResult(
        action="s3:DeleteObject", resource="*", decision="explicitDeny", matched_statements=[]
    )
    assert r.allowed is False


def test_allowed_property_false_on_implicit_deny():
    r = PolicyCheckResult(
        action="iam:DeleteRole", resource="*", decision="implicitDeny", matched_statements=[]
    )
    assert r.allowed is False


# Note: simulate() and resolve_role_arn() call boto3/IAM directly and are
# exercised via integration/manual testing against a real account, not unit
# tests here — mocking IAM's policy simulator faithfully needs `moto`'s IAM
# support, which is limited for this API at time of writing.
