
from defines import GUEST_LIST_IDX_E
from make_reports import normalize_phone_number
from make_bag_tags_and_report import item_count_to_label_count

#columns:
#2-column:
# tags_for_all_guests:  First Last Time/Route Items  -> sorted by last, first or route, last; 2 column
# pickup: empty, Bags, Time, First, Last, phone   -> sorted by time, last, first; 2 column
#1-column:
# delivery: empty, Bags, Route, First, Last, ?phone -> sorted by route, last, first
# delivery_per_route : Bags, First, Last, Street, Unit, Phone

# Driver_Timing: route #, route name, # orders, Minutes to complete	Completion TIME	First Order Out	Orders Complete	Vehicle/Driver	Driver arrival

"""Transforms guest visit lists and client info into sorted report-ready lists."""

from dataclasses import dataclass
from typing import NamedTuple
from defines import GUEST_LIST_IDX_E
from make_bag_tags_and_report import item_count_to_label_count
from make_reports import normalize_phone_number

LONG_ROUTE_LENGTH = 18
SHORT_ROUTE_LENGTH = 7
MAX_FIRST_NAME_LEN = 8
MAX_LAST_NAME_LEN = 13
MAX_DISPLAY_NAME_LEN = 19

class ProcessedReportLists(NamedTuple):
    pickup_by_time_list: list
    delivery_with_item_list: list
    delivery_with_bags_list: list
    delivery_before_move_list: list
    pickup_on_friday_list: list
    pickup_on_saturday_list: list


def _format_route(raw_route: str | None) -> str:
    if not raw_route:
        return ""
    return (
        raw_route.replace(" - ", ": ")
        .replace("- ", ": ")
        .replace(",", "-")[:LONG_ROUTE_LENGTH]
    )


def move_delivery_to_pickup(
    guest_list_list: list[list],
    route_time_tuple_list: list[tuple[str, str]],
    client_info: dict[str, list],
) -> ProcessedReportLists:
    """Relocates designated delivery routes to pickup slots and formats lists for PDF reports."""
    pickup_by_time_list = []
    delivery_with_item_list = []
    delivery_with_bags_list = []
    delivery_before_move_list = []
    pickup_on_friday_list = []
    pickup_on_saturday_list = []

    for g_l_index, guest_list in enumerate(guest_list_list):
        for visit_tuple in guest_list:
            client_id = str(visit_tuple[0])
            if client_id not in client_info:
                print(f"Visit error: {client_id} missing for {visit_tuple=}")
                continue

            info = client_info[client_id]
            first_name = info[0]
            phone = normalize_phone_number(info[3])
            item_count = visit_tuple[1]
            bags = item_count_to_label_count(item_count)

            if g_l_index == GUEST_LIST_IDX_E.Delivery.value:
                raw_route = visit_tuple[3] or ""
                last_name = visit_tuple[4][:MAX_DISPLAY_NAME_LEN]
                route = _format_route(raw_route)

                delivery_before_move_list.append([
                    client_id,
                    first_name[:MAX_FIRST_NAME_LEN],
                    last_name[:MAX_LAST_NAME_LEN],
                    route[:SHORT_ROUTE_LENGTH],
                    item_count,
                ])

                # Match against requested route relocations
                matched_rule = next(
                    (rule for rule in route_time_tuple_list if rule[0] in raw_route),
                    None,
                )

                if matched_rule:
                    route_prefix, pickup_time = matched_rule
                    route_plus_first_name = f"{route_prefix[:4]}: {first_name[:MAX_FIRST_NAME_LEN]}"
                    moved_visit_with_bags = [
                        client_id, "", "", bags, pickup_time,
                        route_plus_first_name, last_name, item_count, phone,
                    ]
                    pickup_by_time_list.append(moved_visit_with_bags)
                else:
                    delivery_with_item_list.append([
                        client_id,
                        first_name[:MAX_FIRST_NAME_LEN],
                        last_name[:MAX_LAST_NAME_LEN],
                        route[:SHORT_ROUTE_LENGTH],
                        item_count,
                    ])
                    delivery_with_bags_list.append([
                        client_id, "", "", bags, route,
                        first_name, last_name, item_count, phone,
                    ])
            else:
                last_name = info[1][:MAX_DISPLAY_NAME_LEN]
                pickup_time = (visit_tuple[2] or "")[:5]

                visit_with_items = [
                    client_id,
                    first_name[:MAX_FIRST_NAME_LEN],
                    last_name[:MAX_LAST_NAME_LEN],
                    pickup_time,
                    item_count,
                ]
                visit_with_bags = [
                    client_id, "", "", bags, pickup_time,
                    first_name, last_name, item_count, phone,
                ]
                pickup_by_time_list.append(visit_with_bags)

                if g_l_index == GUEST_LIST_IDX_E.Pickup_Saturday.value:
                    pickup_on_saturday_list.append(visit_with_items)
                else:
                    pickup_on_friday_list.append(visit_with_items)

    # Sort reports
    pickup_on_saturday_list.sort(key=lambda x: (x[2].lower(), x[1].lower()))
    pickup_on_friday_list.sort(key=lambda x: (x[2].lower(), x[1].lower()))

    pickup_by_time_list.sort(key=lambda x: (x[4], x[6].lower(), x[5].lower()))
    delivery_with_bags_list.sort(key=lambda x: (x[4], x[6].lower(), x[5].lower()))

    delivery_before_move_list.sort(key=lambda x: (x[3], x[2].lower(), x[1].lower()))
    delivery_with_item_list.sort(key=lambda x: (x[3], x[2].lower(), x[1].lower()))

    return ProcessedReportLists(
        pickup_by_time_list=pickup_by_time_list,
        delivery_with_item_list=delivery_with_item_list,
        delivery_with_bags_list=delivery_with_bags_list,
        delivery_before_move_list=delivery_before_move_list,
        pickup_on_friday_list=pickup_on_friday_list,
        pickup_on_saturday_list=pickup_on_saturday_list,
    )
