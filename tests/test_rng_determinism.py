from gamecore import rules


def test_rng_determinism_sequence() -> None:
    rules.set_seed(42)
    seq1 = [rules.RNG.next() for _ in range(10)]
    rules.set_seed(42)
    seq2 = [rules.RNG.next() for _ in range(10)]
    assert seq1 == seq2
