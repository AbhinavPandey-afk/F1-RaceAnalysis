import re

from fastapi import APIRouter

from app.services.llm_engineer import generate_engineer_briefing
from app.telemetry.f1_data import get_driver_laps, load_session

router = APIRouter()


def _clean_laps(driver: str):
    laps = get_driver_laps(driver)

    if laps is None or laps.empty:
        return laps

    laps = laps.dropna(subset=["LapTime"]).copy()
    laps["LapSeconds"] = laps["LapTime"].dt.total_seconds()
    laps = laps[(laps["LapSeconds"] > 0) & (laps["LapSeconds"] < 150)]

    return laps.reset_index(drop=True)


def _mean(values):
    return round(sum(values) / len(values), 3) if values else None


def _safe_number(value, digits=3):
    try:
        if value != value:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _trend(values):
    if len(values) < 2:
        return 0

    x_avg = (len(values) - 1) / 2
    y_avg = sum(values) / len(values)
    numerator = sum((index - x_avg) * (value - y_avg) for index, value in enumerate(values))
    denominator = sum((index - x_avg) ** 2 for index in range(len(values)))

    return round(numerator / denominator, 3) if denominator else 0


def _lap_focus(question: str, fallback: int):
    match = re.search(r"lap\s*(\d+)", question.lower())
    return int(match.group(1)) if match else fallback


def _question_intent(question: str):
    text = question.lower()
    intent_keywords = {
        "strategy": ["strategy", "pit", "stop", "undercut", "overcut", "window", "cycle"],
        "context": ["traffic", "dirty air", "safety", "yellow", "flag", "weather", "rain", "temperature", "context"],
        "comparison": ["sector", "where", "compare", "delta", "faster", "slower", "losing time", "gaining"],
        "tyres": ["tyre", "tire", "degradation", "deg", "compound", "wear", "stint"],
        "telemetry": ["speed", "throttle", "brake", "braking", "straight", "corner", "trace"],
    }

    for intent, keywords in intent_keywords.items():
        if any(keyword in text for keyword in keywords):
            return intent

    return "summary"


def _window(laps, center_lap: int, size: int = 3):
    return laps[
        (laps["LapNumber"] >= center_lap - size)
        & (laps["LapNumber"] <= center_lap + size)
    ]


def _seconds(value):
    try:
        if value != value:
            return None
        return round(value.total_seconds(), 3)
    except AttributeError:
        return None


def _focus_lap_row(laps, focus_lap: int):
    exact = laps[laps["LapNumber"] == focus_lap]
    if not exact.empty:
        return exact.iloc[0]

    nearest_index = (laps["LapNumber"] - focus_lap).abs().idxmin()
    return laps.loc[nearest_index]


def _car_trace_summary(driver: str, lap_number: int):
    try:
        session = load_session()
        driver_laps = session.laps.pick_driver(driver)
        lap_rows = driver_laps[driver_laps["LapNumber"] == lap_number]

        if lap_rows.empty:
            return {}

        car_data = lap_rows.iloc[0].get_car_data()
        if car_data.empty:
            return {}

        speed = car_data["Speed"].dropna()
        throttle = car_data["Throttle"].dropna()
        brake = car_data["Brake"].dropna()

        return {
            "maxSpeed": _safe_number(speed.max(), 1),
            "averageSpeed": _safe_number(speed.mean(), 1),
            "averageThrottle": _safe_number(throttle.mean(), 1),
            "fullThrottleSamples": int((throttle > 95).sum()),
            "brakeSamples": int((brake == True).sum()),
        }
    except Exception as error:
        print("CAR TRACE ERROR:", error)
        return {}


def _agent(name, status, confidence, summary, evidence):
    return {
        "name": name,
        "status": status,
        "confidence": confidence,
        "summary": summary,
        "evidence": evidence,
    }


