"""Current conditional 144-hour projection using historical Monsoon coefficients."""
import argparse
import json

# From evaluation/data/model_coefficients.csv (independent method).
# Period and default event count from evaluation/current/functional_timing.csv.
HOURS = 144
BASE_W = 1.8353180532955933
BASE_SENSOR_J = 0.050572208485023654
BASE_CAMERA_J = 2.7016091323289575
OPT_W = 1.3347758019999991
OPT_SENSOR_J = 0.09247340247810949
OPT_BLOCK_J = 56.046417921053376
BLOCK_S = 34.644
HISTORICAL_PERIOD_S = 10.34
DEFAULT_SENSOR_EVENTS = 25378

def project(pi_blocks, sensor_events=DEFAULT_SENSOR_EVENTS):
    if pi_blocks < 0 or sensor_events < 0:
        raise ValueError("counts must be non-negative")
    baseline = HOURS*BASE_W + (25920*BASE_SENSOR_J+288*BASE_CAMERA_J)/3600
    net = OPT_BLOCK_J-BLOCK_S*OPT_SENSOR_J/HISTORICAL_PERIOD_S
    optimized = HOURS*OPT_W+(sensor_events*OPT_SENSOR_J+pi_blocks*net)/3600
    return dict(type="model_projection_not_measurement", hours=HOURS, baseline_wh=baseline,
                optimized_wh=optimized, pi_activity_blocks=pi_blocks, sensor_events=sensor_events,
                net_pi_block_j=net, saving_wh=baseline-optimized,
                saving_percent=100*(1-optimized/baseline))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pi-blocks", type=int, required=True)
    parser.add_argument("--sensor-events", type=int, default=DEFAULT_SENSOR_EVENTS)
    args = parser.parse_args()
    print(json.dumps(project(args.pi_blocks, args.sensor_events), indent=2))
