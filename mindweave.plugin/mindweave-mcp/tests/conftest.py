import pytest
from mindweave_mcp.storage import Storage


@pytest.fixture()
def storage(tmp_path):
    """storage 引擎直构（test_storage.py 用，显式传 base_dir）。"""
    return Storage(base_dir=tmp_path)


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    """隔离数据目录到 tmp_path，避免 tools 测试写入真实 data/。

    关键：`_DATA_DIR` 的唯一定义点是 `crud` 模块；export 经 `get_storage().exports_dir`、
    organize 经 `crud._DATA_DIR` 属性访问取目录，均随 crud 单点 patch 一并隔离。
    故只需 patch `crud._DATA_DIR` 一处。
    """
    monkeypatch.setattr("mindweave_mcp.tools.crud._DATA_DIR", tmp_path)
    return tmp_path