def _telemetry_agent(driver1: str, driver2: str, laps1, laps2, focus_lap: int):
    lap1 = _focus_lap_row(laps1, focus_lap)
    lap2 = _focus_lap_row(laps2, focus_lap)
    trace1 = _car_trace_summary(driver1, int(lap1["LapNumber"]))
    trace2 = _car_trace_summary(driver2, int(lap2["LapNumber"]))

    speed_delta = None
    if trace1.get("averageSpeed") is not None and trace2.get("averageSpeed") is not None:
        speed_delta = round(trace1["averageSpeed"] - trace2["averageSpeed"], 1)

    tyre_life = int(lap1["TyreLife"]) if lap1.get("TyreLife") == lap1.get("TyreLife") else None
    compound = str(lap1.get("Compound", "--"))
    focus_time = _seconds(lap1["LapTime"])
    rival_time = _seconds(lap2["LapTime"])

    summary = (
        f"{driver1} lap {int(lap1['LapNumber'])} was {round(focus_time - rival_time, 3)}s "
        f"{'slower' if focus_time > rival_time else 'faster'} than {driver2}, with {compound} tyres at {tyre_life} laps old."
        if focus_time is not None and rival_time is not None
        else f"{driver1} telemetry around lap {focus_lap} was checked against {driver2}."
    )

    evidence = [
        f"{driver1} average speed: {trace1.get('averageSpeed', '--')} km/h",
        f"{driver2} average speed: {trace2.get('averageSpeed', '--')} km/h",
        f"Average speed delta: {speed_delta if speed_delta is not None else '--'} km/h",
        f"{driver1} throttle average: {trace1.get('averageThrottle', '--')}%",
        f"{driver1} brake samples: {trace1.get('brakeSamples', '--')}",
    ]

    return _agent("Telemetry Agent", "Speed, throttle, braking, tyre wear", "High", summary, evidence)


def _strategy_agent(driver1: str, driver2: str, laps1, laps2, focus_lap: int):
    lap1 = _focus_lap_row(laps1, focus_lap)
    lap2 = _focus_lap_row(laps2, focus_lap)

    pit_laps1 = [
        int(lap["LapNumber"])
        for _, lap in laps1.iterrows()
        if lap.get("PitInTime") == lap.get("PitInTime") or lap.get("PitOutTime") == lap.get("PitOutTime")
    ]
    pit_laps2 = [
        int(lap["LapNumber"])
        for _, lap in laps2.iterrows()
        if lap.get("PitInTime") == lap.get("PitInTime") or lap.get("PitOutTime") == lap.get("PitOutTime")
    ]

    nearby_pits = [lap for lap in pit_laps1 + pit_laps2 if abs(lap - focus_lap) <= 5]
    compound_offset = str(lap1.get("Compound", "--")) != str(lap2.get("Compound", "--"))
    tyre_life_delta = None
    if lap1.get("TyreLife") == lap1.get("TyreLife") and lap2.get("TyreLife") == lap2.get("TyreLife"):
        tyre_life_delta = int(lap1["TyreLife"] - lap2["TyreLife"])

    summary = (
        f"Pit-window pressure was active near lap {focus_lap}."
        if nearby_pits
        else f"No immediate pit stop happened within five laps of lap {focus_lap}, so the pace change looks more stint-driven."
    )

    evidence = [
        f"{driver1} pit markers: {pit_laps1 or 'none'}",
        f"{driver2} pit markers: {pit_laps2 or 'none'}",
        f"Compound offset at focus lap: {'yes' if compound_offset else 'no'}",
        f"Tyre-life delta ({driver1} - {driver2}): {tyre_life_delta if tyre_life_delta is not None else '--'} laps",
    ]

    return _agent("Strategy Agent", "Pit windows, compounds, undercut/overcut", "Medium", summary, evidence)


def _context_agent(driver1: str, laps1, focus_lap: int):
    session = load_session()
    focus_window = _window(laps1, focus_lap, 2)
    track_statuses = sorted({str(status) for status in focus_window["TrackStatus"].dropna().tolist()})
    weather = session.weather_data
    race_control = session.race_control_messages
    messages = []

    if "Lap" in race_control.columns:
        nearby = race_control[
            race_control["Lap"].notna()
            & (race_control["Lap"] >= focus_lap - 3)
            & (race_control["Lap"] <= focus_lap + 3)
        ]
        messages = nearby["Message"].dropna().astype(str).head(3).tolist()

    if not weather.empty:
        row = weather.iloc[(weather["Time"] - _focus_lap_row(laps1, focus_lap)["LapTime"]).abs().argsort()[:1]]
        weather_row = row.iloc[0] if not row.empty else weather.iloc[-1]
        weather_text = (
            f"Air {weather_row['AirTemp']:.1f}C, track {weather_row['TrackTemp']:.1f}C, "
            f"rainfall {'yes' if bool(weather_row['Rainfall']) else 'no'}"
        )
    else:
        weather_text = "Weather data unavailable"

    summary = (
        f"Race context around lap {focus_lap}: track status {', '.join(track_statuses) or 'normal'}, {weather_text}."
    )

    evidence = [
        f"Track status codes near lap {focus_lap}: {', '.join(track_statuses) or 'none'}",
        weather_text,
        f"Race control: {messages[0] if messages else 'no nearby race-control message'}",
    ]

    return _agent("Race Context Agent", "Safety cars, yellow flags, weather, traffic", "Medium", summary, evidence)


