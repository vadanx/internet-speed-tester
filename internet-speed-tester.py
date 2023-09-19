#!/usr/bin/env python3


from datetime import datetime
import json
from loguru import logger
from matplotlib import pyplot as plot, dates
from os.path import isfile
from pytz import timezone
from speedtest import Speedtest


BASE_NAME = "Internet Speed Tester"
DATETIME_NOW = datetime.now().astimezone(timezone("UTC"))
FILE_PREFIX = f"generated-{DATETIME_NOW.strftime('%Y-%m-%d')}"
FILE_DATA = f"{FILE_PREFIX}-data.json"
FILE_GRAPH = f"{FILE_PREFIX}-graph.png"
FILE_LOGGER = f"{FILE_PREFIX}-logger.log"
TEST_COUNT = 1
TEST_TOOL = Speedtest(secure=True)
TEST_TYPES = ["download", "upload"]
TEST_UNIT = "Mbps"


@logger.catch
def normalize(bps: float) -> float:
    resp = {
        "Kbps": bps // (1024**1),
        "Mbps": bps // (1024**2),
        "Gbps": bps // (1024**3),
    }
    return resp[TEST_UNIT]


@logger.catch
def record(testing: dict) -> None:
    record_graph(record_data(testing))


@logger.catch
def record_data(testing: dict) -> dict:
    if not isfile(FILE_DATA):
        open(FILE_DATA, "x")
    with open(FILE_DATA, "r") as old_f:
        try:
            old_testing = json.loads(old_f.read())
        except json.decoder.JSONDecodeError:
            old_testing = {}
    for type in TEST_TYPES:
        new_has_type = testing.get(type)
        old_has_type = old_testing.get(type)
        if new_has_type and old_has_type:
            testing[type].update(old_testing[type])
        elif not new_has_type and old_has_type:
            testing[type] = old_testing[type]
        elif not new_has_type and not old_has_type:
            testing[type] = {}
    with open(FILE_DATA, "w") as new_f:
        new_f.write(json.dumps(testing, indent=4, sort_keys=True))
    return testing


@logger.catch
def record_graph(results: dict) -> None:
    graph_plot = {}
    for type in results:
        graph_plot[type] = {}
        graph_plot[type]["x"] = []
        graph_plot[type]["y"] = []
        for sample in dict(sorted(results[type].items())):
            graph_plot[type]["x"] += [
                datetime.fromisoformat(results[type][sample]["time"])
            ]
            graph_plot[type]["y"] += [results[type][sample]["value"]]
    graph_size = max(len(graph_plot[TEST_TYPES[0]]["x"]), 15)
    plot.figure(
        figsize=(graph_size, graph_size),
        dpi=150,
    )
    plot.xlabel("Timestamp", fontsize=14)
    plot.ylabel(f"Bandwidth (in {TEST_UNIT})", fontsize=14)
    for type in results:
        plot.plot(graph_plot[type]["x"], graph_plot[type]["y"], label=type, marker=".")
    plot.gcf()
    plot.tick_params(rotation=45)
    plot.gca().xaxis.set_major_formatter(dates.DateFormatter("%Y-%m-%d %H:%M:%S"))
    plot.title(f"{BASE_NAME}\n\nCreated: {DATETIME_NOW}\n", fontsize=14)
    plot.legend()
    plot.savefig(FILE_GRAPH, format=FILE_GRAPH.split(".")[1])


@logger.catch
def test(type: str) -> float:
    resp = float(0)
    try:
        match type:
            case "download":
                resp = TEST_TOOL.download()
            case "upload":
                resp = TEST_TOOL.upload()
        logger.info(f"{type} => {resp} bps")
    except:
        logger.exception()
    finally:
        return resp


@logger.catch
def run() -> None:
    logger.add(FILE_LOGGER, serialize=True)
    testing = {}
    for test_type in TEST_TYPES:
        testing[test_type] = {}
        for _ in range(TEST_COUNT):
            time = datetime.now().astimezone(timezone("UTC"))
            test_key = str(time.timestamp())
            test_time = time.isoformat()
            test_value = normalize(test(test_type))
            testing[test_type][test_key] = {"time": test_time, "value": test_value}
    record(testing)


if __name__ == "__main__":
    run()
