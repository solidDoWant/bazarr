from pathlib import Path

import pytest

from subliminal_patch import core


def test_scan_video_movie(tmpdir):
    video_path = Path(tmpdir, "Taxi Driver 1976 Bluray 720p x264.mkv")
    video_path.touch()

    result = core.scan_video(str(video_path))
    assert isinstance(result, core.Movie)


def test_scan_video_episode(tmpdir):
    video_path = Path(tmpdir, "The Wire S01E01 Bluray 720p x264.mkv")
    video_path.touch()

    result = core.scan_video(str(video_path))
    assert isinstance(result, core.Episode)


@pytest.fixture
def pool_instance():
    yield core.SZProviderPool({"opensubtitlescom"}, {})


def test_pool_update_w_nothing(pool_instance):
    pool_instance.update({}, {}, [], {})
    assert pool_instance.providers == set()
    assert pool_instance.discarded_providers == set()


def test_pool_update_w_multiple_providers(pool_instance):
    assert pool_instance.providers == {"opensubtitlescom"}
    pool_instance.update({"opensubtitlescom", "subf2m"}, {}, [], {})
    assert pool_instance.providers == {"opensubtitlescom", "subf2m"}


def test_pool_update_discarded_providers(pool_instance):
    assert pool_instance.providers == {"opensubtitlescom"}

    # Provider was discarded internally
    pool_instance.discarded_providers = {"opensubtitlescom"}

    assert pool_instance.discarded_providers == {"opensubtitlescom"}

    # Provider is set to be used again
    pool_instance.update({"opensubtitlescom", "subf2m"}, {}, [], {})

    assert pool_instance.providers == {"subf2m", "opensubtitlescom"}

    # Provider should disappear from discarded providers
    assert pool_instance.discarded_providers == set()


def test_pool_update_discarded_providers_2(pool_instance):
    assert pool_instance.providers == {"opensubtitlescom"}

    # Provider was discarded internally
    pool_instance.discarded_providers = {"opensubtitlescom"}

    assert pool_instance.discarded_providers == {"opensubtitlescom"}

    # Provider is not set to be used again
    pool_instance.update({"subf2m"}, {}, [], {})

    assert pool_instance.providers == {"subf2m"}

    # Provider should not disappear from discarded providers
    assert pool_instance.discarded_providers == {"opensubtitlescom"}


def test_language_equals_init():
    assert core._LanguageEquals([(core.Language("spa"), core.Language("spa", "MX"))])


def test_language_equals_init_invalid():
    with pytest.raises(ValueError):
        assert core._LanguageEquals([(core.Language("spa", "MX"),)])


def test_language_equals_init_empty_list_gracefully():
    assert core._LanguageEquals([]) == []


@pytest.mark.parametrize(
    "langs",
    [
        [(core.Language("spa"), core.Language("spa", "MX"))],
        [(core.Language("por"), core.Language("por", "BR"))],
        [(core.Language("zho"), core.Language("zho", "TW"))],
    ],
)
def test_language_equals_check_set(langs):
    equals = core._LanguageEquals(langs)
    lang_set = {langs[0]}
    assert equals.check_set(lang_set) == set(langs)


def test_language_equals_check_set_do_nothing():
    equals = core._LanguageEquals([(core.Language("eng"), core.Language("spa"))])
    lang_set = {core.Language("spa")}
    assert equals.check_set(lang_set) == {core.Language("spa")}


def test_language_equals_check_set_do_nothing_w_forced():
    equals = core._LanguageEquals(
        [(core.Language("spa", forced=True), core.Language("spa", "MX"))]
    )
    lang_set = {core.Language("spa")}
    assert equals.check_set(lang_set) == {core.Language("spa")}


@pytest.fixture
def language_equals_pool_intance():
    equals = [(core.Language("spa"), core.Language("spa", "MX"))]
    yield core.SZProviderPool({"opensubtitlescom"}, language_equals=equals)


def test_language_equals_pool_intance_list_subtitles(
    language_equals_pool_intance, movies
):
    subs = language_equals_pool_intance.list_subtitles(
        movies["dune"], {core.Language("spa")}
    )
    assert subs
    assert all(sub.language == core.Language("spa", "MX") for sub in subs)


def test_language_equals_pool_intance_list_subtitles_reversed(movies):
    equals = [(core.Language("spa", "MX"), core.Language("spa"))]
    language_equals_pool_intance = core.SZProviderPool(
        {"opensubtitlescom"}, language_equals=equals
    )
    subs = language_equals_pool_intance.list_subtitles(
        movies["dune"], {core.Language("spa")}
    )
    assert subs
    assert all(sub.language == core.Language("spa") for sub in subs)


