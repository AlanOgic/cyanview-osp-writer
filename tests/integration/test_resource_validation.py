"""Integration: bundled resource files are well-formed."""

from cyanview_osp_writer.resources import OSP_GUIDE_NAMES, load_resources
from cyanview_osp_writer.schemas import (
    AudiencesFile,
    ClaimsFile,
    GlossaryFile,
)


class TestResourceValidation:
    def test_glossary_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.glossary, GlossaryFile)
        assert len(r.glossary.terms) >= 5

    def test_audiences_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.audiences, AudiencesFile)

    def test_claims_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.claims, ClaimsFile)
        assert len(r.claims.banned_superlatives) >= 1

    def test_osp_guides_present_and_nonempty(self):
        r = load_resources()
        for name in OSP_GUIDE_NAMES:
            assert name in r.osp_guides, f"missing OSP guide: {name}"
            content = r.osp_guides[name]
            assert len(content.strip()) > 0, f"empty OSP guide: {name}"
            assert content.startswith("#"), f"OSP guide missing markdown header: {name}"

    def test_osp_source_sha_present(self):
        r = load_resources()
        assert r.osp_source_sha
        # "placeholder" is the literal contents of the committed
        # .source-sha before the first sync; "unknown" is the
        # resources.py fallback if the file is missing entirely;
        # post-sync the file holds a 40-char git SHA.
        assert (
            r.osp_source_sha in {"placeholder", "unknown"}
            or len(r.osp_source_sha) == 40
        )
