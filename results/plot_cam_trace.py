#!/usr/bin/env python3
"""Plot CAM trace latitude and longitude time series with attack highlights."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_trace(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CAM trace file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CAM trace file is empty: {csv_path}")

    # Repair older trace files where the header still includes a mac column but rows omit it.
    if "mac" in df.columns and "label" in df.columns and df["label"].isna().all():
        if all(col in df.columns for col in ["station_id", "lat", "lon", "speed_mps", "heading_deg"]):
            df["label"] = df["heading_deg"]
            df["heading_deg"] = df["speed_mps"]
            df["speed_mps"] = df["lon"]
            df["lon"] = df["lat"]
            df["lat"] = df["station_id"]
            df["station_id"] = df["mac"]
            df = df.drop(columns=["mac"])

    if "ts_ms" not in df.columns:
        raise ValueError("Required column ts_ms missing from CAM trace")
    if "station_id" not in df.columns:
        raise ValueError("Required column station_id missing from CAM trace")
    if "lat" not in df.columns or "lon" not in df.columns:
        raise ValueError("Required latitude/longitude columns missing from CAM trace")
    if "label" not in df.columns:
        raise ValueError("Required label column missing from CAM trace")

    df["ts_ms"] = pd.to_datetime(df["ts_ms"], unit="ms")
    df = df.sort_values("ts_ms")
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    return df


def plot_trace(df: pd.DataFrame, output_dir: Path) -> None:
    df["time_s"] = (df["ts_ms"] - df["ts_ms"].min()).dt.total_seconds()

    stations = sorted(df["station_id"].unique())
    if not stations:
        raise ValueError("No station data found in CAM trace.")

    time_min = 0.0
    time_max = 30.0
    lat_min, lat_max = df["lat"].min(), df["lat"].max()
    lon_min, lon_max = df["lon"].min(), df["lon"].max()
    lat_range = max(lat_max - lat_min, 1e-6)
    lon_range = max(lon_max - lon_min, 1e-6)

    lat_pad = max(lat_range * 0.1, 0.00001)
    lon_pad = max(lon_range * 0.1, 0.00001)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Latitude plot
    fig_lat, ax_lat = plt.subplots(figsize=(10, 6))
    for station in stations:
        station_df = df[df["station_id"] == station]
        ax_lat.plot(station_df["time_s"], station_df["lat"], label=f"station {station}", linewidth=1)
        valid_df = station_df[station_df["label"] == 0]
        attacked_df = station_df[station_df["label"] != 0]
        ax_lat.scatter(valid_df["time_s"], valid_df["lat"], c="blue", s=20, alpha=0.6, edgecolors="none")
        ax_lat.scatter(attacked_df["time_s"], attacked_df["lat"], c="red", s=80, alpha=0.9, edgecolors="black", linewidths=0.5)

    ax_lat.set_title("Latitude trace over time")
    ax_lat.set_xlabel("Seconds since start")
    ax_lat.set_ylabel("Latitude")
    ax_lat.set_xlim(time_min, time_max)
    ax_lat.set_ylim(lat_min - lat_pad, lat_max + lat_pad)
    ax_lat.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.6f}"))
    ax_lat.grid(True, alpha=0.3)
    ax_lat.legend(loc="upper right", fontsize="small")
    fig_lat.tight_layout()
    lat_path = output_dir / "cam_trace_latitude.png"
    fig_lat.savefig(lat_path, dpi=200)
    plt.close(fig_lat)

    # Longitude plot
    fig_lon, ax_lon = plt.subplots(figsize=(10, 6))
    for station in stations:
        station_df = df[df["station_id"] == station]
        ax_lon.plot(station_df["time_s"], station_df["lon"], label=f"station {station}", linewidth=1)
        valid_df = station_df[station_df["label"] == 0]
        attacked_df = station_df[station_df["label"] != 0]
        ax_lon.scatter(valid_df["time_s"], valid_df["lon"], c="blue", s=20, alpha=0.6, edgecolors="none")
        ax_lon.scatter(attacked_df["time_s"], attacked_df["lon"], c="red", s=80, alpha=0.9, edgecolors="black", linewidths=0.5)

    ax_lon.set_title("Longitude trace over time")
    ax_lon.set_xlabel("Seconds since start")
    ax_lon.set_ylabel("Longitude")
    ax_lon.set_xlim(time_min, time_max)
    ax_lon.set_ylim(lon_min - lon_pad, lon_max + lon_pad)
    ax_lon.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.6f}"))
    ax_lon.grid(True, alpha=0.3)
    ax_lon.legend(loc="upper right", fontsize="small")
    fig_lon.tight_layout()
    lon_path = output_dir / "cam_trace_longitude.png"
    fig_lon.savefig(lon_path, dpi=200)
    plt.close(fig_lon)

    print(f"Saved latitude plot to {lat_path}")
    print(f"Saved longitude plot to {lon_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot CAM trace station latitude and longitude time series.")
    parser.add_argument(
        "--csv",
        default=None,
        help="Path to cam_trace.csv. Defaults to root/data/cam_trace.csv.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for PNG files. Defaults to results/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    csv_path = Path(args.csv) if args.csv else root / "data" / "cam_trace.csv"
    output_dir = Path(args.output) if args.output else Path(__file__).resolve().parent

    df = load_trace(csv_path)
    plot_trace(df, output_dir)


if __name__ == "__main__":
    main()
