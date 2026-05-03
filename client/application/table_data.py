def _parse_tier_detail(detail_cb):
    if detail_cb is None:
        return None

    text = detail_cb.currentText().strip()
    if text in {"", "-"}:
        return None

    return int(text)


def _get_row_meta(table, row):
    chk = table.cellWidget(row, 0)
    if not chk:
        return {}
    return dict(chk.property("user_meta") or {})


def extract_table_data(table):
    users = []

    for row in range(table.rowCount()):
        name_edit = table.cellWidget(row, 1)

        if not name_edit or not name_edit.text().strip():
            return None, f"{row + 1}번째 줄의 이름이 비어 있습니다."

        chk = table.cellWidget(row, 0)
        tier_cb = table.cellWidget(row, 2)
        detail_cb = table.cellWidget(row, 3)
        p1 = table.cellWidget(row, 4)
        p2 = table.cellWidget(row, 5)
        p3 = table.cellWidget(row, 6)

        user = _get_row_meta(table, row)
        user.update({
            "selected": chk.isChecked() if chk else False,
            "name": name_edit.text().strip(),
            "tier": tier_cb.currentText() if tier_cb else "",
            "tier_detail": _parse_tier_detail(detail_cb),
            "positions": [
                p1.currentText() if p1 else "",
                p2.currentText() if p2 else "",
                p3.currentText() if p3 else "",
            ],
        })
        users.append(user)

    return users, None


def extract_selected_users(table):
    selected = []

    for row in range(table.rowCount()):
        chk = table.cellWidget(row, 0)
        if not chk or not chk.isChecked():
            continue

        name_edit = table.cellWidget(row, 1)
        tier_cb = table.cellWidget(row, 2)
        detail_cb = table.cellWidget(row, 3)
        p1 = table.cellWidget(row, 4)
        p2 = table.cellWidget(row, 5)
        p3 = table.cellWidget(row, 6)

        if any(widget is None for widget in [name_edit, tier_cb, detail_cb, p1, p2, p3]):
            continue

        name = name_edit.text().strip()
        if not name:
            continue

        user = _get_row_meta(table, row)
        user.update({
            "name": name,
            "tier": tier_cb.currentText(),
            "tier_detail": _parse_tier_detail(detail_cb),
            "positions": [
                p1.currentText(),
                p2.currentText(),
                p3.currentText(),
            ],
        })
        selected.append(user)

    return selected
