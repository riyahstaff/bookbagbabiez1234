from app.assembler.subtitles import build_srt


def test_build_srt_formats_a_single_cue():
    srt = build_srt([(0.0, 1.5, "Hello there")])
    assert srt == "1\n00:00:00,000 --> 00:00:01,500\nHello there\n"


def test_build_srt_numbers_cues_sequentially_and_formats_larger_times():
    srt = build_srt(
        [
            (0.0, 2.0, "First line"),
            (65.25, 70.0, "Second line, past a minute"),
            (3725.0, 3726.0, "Third line, past an hour"),
        ]
    )
    lines = srt.splitlines()
    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:02,000"
    assert lines[2] == "First line"
    assert lines[4] == "2"
    assert lines[5] == "00:01:05,250 --> 00:01:10,000"
    assert lines[8] == "3"
    assert lines[9] == "01:02:05,000 --> 01:02:06,000"


def test_build_srt_with_no_cues_is_empty():
    assert build_srt([]) == ""
