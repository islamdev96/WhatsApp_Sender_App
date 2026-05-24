"""Remove unused UI tabs and handlers from modern_ui.py (line-preserving)."""
import ast
import sys

PATH = "gui/modern_ui.py"

REMOVE_METHODS = {
    "_build_tab_gmaps",
    "_start_gmaps_scraper",
    "_run_gmaps_scraper_thread",
    "_stop_gmaps_scraper",
    "_clear_gmaps_results",
    "_export_gmaps_to_campaign",
    "_export_gmaps_to_csv",
    "_build_tab_warmer",
    "_start_warmer",
    "_stop_warmer",
    "_run_warmer_automation",
    "_build_tab_workflows",
    "_get_workflow_names",
    "_refresh_workflow_menu",
    "_refresh_workflow_list",
    "_render_workflow_steps",
    "_load_workflow_into_editor",
    "_new_workflow",
    "_save_workflow",
    "_delete_workflow",
    "_add_or_update_step",
    "_edit_step",
    "_delete_step",
    "_clear_step_editor",
    "_use_workflow_in_main",
    "_get_selected_workflow",
    "_schedule_action",
    "_schedule_send",
    "_cancel_schedule",
    "_update_schedule_countdown",
    "_scheduled_start_callback",
    "_start_thread",
    "_build_tab_analytics",
    "_refresh_analytics",
    "_delete_campaign",
    "_build_tab_chatbot",
    "_add_chatbot_rule",
    "_delete_chatbot_rule",
    "_toggle_chatbot",
    "_run_chatbot_automation",
    "_build_tab_filter",
    "_start_number_filter",
    "_run_filter_thread",
    "_export_filtered_numbers",
    "_build_tab_received",
    "_load_ar_rules",
    "_save_ar_rules",
    "_populate_ar_rules_table",
    "_add_ar_rule_dialog",
    "_delete_ar_rule",
    "_toggle_auto_responder",
    "_start_auto_responder_thread",
    "_auto_responder_worker",
    "_begin_send_workflow",
    "_run_workflow_automation",
    "_log_preflight_workflow",
}


def main():
    with open(PATH, encoding="utf-8") as f:
        lines = f.readlines()

    tree = ast.parse("".join(lines))
    ranges = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "ModernWhatsAppApp":
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in REMOVE_METHODS:
                start = item.lineno - 1
                end = item.end_lineno
                ranges.append((start, end))
        break

    for start, end in sorted(ranges, reverse=True):
        del lines[start:end]

    with open(PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Removed {len(ranges)} methods from {PATH}")


if __name__ == "__main__":
    main()
