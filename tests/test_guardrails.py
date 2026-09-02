from orgctl import guardrails


def test_protected_account_blocks_everything():
    cfg = guardrails.GuardrailConfig(protected_account_ids=["111111111111"])
    reason = guardrails.check_command(["aws", "s3", "ls"], "111111111111", cfg)
    assert reason is not None
    assert "protected" in reason.lower()


def test_builtin_deny_blocks_leave_organization():
    cfg = guardrails.GuardrailConfig()
    reason = guardrails.check_command(
        ["aws", "organizations", "leave-organization"], "222222222222", cfg
    )
    assert reason is not None


def test_custom_deny_pattern():
    cfg = guardrails.GuardrailConfig(deny_patterns=["aws iam delete-role*"])
    reason = guardrails.check_command(
        ["aws", "iam", "delete-role", "--role-name", "foo"], "333333333333", cfg
    )
    assert reason is not None


def test_safe_command_not_blocked():
    cfg = guardrails.GuardrailConfig()
    reason = guardrails.check_command(["aws", "s3", "ls"], "444444444444", cfg)
    assert reason is None


def test_confirmation_pattern_detected():
    cfg = guardrails.GuardrailConfig(require_confirmation_patterns=["aws s3 rm*"])
    match = guardrails.needs_confirmation(["aws", "s3", "rm", "s3://bucket/key"], cfg)
    assert match == "aws s3 rm*"


def test_no_confirmation_needed_when_no_match():
    cfg = guardrails.GuardrailConfig(require_confirmation_patterns=["aws s3 rm*"])
    match = guardrails.needs_confirmation(["aws", "s3", "ls"], cfg)
    assert match is None
