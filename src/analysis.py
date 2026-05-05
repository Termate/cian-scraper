from __future__ import annotations

import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from src.config import ARTIFACTS_DIR, DB_PATH, EXPORTS_DIR


def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM listings", conn)
    conn.close()
    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    df = df.dropna(subset=["price_rub", "area_m2"])
    df = df[df["area_m2"] > 0]
    df["price_per_m2"] = df["price_rub"] / df["area_m2"]
    return df


def save_csv_reports(df: pd.DataFrame) -> None:
    latest_time = df["scraped_at"].max()
    latest = df[df["scraped_at"] == latest_time].copy()

    latest.to_csv(EXPORTS_DIR / "latest_snapshot.csv", index=False)

    summary = pd.DataFrame(
        {
            "metric": [
                "total_rows",
                "unique_listings",
                "scrape_runs",
                "first_scrape",
                "last_scrape",
                "mean_price",
                "median_price",
                "min_price",
                "max_price",
                "mean_area",
                "median_area",
                "mean_price_per_m2",
            ],
            "value": [
                len(df),
                df["listing_id"].nunique(),
                df["scraped_at"].nunique(),
                df["scraped_at"].min(),
                df["scraped_at"].max(),
                round(df["price_rub"].mean(), 2),
                round(df["price_rub"].median(), 2),
                int(df["price_rub"].min()),
                int(df["price_rub"].max()),
                round(df["area_m2"].mean(), 2),
                round(df["area_m2"].median(), 2),
                round(df["price_per_m2"].mean(), 2),
            ],
        }
    )
    summary.to_csv(ARTIFACTS_DIR / "summary_report.csv", index=False)

    by_run = (
        df.groupby("scraped_at")
        .agg(
            listings_count=("listing_id", "nunique"),
            mean_price=("price_rub", "mean"),
            median_price=("price_rub", "median"),
            mean_area=("area_m2", "mean"),
            mean_price_per_m2=("price_per_m2", "mean"),
        )
        .reset_index()
    )
    by_run.to_csv(ARTIFACTS_DIR / "report_by_run.csv", index=False)

    top_expensive = latest.sort_values("price_rub", ascending=False).head(10)
    top_expensive.to_csv(ARTIFACTS_DIR / "top_expensive_latest.csv", index=False)

    top_cheapest = latest.sort_values("price_rub", ascending=True).head(10)
    top_cheapest.to_csv(ARTIFACTS_DIR / "top_cheapest_latest.csv", index=False)


def plot_avg_price_by_run(df: pd.DataFrame) -> None:
    grouped = df.groupby("scraped_at")["price_rub"].mean()

    plt.figure(figsize=(10, 5))
    grouped.plot(marker="o")
    plt.title("Средняя цена аренды студий по запускам")
    plt.xlabel("Время запуска")
    plt.ylabel("Средняя цена, руб.")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "avg_price_by_run.png")
    plt.close()


def plot_listings_count_by_run(df: pd.DataFrame) -> None:
    grouped = df.groupby("scraped_at")["listing_id"].nunique()

    plt.figure(figsize=(10, 5))
    grouped.plot(marker="o")
    plt.title("Количество уникальных объявлений по запускам")
    plt.xlabel("Время запуска")
    plt.ylabel("Количество объявлений")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "listings_count_by_run.png")
    plt.close()


def plot_price_distribution(df: pd.DataFrame) -> None:
    latest_time = df["scraped_at"].max()
    latest = df[df["scraped_at"] == latest_time]

    plt.figure(figsize=(10, 5))
    latest["price_rub"].hist(bins=20)
    plt.title("Распределение цен в последнем запуске")
    plt.xlabel("Цена, руб.")
    plt.ylabel("Количество объявлений")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "price_distribution_latest.png")
    plt.close()


def plot_price_per_m2_distribution(df: pd.DataFrame) -> None:
    latest_time = df["scraped_at"].max()
    latest = df[df["scraped_at"] == latest_time]

    plt.figure(figsize=(10, 5))
    latest["price_per_m2"].hist(bins=20)
    plt.title("Распределение цены за м² в последнем запуске")
    plt.xlabel("Цена за м², руб.")
    plt.ylabel("Количество объявлений")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "price_per_m2_distribution_latest.png")
    plt.close()


def print_console_report(df: pd.DataFrame) -> None:
    print("\n=== Отчёт по данным ЦИАН ===")
    print(f"Всего строк в базе: {len(df)}")
    print(f"Уникальных объявлений: {df['listing_id'].nunique()}")
    print(f"Количество запусков: {df['scraped_at'].nunique()}")
    print(f"Первый запуск: {df['scraped_at'].min()}")
    print(f"Последний запуск: {df['scraped_at'].max()}")

    print("\n=== Цены ===")
    print(f"Средняя цена: {df['price_rub'].mean():,.0f} руб.".replace(",", " "))
    print(f"Медианная цена: {df['price_rub'].median():,.0f} руб.".replace(",", " "))
    print(f"Минимальная цена: {df['price_rub'].min():,.0f} руб.".replace(",", " "))
    print(f"Максимальная цена: {df['price_rub'].max():,.0f} руб.".replace(",", " "))

    print("\n=== Площадь ===")
    print(f"Средняя площадь: {df['area_m2'].mean():.1f} м²")
    print(f"Медианная площадь: {df['area_m2'].median():.1f} м²")

    print("\n=== Цена за м² ===")
    print(f"Средняя цена за м²: {df['price_per_m2'].mean():,.0f} руб.".replace(",", " "))


def build_all_artifacts() -> None:
    df = load_data()

    if df.empty:
        print("В базе данных нет записей.")
        return

    df = prepare_data(df)

    if df.empty:
        print("После очистки не осталось данных для анализа.")
        return

    save_csv_reports(df)
    plot_avg_price_by_run(df)
    plot_listings_count_by_run(df)
    plot_price_distribution(df)
    plot_price_per_m2_distribution(df)
    print_console_report(df)

    print("\nАртефакты сохранены в папку:", ARTIFACTS_DIR)


if __name__ == "__main__":
    build_all_artifacts()