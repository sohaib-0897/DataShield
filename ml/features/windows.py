"""Shared per-user, disjoint event windows with explicit signal coverage.

Adapters supply normalized event dictionaries and observed source intervals.
The CERT schema is deliberately incompatible with event-window-v2 live models.
"""
from collections import defaultdict
from datetime import datetime, timedelta
import math

VERSION = 'cert-user-hour-v1'
CHANNELS = ('FILE', 'HTTP', 'EMAIL', 'LOGON', 'USB')
FEATURE_NAMES = tuple(f'{c.lower()}_count' for c in CHANNELS) + (
    'total_count', 'after_hours_fraction', 'unique_pc_count', 'novel_pc_fraction',
    'past_mean_total', 'total_over_past_mean', 'history_windows', 'cold_start',
) + tuple(f'{c.lower()}_available' for c in CHANNELS)


def floor_hour(value):
    return value.replace(minute=0, second=0, microsecond=0)


def build_windows(events, coverage, *, work_start=9, work_end=17, weekdays=(0, 1, 2, 3, 4)):
    """Active user-hours only; absent user-hours are not inferred inactivity.

    A channel is observed only when the ENTIRE window lies in its coverage.
    Missing counts are None, with binary availability features. Numeric training
    selects fully observed windows. Baselines include only completed, fully
    observed windows for the same user. No current/future event enters baseline.
    All times must be naive release-local; no timezone conversion is invented.
    """
    if not 0 <= work_start < work_end <= 24 or not set(weekdays) <= set(range(7)):
        raise ValueError('Invalid work hours')
    intervals = {}
    for channel, (start, end) in coverage.items():
        if channel not in CHANNELS or start.tzinfo or end.tzinfo or start > end:
            raise ValueError('Invalid coverage')
        intervals[channel] = (start, end)
    groups = defaultdict(list)
    for event in events:
        when = datetime.fromisoformat(event['timestamp_local'])
        if when.tzinfo or event['channel'] not in CHANNELS:
            raise ValueError('Unsupported time/channel contract')
        groups[(event['username'], floor_hour(when))].append(event)
    result, history, seen_pc = [], defaultdict(list), defaultdict(set)
    for (user, start), rows in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0])):
        end = start + timedelta(hours=1)
        availability = {c: int(c in intervals and intervals[c][0] <= start and end <= intervals[c][1]) for c in CHANNELS}
        counts = {f'{c.lower()}_count': sum(e['channel'] == c for e in rows) if availability[c] else None for c in CHANNELS}
        prior = history[user]
        mean = sum(prior) / len(prior) if prior else None
        total = len(rows)
        off_hours = sum(datetime.fromisoformat(e['timestamp_local']).weekday() not in weekdays or
                        not work_start <= datetime.fromisoformat(e['timestamp_local']).hour < work_end for e in rows)
        pcs = {e['pc'] for e in rows}
        full = all(availability.values())
        values = {**counts, 'total_count': total if full else None,
                  'after_hours_fraction': off_hours / total if full else None,
                  'unique_pc_count': len(pcs) if full else None,
                  'novel_pc_fraction': len(pcs - seen_pc[user]) / len(pcs) if full and prior else None,
                  'past_mean_total': mean, 'total_over_past_mean': total / mean if full and mean else None,
                  'history_windows': len(prior), 'cold_start': int(not prior),
                  **{f'{c.lower()}_available': availability[c] for c in CHANNELS}}
        result.append({'user': user, 'start': start.isoformat(), 'end': end.isoformat(),
                       'feature_version': VERSION, 'features': values, 'fully_observed': full,
                       'event_keys': [(e['dataset_sha256'], e['source_file'], e['source_id']) for e in rows]})
        if full:
            history[user].append(total)
            seen_pc[user].update(pcs)
    return result


def matrix(windows):
    """Stable ordered input; unavailable values remain NaN for train-fitted imputation."""
    return [[math.nan if w['features'][name] is None else w['features'][name] for name in FEATURE_NAMES] for w in windows]
