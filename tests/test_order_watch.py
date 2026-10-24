import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from demo import summarize, simulate_cancel, pick_order
import mcp_bridge
from mcp_bridge import allowed_tools, prepare_call


class OrderWatchTests(unittest.TestCase):
    def setUp(self):
        self.order = {"id": "DEMO-1001", "mode": "delivery", "status": "delivering",
                      "eta": "2026-10-24T12:10:00+08:00", "items": ["模拟汉堡"]}
        self.now = "2026-10-24T12:22:00+08:00"

    def test_overdue_uses_server_time(self):
        report = summarize(self.order, self.now)
        self.assertEqual(report["overdue_minutes"], 12)
        self.assertIn("12 分钟", report["timing"])
        self.assertNotIn("已催单", report["action"])

    def test_pickup_preparing_does_not_claim_ready(self):
        self.order.update(mode="pickup", status="preparing")
        report = summarize(self.order, self.now)
        self.assertIn("空等", report["action"])

    def test_pickup_ready_recommends_pickup(self):
        self.order.update(mode="pickup", status="ready")
        report = summarize(self.order, self.now)
        self.assertIn("取餐", report["action"])
        self.assertIsNone(report["overdue_minutes"])

    def test_missing_or_naive_dates_are_not_guessed(self):
        for eta in (None, "08:00", "2026-10-24T12:10:00"):
            self.order["eta"] = eta
            report = summarize(self.order, self.now)
            self.assertIsNone(report["overdue_minutes"])
            self.assertIn("无法", report["timing"])

    def test_completed_order_is_not_overdue(self):
        self.order["status"] = "completed"
        self.assertIsNone(summarize(self.order, self.now)["overdue_minutes"])

    def test_unknown_status_and_mode_do_not_invent_progress(self):
        self.order.update(status="999", mode="999")
        report = summarize(self.order, self.now)
        self.assertIn("未知", report["status"])
        self.assertIn("核实", report["action"])

    def test_multiple_orders_require_selection(self):
        other = dict(self.order, id="DEMO-1002")
        with self.assertRaises(ValueError):
            pick_order([self.order, other])
        self.assertEqual(pick_order([self.order, other], "DEMO-1002")["id"], "DEMO-1002")

    def test_cancellation_needs_matching_confirmation(self):
        before = copy.deepcopy(self.order)
        for confirmation in (None, "DEMO-OTHER"):
            with self.assertRaises(ValueError):
                simulate_cancel(self.order, confirmation)
        self.assertEqual(self.order, before)
        result = simulate_cancel(self.order, self.order["id"])
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(self.order, before)

    def test_terminal_order_cannot_be_cancelled(self):
        self.order["status"] = "completed"
        with self.assertRaises(ValueError):
            simulate_cancel(self.order, self.order["id"])

    def test_bridge_is_read_only_by_default(self):
        self.assertNotIn("cancel-order", allowed_tools(False))
        for name in ("cancel-order", "create-order", "auto-bind-coupons"):
            with self.assertRaises(ValueError):
                prepare_call(name, {}, allow_cancel=False)

    def test_bridge_cancel_requires_confirmation_and_strips_local_field(self):
        with self.assertRaises(ValueError):
            prepare_call("cancel-order", {"orderId": "123"}, allow_cancel=True)
        args = {"orderId": "123", "_user_confirmed": True}
        self.assertEqual(prepare_call("cancel-order", args, allow_cancel=True), {"orderId": "123"})
        self.assertIn("_user_confirmed", args)

    def test_http_errors_keep_safe_status_without_secret(self):
        from types import SimpleNamespace
        handler = getattr(mcp_bridge, "safe_failure", None)
        self.assertIsNotNone(handler, "bridge must preserve safe HTTP error categories")
        error = RuntimeError("FAKE_SECRET_DO_NOT_ECHO")
        error.response = SimpleNamespace(status_code=429, headers={"retry-after": "90"})
        message = handler(SimpleNamespace(exceptions=[error]))
        self.assertIn("429", message)
        self.assertIn("90", message)
        self.assertNotIn("FAKE_SECRET", message)
        error.response.status_code = 401
        self.assertIn("401", handler(error))


if __name__ == "__main__":
    unittest.main()