def _comparison_agent(driver1: str, driver2: str, laps1, laps2, focus_lap: int):
    lap1 = _focus_lap_row(laps1, focus_lap)
    lap2 = _focus_lap_row(laps2, focus_lap)

    sector_deltas = {}
    for sector in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        s1 = _seconds(lap1.get(sector))
        s2 = _seconds(lap2.get(sector))
        if s1 is not None and s2 is not None:
            sector_deltas[sector.replace("Time", "")] = round(s1 - s2, 3)

    before1 = _mean(_window(laps1, focus_lap - 3, 3)["LapSeconds"].tolist())
    before2 = _mean(_window(laps2, focus_lap - 3, 3)["LapSeconds"].tolist())
    after1 = _mean(_window(laps1, focus_lap + 3, 3)["LapSeconds"].tolist())
    after2 = _mean(_window(laps2, focus_lap + 3, 3)["LapSeconds"].tolist())
    before_delta = round(before1 - before2, 3) if before1 is not None and before2 is not None else None
    after_delta = round(after1 - after2, 3) if after1 is not None and after2 is not None else None

    worst_sector = max(sector_deltas, key=lambda key: sector_deltas[key]) if sector_deltas else None
    summary = (
        f"{driver1} lost the most relative time in {worst_sector} on lap {focus_lap}."
        if worst_sector and sector_deltas[worst_sector] > 0
        else f"{driver1} vs {driver2} relative pace was compared through lap pace and sector deltas."
    )

    evidence = [
        f"Pre-focus average delta: {before_delta if before_delta is not None else '--'}s",
        f"Post-focus average delta: {after_delta if after_delta is not None else '--'}s",
        f"Sector deltas: {sector_deltas or 'unavailable'}",
    ]

    return _agent("Comparison Agent", "Rival pace, teammate pace, sector deltas", "High", summary, evidence)


def _llm_explanation_agent(driver1: str, driver2: str, focus_lap: int, agents):
    summary_parts = [agent["summary"] for agent in agents[:4]]
    explanation = (
        f"{driver1}'s pace change after lap {focus_lap} is best explained by the combined agent view: "
        + " ".join(summary_parts)
        + f" Overall, compare the stint phase and relative pace against {driver2} before calling it a pure driver-performance drop."
    )

    return _agent(
        "LLM Explanation Agent",
        "Natural-language race engineer synthesis",
        "High",
        explanation,
        [agent["name"] + ": " + agent["summary"] for agent in agents[:4]],
    )


def _build_agent_report(question: str, driver1: str, driver2: str):
    laps1 = _clean_laps(driver1)
    laps2 = _clean_laps(driver2)

    if laps1 is None or laps2 is None or laps1.empty or laps2.empty:
        return {
            "focusLap": None,
            "agents": [],
            "conclusion": "I could not find enough clean lap data for the specialist agents.",
        }

    focus_lap = _lap_focus(question, int(laps1["LapNumber"].median()))
    agents = [
        _telemetry_agent(driver1, driver2, laps1, laps2, focus_lap),
        _strategy_agent(driver1, driver2, laps1, laps2, focus_lap),
        _context_agent(driver1, laps1, focus_lap),
        _comparison_agent(driver1, driver2, laps1, laps2, focus_lap),
    ]
    agents.append(_llm_explanation_agent(driver1, driver2, focus_lap, agents))

    return {
        "focusLap": focus_lap,
        "agents": agents,
        "conclusion": agents[-1]["summary"],
    }


def _agent_by_name(agents, name):
    return next((agent for agent in agents if agent["name"] == name), None)