def test_language_equals_pool_intance_list_subtitles_empty_lang_equals(movies):
    language_equals_pool_intance = core.SZProviderPool(
        {"opensubtitlescom"}, language_equals=None
    )
    subs = language_equals_pool_intance.list_subtitles(
        movies["dune"], {core.Language("spa")}
    )
    assert subs
    assert not all(sub.language == core.Language("spa", "MX") for sub in subs)


def test_language_equals_pool_intance_list_subtitles_return_nothing(movies):
    equals = [
        (core.Language("spa", "MX"), core.Language("eng")),
        (core.Language("spa"), core.Language("eng")),
    ]
    language_equals_pool_intance = core.SZProviderPool(
        {"opensubtitlescom"}, language_equals=equals
    )
    subs = language_equals_pool_intance.list_subtitles(
        movies["dune"], {core.Language("spa")}
    )
    assert not language_equals_pool_intance.download_best_subtitles(
        subs, movies["dune"], {core.Language("spa")}
    )


def test_get_subtitle_path_with_provider_tag():
    path = core.get_subtitle_path(
        "/x/y.mkv", core.Language("eng"), tags=["whisperai", "large-v3"]
    )
    assert path == "/x/y.en.whisperai-large-v3.srt"


def test_get_subtitle_path_with_provider_tag_no_model():
    path = core.get_subtitle_path("/x/y.mkv", core.Language("eng"), tags=["whisperai"])
    assert path == "/x/y.en.whisperai.srt"


def test_search_external_subtitles_recognizes_whisperai_tag(tmpdir):
    video_path = tmpdir.join("Some.Movie.2023.1080p.mkv")
    video_path.ensure(file=True)
    sub_path = tmpdir.join("Some.Movie.2023.1080p.en.whisperai-large-v3.srt")
    sub_path.ensure(file=True)

    found = core._search_external_subtitles(str(video_path))

    assert sub_path.basename in found
    assert found[sub_path.basename] == core.Language("eng")


def test_search_external_subtitles_recognizes_whisperai_tag_no_model(tmpdir):
    video_path = tmpdir.join("Other.Movie.2024.mkv")
    video_path.ensure(file=True)
    sub_path = tmpdir.join("Other.Movie.2024.en.whisperai.srt")
    sub_path.ensure(file=True)

    found = core._search_external_subtitles(str(video_path))

    assert found[sub_path.basename] == core.Language("eng")


class _FakeWhisperProvider:
    def __init__(self):
        self.queried = []

    def list_subtitles(self, video, languages):
        self.queried.append(set(languages))
        return []


def _make_whisper_pool():
    pool = core.SZProviderPool({"whisperai"})
    fake = _FakeWhisperProvider()
    pool.initialized_providers["whisperai"] = fake
    return pool, fake


def test_pool_always_use_whisper_skips_existing(movies):
    pool, fake = _make_whisper_pool()
    pool.download_best_subtitles(
        [],
        movies["dune"],
        {core.Language("eng")},
        always_use_whisper=True,
        whisper_languages_to_skip={core.Language("eng")},
    )
    assert fake.queried == []


def test_pool_always_use_whisper_queries_remaining_languages(movies):
    pool, fake = _make_whisper_pool()
    pool.download_best_subtitles(
        [],
        movies["dune"],
        {core.Language("eng"), core.Language("spa")},
        always_use_whisper=True,
        whisper_languages_to_skip={core.Language("eng")},
    )
    assert fake.queried == [{core.Language("spa")}]


def test_pool_always_use_whisper_disabled_does_not_query(movies):
    pool, fake = _make_whisper_pool()
    pool.download_best_subtitles(
        [],
        movies["dune"],
        {core.Language("eng")},
        always_use_whisper=False,
    )
    assert fake.queried == []


def test_pool_always_use_whisper_without_whisper_provider_is_noop(movies):
    # whisperai not in the pool's enabled providers
    pool = core.SZProviderPool({"opensubtitlescom"})
    fake = _FakeWhisperProvider()
    # even if a stale provider object exists, the pool should never reach it
    pool.initialized_providers["whisperai"] = fake
    result = pool.download_best_subtitles(
        [],
        movies["dune"],
        {core.Language("eng")},
        always_use_whisper=True,
    )
    assert result == []
    assert fake.queried == []
