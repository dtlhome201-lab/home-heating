#!/usr/bin/env python3
"""기상청 날씨누리 과거관측(일별자료)에서 관측소별 일평균기온을 받아 data/kma.json을 갱신합니다.

- 처음 실행하면 2025-10-01부터 어제까지 전부 받고,
  이후에는 최근 2개월만 다시 받아 덮어씁니다(늦게 들어온 관측값 반영).
- 표준 라이브러리만 사용합니다. PC에서도 `python scripts/update_kma.py`로 돌릴 수 있습니다.
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request

STATIONS = [108, 112, 119, 131, 133, 143, 146, 152, 155, 156, 159, 184, 253, 257, 296]
START = dt.date(2025, 10, 1)
URL = "https://www.weather.go.kr/w/weather/land/past-obs/obs-by-day.do?stn={stn}&yy={y}&mm={m}&obs=1"
KST = dt.timezone(dt.timedelta(hours=9))
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "kma.json")


def fetch(stn, y, m, tries=3):
    req = urllib.request.Request(URL.format(stn=stn, y=y, m=m), headers={"User-Agent": "Mozilla/5.0 (home-heating updater)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 + 3 * i)


def parse(html, y, m):
    """달력 표에서 {일: 평균기온} 을 뽑습니다. 날짜 행 다음 행이 값 행인 구조."""
    if f"{y}년 {m}월" not in html:
        raise ValueError(f"응답 제목이 {y}년 {m}월이 아님")
    k = html.find("table-cal")
    body = html[k: html.find("</table>", k)]
    rows = re.findall(r"<tr>(.*?)</tr>", body, re.S)
    out, days = {}, None
    for row in rows:
        cells = [re.sub(r"<[^>]+>|&nbsp;", " ", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if not cells:
            continue
        nums = [re.fullmatch(r"\s*(\d{1,2})일\s*", c) for c in cells]
        if any(nums):
            days = [int(x.group(1)) if x else None for x in nums]
            continue
        if days:
            for d, c in zip(days, cells):
                if d is None:
                    continue
                mt = re.search(r"평균기온:\s*(-?\d+(?:\.\d+)?)", c)
                out[d] = float(mt.group(1)) if mt else None
            days = None
    return out


def month_iter(a, b):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    today = dt.datetime.now(KST).date()
    end = today - dt.timedelta(days=1)  # 오늘은 하루가 끝나지 않았으므로 어제까지
    n = (end - START).days + 1
    try:
        with open(PATH, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"start": START.isoformat(), "stations": {}}
    first_run = not data.get("stations")
    since = START if first_run else max(START, (end.replace(day=1) - dt.timedelta(days=1)).replace(day=1))

    errors = []
    for stn in STATIONS:
        arr = data["stations"].get(str(stn), [])
        arr = (arr + [None] * n)[:n]
        for y, m in month_iter(since, end):
            try:
                vals = parse(fetch(stn, y, m), y, m)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{stn} {y}-{m:02d}: {e}")
                continue
            for d, v in vals.items():
                i = (dt.date(y, m, d) - START).days
                if 0 <= i < n and v is not None:
                    arr[i] = v
            time.sleep(0.3)
        data["stations"][str(stn)] = arr

    data["updated"] = dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    data["end"] = end.isoformat()
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"갱신 완료: {START} ~ {end}, 관측소 {len(STATIONS)}곳")
    if errors:
        print("받지 못한 달:", *errors, sep="\n  ")
        if len(errors) == len(STATIONS) * len(list(month_iter(since, end))):
            sys.exit(1)  # 전부 실패하면 워크플로를 실패로 표시


if __name__ == "__main__":
    main()
