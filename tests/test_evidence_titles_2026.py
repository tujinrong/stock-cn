"""Issuer title forms only classify evidence; they imply no investment conclusion."""
import pytest

from stock_cn.evidence import classify_announcement_title, is_periodic_report_body


@pytest.mark.parametrize('title', [
    '2026年一季度报告',
    '2025年三季度报告',
    '2025年度报告',
    '2025年年度报告',
    '2026年第一季度报告',
    '2025年第三季度报告',
    '2026年半年度报告',
    '<em>2026年一季度报告</em>',
    '2025年度报告（修订稿）',
    '2025年度报告(修订版)',
    '2026年半年度报告（更正后）',
])
def test_periodic_full_report_title_forms(title):
    assert classify_announcement_title(title) == 'PERIODIC_REPORT'
    assert is_periodic_report_body(title) is True


@pytest.mark.parametrize('title', [
    '2025年度A股股息分派实施公告',
    '2025年度权益分派实施公告',
    '2025年度利润分配实施公告',
    '2025年度股息派发公告',
    '2025年度股利分配方案',
])
def test_cash_dividend_titles_are_research_references(title):
    assert classify_announcement_title(title) == 'DIVIDEND'
    assert is_periodic_report_body(title) is False


@pytest.mark.parametrize('title', [
    '2025年度报告摘要',
    '2025年度报告摘要（修订版）',
    '2026年一季度报告（摘要）',
    '2025年度报告（英文译本）',
    '2025年度报告（英文版）',
    '2025年度报告审计报告',
    '2025年度报告（内部控制报告）',
    '2025年度报告（提示性公告）',
    '关于2025年度报告的修订公告',
    '2025年度报告（修订说明）',
    '2025年度报告（修订部分）',
    '2025年度报告（更正内容）',
])
def test_summary_translation_audit_and_revision_fragments_are_not_full_reports(title):
    # They can still route to report research, but cannot satisfy the requirement
    # for the latest official full report used by financial review.
    assert classify_announcement_title(title) == 'PERIODIC_REPORT'
    assert is_periodic_report_body(title) is False