def _build_question_response(question, driver1, driver2, focus_lap, agents, likely_causes):
    intent = _question_intent(question)
    telemetry = _agent_by_name(agents, "Telemetry Agent")
    strategy = _agent_by_name(agents, "Strategy Agent")
    context = _agent_by_name(agents, "Race Context Agent")
    comparison = _agent_by_name(agents, "Comparison Agent")
    synthesis = _agent_by_name(agents, "LLM Explanation Agent")

    if intent == "tyres":
        answer = (
            f"Tyres are a credible part of the explanation around lap {focus_lap}. "
            f"{telemetry['summary'] if telemetry else ''} "
            f"{strategy['summary'] if strategy else ''} "
            "The key tyre clue is compound and tyre-life offset, not just the raw lap time."
        )
        analysis = [
            telemetry["summary"] if telemetry else None,
            strategy["summary"] if strategy else None,
            *(strategy["evidence"][:2] if strategy else []),
        ]
    elif intent == "strategy":
        answer = (
            f"From a strategy view, lap {focus_lap} looks more about stint position and pit-cycle timing. "
            f"{strategy['summary'] if strategy else ''} "
            f"{comparison['summary'] if comparison else ''}"
        )
        analysis = [
            strategy["summary"] if strategy else None,
            *(strategy["evidence"] if strategy else []),
        ]
    elif intent == "context":
        answer = (
            f"The race-context check around lap {focus_lap} does not point to a dramatic external interruption unless the race-control evidence says otherwise. "
            f"{context['summary'] if context else ''} "
            "Traffic can still matter, but this dataset infers it indirectly from pace and sector loss."
        )
        analysis = [
            context["summary"] if context else None,
            *(context["evidence"] if context else []),
        ]
    elif intent == "comparison":
        answer = (
            f"Compared with {driver2}, the important signal is where {driver1} lost relative time. "
            f"{comparison['summary'] if comparison else ''} "
            f"{telemetry['summary'] if telemetry else ''}"
        )
        analysis = [
            comparison["summary"] if comparison else None,
            *(comparison["evidence"] if comparison else []),
        ]
    elif intent == "telemetry":
        answer = (
            f"The telemetry trace around lap {focus_lap} shows the car-level symptoms first. "
            f"{telemetry['summary'] if telemetry else ''} "
            "Use speed, throttle, and braking evidence to separate tyre limitation from driver pace."
        )
        analysis = [
            telemetry["summary"] if telemetry else None,
            *(telemetry["evidence"] if telemetry else []),
        ]
    else:
        answer = synthesis["summary"] if synthesis else " ".join(likely_causes[:3])
        analysis = likely_causes

    return {
        "intent": intent,
        "answer": " ".join(answer.split()),
        "analysis": [item for item in analysis if item],
    }


def _driver_summary(driver: str, laps, focus_lap: int):
    lap_times = laps["LapSeconds"].tolist()
    focus_window = _window(laps, focus_lap)
    before_window = laps[
        (laps["LapNumber"] >= focus_lap - 6)
        & (laps["LapNumber"] < focus_lap)
    ]
    after_window = laps[
        (laps["LapNumber"] > focus_lap)
        & (laps["LapNumber"] <= focus_lap + 6)
    ]

    focus_lap_row = laps[laps["LapNumber"] == focus_lap]
    compound = "--"
    tyre_life = "--"
    if not focus_lap_row.empty:
        compound = str(focus_lap_row.iloc[0].get("Compound", "--"))
        tyre_life_value = focus_lap_row.iloc[0].get("TyreLife", "--")
        tyre_life = int(tyre_life_value) if tyre_life_value == tyre_life_value else "--"

    pit_laps = []
    for _, lap in laps.iterrows():
        if lap.get("PitInTime") == lap.get("PitInTime") or lap.get("PitOutTime") == lap.get("PitOutTime"):
            pit_laps.append(int(lap["LapNumber"]))

    return {
        "driver": driver,
        "fastest": round(min(lap_times), 3),
        "average": round(sum(lap_times) / len(lap_times), 3),
        "degradation": _trend(focus_window["LapSeconds"].tolist()),
        "beforePace": _mean(before_window["LapSeconds"].tolist()),
        "afterPace": _mean(after_window["LapSeconds"].tolist()),
        "compound": compound,
        "tyreLife": tyre_life,
        "pitLaps": pit_laps,
    }


