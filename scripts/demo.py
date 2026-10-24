"""离线演示：所有订单、时间均为固定假数据，不调用网络或读取 Token。"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

LABELS = {"placed": "已下单", "preparing": "制作中", "delivering": "配送中",
          "ready": "待取餐", "completed": "已完成", "cancelled": "已取消",
          "pending_payment": "待付款", "cancelling": "取消处理中",
          "refunding": "退款处理中", "refunded": "已退款"}
TERMINAL = {"completed", "cancelled", "refunded"}


def aware_time(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.utcoffset() is not None else None
    except ValueError:
        return None


def summarize(order, server_time, threshold=10):
    status, mode = order.get("status"), order.get("mode")
    now, eta = aware_time(server_time), aware_time(order.get("eta"))
    timing, overdue = "无法判断剩余时间：缺少完整日期、时区或服务器时间。", None
    if status in TERMINAL or status in {"ready", "cancelling", "refunding"}:
        timing = "以当前状态为准，不继续计算送达/备餐超时。"
    elif now and eta:
        seconds = (now - eta).total_seconds()
        if seconds > 0:
            overdue = int(seconds // 60)
            timing = f"已超过预计时间 {overdue} 分钟；预计时间不代表保证。"
        else:
            minutes = int((-seconds + 59) // 60)
            timing = f"距预计时间约 {minutes} 分钟，以最新订单进度为准。"

    if status == "completed":
        action = "订单显示已完成；如未收到餐品，请从官方订单页联系门店或客服。"
    elif status in {"cancelled", "refunded"}:
        action = "查看官方订单页确认退款进度；仍需用餐可自行重新下单。"
    elif status in {"cancelling", "refunding"}:
        action = "等待取消/退款结果；目前不能承诺到账时间，也不要重复提交取消。"
    elif status == "pending_payment":
        action = "先核实这是否为你要查的订单，再到官方订单页处理付款。"
    elif mode == "pickup" and status == "ready":
        action = "餐品已可取，现在可以前往门店取餐；带好官方订单页的取餐凭证。"
    elif mode == "pickup" and status in {"placed", "preparing"}:
        action = "门店尚未确认可取，现在去可能空等；等到待取餐再出发更稳妥。"
    elif mode == "delivery" and status in {"placed", "preparing"}:
        action = "当前处于门店阶段，先等备餐；这条状态不能证明已有骑手接单。"
    elif mode == "delivery" and status == "delivering":
        action = "订单显示配送中，保持电话畅通；未返回骑手位置，无法推算精确到达时间。"
    else:
        action = "状态或取餐方式信息不足，请从官方订单页核实当前阶段。"
    if overdue is not None and overdue >= threshold and status not in TERMINAL:
        action += " 已达到本项目延迟提醒阈值，建议刷新查单或联系官方渠道；若考虑取消，需先确认具体订单与可取消条件。"
    return {"demo": True, "order_id": order.get("id"), "status": LABELS.get(status, "未知状态"),
            "mode": {"delivery": "外送", "pickup": "自取"}.get(mode, "未知方式"),
            "items": order.get("items", []), "server_time": server_time,
            "timing": timing, "overdue_minutes": overdue, "action": action}


def pick_order(orders, order_id=None, latest=False):
    if order_id:
        matches = [order for order in orders if order.get("id") == order_id]
        if not matches:
            raise ValueError("没有找到该模拟订单号，请先用 --list 查看。")
        return matches[0]
    if not orders:
        raise ValueError("没有可查询订单。")
    if len(orders) == 1:
        return orders[0]
    if latest:
        dated = [(aware_time(order.get("created_at")), order) for order in orders]
        if any(date is None for date, _ in dated):
            raise ValueError("缺少下单时间，无法判断最近一单，请指定订单号。")
        return max(dated, key=lambda item: item[0])[1]
    raise ValueError("有多笔订单，请先用 --list 查看，再用 --order-id 指定；查最近一单可用 --latest。")


def simulate_cancel(order, confirmed_id):
    if confirmed_id != order.get("id"):
        raise ValueError("取消尚未确认：须用 --confirm 加上同一个模拟订单号。")
    if order.get("status") not in {"placed", "preparing", "delivering", "ready", "pending_payment"}:
        raise ValueError("该状态不支持模拟取消，请先查看订单。")
    return dict(order, status="cancelled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["delivery", "pickup", "overdue", "unknown", "multiple"], default="delivery")
    parser.add_argument("--list", action="store_true", help="列出模拟订单")
    parser.add_argument("--latest", action="store_true", help="显式选择最近一单")
    parser.add_argument("--order-id")
    parser.add_argument("--cancel", metavar="ORDER_ID", help="只模拟取消，不产生真实操作")
    parser.add_argument("--confirm", metavar="ORDER_ID", help="确认同一模拟订单")
    args = parser.parse_args()
    data = json.loads((Path(__file__).resolve().parents[1] / "examples" / "orders.json").read_text(encoding="utf-8"))
    orders = data["scenarios"][args.scenario]
    print("【离线演示 / 全部为假订单 / 固定模拟服务器时间】")
    if args.list:
        for order in orders:
            print(f"{order['id']} | {order.get('created_at', '时间未知')} | {order['mode']} | {LABELS.get(order['status'], '未知状态')}")
        return 0
    try:
        if args.cancel and args.order_id and args.cancel != args.order_id:
            raise ValueError("查询订单号与取消订单号不一致，请重新选择。")
        order = pick_order(orders, args.cancel or args.order_id, args.latest)
        if args.cancel:
            order = simulate_cancel(order, args.confirm)
            print("模拟取消成功；未连接真实服务，未改写样例文件。真实订单能否取消由官方服务决定。")
        report = summarize(order, data["server_time"])
        print(f"订单 {report['order_id']} · {report['mode']} · {report['status']}")
        print("餐品：" + "、".join(report["items"]))
        print("查询时间：" + report["server_time"])
        print(report["timing"])
        print("你现在可以：" + report["action"])
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
