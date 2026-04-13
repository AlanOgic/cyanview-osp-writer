# OSP Upstream Snapshot Fixture

This directory holds a frozen copy of the OSP upstream Python module(s)
used by `tests/integration/test_sync_script.py`. To refresh:

```bash
git clone --depth 1 https://github.com/open-strategy-partners/osp_marketing_tools /tmp/osp-upstream
cp /tmp/osp-upstream/src/osp_marketing_tools/server.py tests/fixtures/osp_snapshot/server.py
```

(Adjust the source path if upstream restructures.)
