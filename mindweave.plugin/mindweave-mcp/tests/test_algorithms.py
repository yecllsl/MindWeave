import pytest
from mindweave_mcp.algorithms import compute_next_review, MIN_EASE_FACTOR

def test_grade_out_of_range_raises():
    with pytest.raises(ValueError):
        compute_next_review(2.5, 0, 0, 5)

def test_grade_lt3_resets():
    r = compute_next_review(2.5, 10, 5, 2)
    assert r["repetitions"] == 0 and r["interval"] == 1

def test_first_success_interval_1():
    r = compute_next_review(2.5, 0, 0, 4)
    assert r["repetitions"] == 1 and r["interval"] == 1

def test_second_success_interval_6():
    r = compute_next_review(2.5, 1, 1, 4)
    assert r["repetitions"] == 2 and r["interval"] == 6

def test_third_success_interval_times_ef():
    r = compute_next_review(2.5, 6, 2, 4)
    assert r["repetitions"] == 3 and r["interval"] == round(6 * 2.5)

def test_ease_factor_updates_and_floor():
    r = compute_next_review(2.5, 6, 2, 4)  # grade 4: SM-2 公式 (0.1 - (5-4)*(0.08+0.02)) = 0 → EF 不变（VocabCraft 已验证语义）
    assert r["ease_factor"] == pytest.approx(2.5)
    low = compute_next_review(1.3, 1, 0, 1)
    assert low["ease_factor"] == MIN_EASE_FACTOR
