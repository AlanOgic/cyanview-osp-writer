"""Integration: server startup, tool registry, resource registry."""

import pytest

from cyanview_osp_writer.server import build_server


@pytest.fixture
def server():
    return build_server()


class TestServerStartup:
    def test_server_built(self, server):
        assert server.name == "cyanview-osp-writer"

    @pytest.mark.asyncio
    async def test_tools_registered(self, server):
        tools = await server.list_tools()
        names = {t.name for t in tools}
        expected = {
            "check_glossary_tool",
            "check_claims_tool",
            "check_audience_tool",
            "osp_edit_tool",
            "osp_seo_tool",
            "osp_meta_tool",
            "osp_writing_tool",
            "osp_value_map_tool",
            "review_draft_tool",
        }
        assert expected.issubset(names)

    @pytest.mark.asyncio
    async def test_resources_registered(self, server):
        resources = await server.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "cyanview://glossary.yaml" in uris
        assert "cyanview://audiences.yaml" in uris
        assert "cyanview://claims-patterns.yaml" in uris
        assert "osp://writing-guide.md" in uris
        assert "osp://editing-codes.md" in uris
        assert "osp://seo-guide.md" in uris
        assert "osp://meta-guide.md" in uris
        assert "osp://value-map.md" in uris
