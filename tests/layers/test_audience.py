"""Tests for the audience prompt-assembly layer."""

import pytest

from cyanview_osp_writer.layers.audience import AudienceLayer, AudienceReview
from cyanview_osp_writer.schemas import AudienceProfile, AudiencesFile


@pytest.fixture
def layer() -> AudienceLayer:
    audiences = AudiencesFile(
        version=1,
        audiences={
            "dp": AudienceProfile(
                label="DP", assumes=["cinematic"], avoid=["jargon"], tone="creative"
            ),
            "broadcast_engineer": AudienceProfile(
                label="BE", assumes=["SDI"], avoid=["fluff"], tone="precise"
            ),
            "rental_house": AudienceProfile(
                label="RH", assumes=["logistics"], avoid=["abstract"], tone="practical"
            ),
        },
    )
    return AudienceLayer(audiences)


class TestAudienceLayer:
    def test_single_audience_returns_one_profile(self, layer: AudienceLayer):
        review = layer.assemble("draft text", audience="dp")
        assert isinstance(review, AudienceReview)
        assert len(review.profiles) == 1
        assert review.profiles[0].label == "DP"
        assert review.draft == "draft text"

    def test_mixed_returns_all_three(self, layer: AudienceLayer):
        review = layer.assemble("draft", audience="mixed")
        assert len(review.profiles) == 3
        labels = {p.label for p in review.profiles}
        assert labels == {"DP", "BE", "RH"}

    def test_unknown_audience_raises(self, layer: AudienceLayer):
        with pytest.raises(KeyError):
            layer.assemble("draft", audience="director")

    def test_guidance_includes_tone_and_avoid(self, layer: AudienceLayer):
        review = layer.assemble("draft", audience="broadcast_engineer")
        assert "precise" in review.guidance
        assert "fluff" in review.guidance