def _build_explanation(question: str, driver1: str, driver2: str):
    laps1 = _clean_laps(driver1)
    laps2 = _clean_laps(driver2)

    if laps1 is None or laps2 is None or laps1.empty or laps2.empty:
        return {
            "answer": "I could not find enough clean lap data for that comparison.",
            "analysis": [],
            "focusLap": None,
            "metrics": {},
        }

    focus_lap = _lap_focus(question, int(laps1["LapNumber"].median()))
    summary1 = _driver_summary(driver1, laps1, focus_lap)
    summary2 = _driver_summary(driver2, laps2, focus_lap)

    post_delta = None
    if summary1["afterPace"] is not None and summary2["afterPace"] is not None:
        post_delta = round(summary1["afterPace"] - summary2["afterPace"], 3)

    before_after_shift = None
    if summary1["beforePace"] is not None and summary1["afterPace"] is not None:
        before_after_shift = round(summary1["afterPace"] - summary1["beforePace"], 3)

    likely_causes = []

    if before_after_shift is not None and before_after_shift > 0.35:
        likely_causes.append(
            f"{driver1}'s pace dropped by {before_after_shift}s after lap {focus_lap}, which points to tyre life or traffic rather than raw speed."
        )
    elif before_after_shift is not None and before_after_shift < -0.2:
        likely_causes.append(
            f"{driver1} actually improved after lap {focus_lap} by {abs(before_after_shift)}s on average, so the concern is probably relative pace."
        )

    if post_delta is not None:
        leader = driver1 if post_delta < 0 else driver2
        likely_causes.append(
            f"After lap {focus_lap}, {leader} held the better average pace by {abs(post_delta)}s per lap."
        )

    if summary1["tyreLife"] != "--":
        likely_causes.append(
            f"At lap {focus_lap}, {driver1} was on {summary1['compound']} tyres with {summary1['tyreLife']} laps of tyre life."
        )

    nearby_pits = [
        lap for lap in summary1["pitLaps"] if abs(lap - focus_lap) <= 3
    ]
    if nearby_pits:
        likely_causes.append(
            f"A pit event near lap {nearby_pits[0]} likely reset the stint profile and affected the lap-time trace."
        )

    if not likely_causes:
        likely_causes.append(
            "The lap-time trace does not show a single obvious cliff, so the answer is likely a combination of stint phase, traffic, and compound offset."
        )

    agent_report = _build_agent_report(question, driver1, driver2)
    question_response = _build_question_response(
        question,
        driver1,
        driver2,
        focus_lap,
        agent_report["agents"],
        likely_causes,
    )
    metrics = {
        driver1: summary1,
        driver2: summary2,
        "postLapDelta": post_delta,
        "paceShift": before_after_shift,
    }
    llm_result = generate_engineer_briefing(
        question=question,
        driver1=driver1,
        driver2=driver2,
        focus_lap=focus_lap,
        intent=question_response["intent"],
        agents=agent_report["agents"],
        metrics=metrics,
        fallback_answer=question_response["answer"],
    )

    return {
        "answer": llm_result["answer"],
        "analysis": question_response["analysis"],
        "intent": question_response["intent"],
        "llm": {
            "provider": llm_result["provider"],
            "model": llm_result["model"],
            "error": llm_result["error"],
        },
        "focusLap": focus_lap,
        "agents": agent_report["agents"],
        "metrics": metrics,
    }


@router.get("/ai-analysis")
def ai_analysis(driver1: str = "VER", driver2: str = "HAM"):
    explanation = _build_explanation(
        f"Compare {driver1} and {driver2} race pace.",
        driver1,
        driver2,
    )

    return {
        "analysis": explanation["analysis"],
        "answer": explanation["answer"],
        "llm": explanation["llm"],
        "agents": explanation["agents"],
        "metrics": explanation["metrics"],
    }


@router.get("/race-engineer")
def race_engineer(
    question: str = "Why did my driver lose pace?",
    driver1: str = "VER",
    driver2: str = "HAM",
):
    return _build_explanation(question, driver1, driver2)


@router.get("/agents-analysis")
def agents_analysis(
    question: str = "Why did my driver lose pace?",
    driver1: str = "VER",
    driver2: str = "HAM",
):
    return _build_agent_report(question, driver1, driver2)
