ALL_DAYS_ORDERED = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

DAY_CHOICES = [(d, d) for d in ALL_DAYS_ORDERED]


def days_list_to_range(days):
    """
    Convert a list of day names into range notation.
    e.g. ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"] -> "จันทร์–ศุกร์"
    e.g. ["จันทร์", "พุธ", "ศุกร์"] -> "จันทร์,พุธ,ศุกร์"
    e.g. ["จันทร์", "อังคาร", "พุธ", "ศุกร์"] -> "จันทร์–พุธ,ศุกร์"
    """
    if not days:
        return ""

    # Sort by the canonical order
    indices = sorted([ALL_DAYS_ORDERED.index(d) for d in days if d in ALL_DAYS_ORDERED])
    if not indices:
        return ""

    # Group into consecutive ranges
    ranges = []
    start = indices[0]
    end = indices[0]
    for i in range(1, len(indices)):
        if indices[i] == end + 1:
            end = indices[i]
        else:
            ranges.append((start, end))
            start = indices[i]
            end = indices[i]
    ranges.append((start, end))

    # Format
    parts = []
    for s, e in ranges:
        if s == e:
            parts.append(ALL_DAYS_ORDERED[s])
        else:
            parts.append(f"{ALL_DAYS_ORDERED[s]}–{ALL_DAYS_ORDERED[e]}")

    return ",".join(parts)


def range_to_days_list(range_str):
    """
    Convert range notation back to a list of individual day names.
    e.g. "จันทร์–ศุกร์" -> ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
    e.g. "จันทร์,พุธ" -> ["จันทร์", "พุธ"]
    e.g. "จันทร์–พุธ,ศุกร์" -> ["จันทร์", "อังคาร", "พุธ", "ศุกร์"]
    """
    if not range_str:
        return []

    days = []
    parts = range_str.split(",")
    for part in parts:
        part = part.strip()
        if "–" in part:
            start_day, end_day = part.split("–")
            start_day = start_day.strip()
            end_day = end_day.strip()
            if start_day in ALL_DAYS_ORDERED and end_day in ALL_DAYS_ORDERED:
                si = ALL_DAYS_ORDERED.index(start_day)
                ei = ALL_DAYS_ORDERED.index(end_day)
                for i in range(si, ei + 1):
                    days.append(ALL_DAYS_ORDERED[i])
        else:
            if part in ALL_DAYS_ORDERED:
                days.append(part)

    return days
