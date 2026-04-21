import unittest
from unittest.mock import patch

from mold_management.services.workspace import ensure_workspace_resources


class TestWorkspace(unittest.TestCase):
	@patch("mold_management.services.workspace._ensure_workspace_dashboard_layout")
	@patch("mold_management.services.workspace._ensure_dashboard_custom_block")
	def test_ensure_workspace_resources_backfills_block_and_layout(self, mock_block, mock_layout):
		ensure_workspace_resources()

		mock_block.assert_called_once_with()
		mock_layout.assert_called_once_with()
